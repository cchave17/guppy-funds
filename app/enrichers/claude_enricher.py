import json
import uuid
from datetime import datetime
from typing import Optional

from anthropic import AsyncAnthropic

from app.config import settings
from app.database import get_database
from app.models import TransactionEnriched, MerchantInfo, AccountInfo, Location, Merchant


class ClaudeEnricher:
    """Enricher using Claude API for intelligent transaction enrichment."""

    def __init__(self, import_id: str, db=None):
        self.import_id = import_id
        self.db = db if db is not None else get_database()
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.enrichment_version = 1.0

    async def enrich_import(self) -> dict:
        """
        Enrich all raw transactions for this import.

        Returns:
            Dictionary with enrichment statistics
        """
        total_rows = 0
        successful_rows = 0
        errors = []

        # Find all raw transactions for this import
        cursor = self.db.transactions_raw.find(
            {"import_id": self.import_id, "processed": False}
        )

        async for raw_transaction in cursor:
            try:
                total_rows += 1

                # Enrich the transaction
                enriched = await self._enrich_transaction(raw_transaction)

                # Insert into transactions_enriched
                await self.db.transactions_enriched.insert_one(enriched.model_dump())

                # Mark raw transaction as processed
                await self.db.transactions_raw.update_one(
                    {"_id": raw_transaction["_id"]}, {"$set": {"processed": True}}
                )

                successful_rows += 1

            except Exception as e:
                error_msg = f"Row {raw_transaction.get('_id')}: {str(e)}"
                errors.append(
                    {
                        "row_number": total_rows,
                        "message": str(e),
                        "timestamp": datetime.utcnow(),
                    }
                )
                print(f"Error enriching transaction: {e}")

        return {
            "total_rows": total_rows,
            "successful_rows": successful_rows,
            "failed_rows": len(errors),
            "errors": errors,
        }

    async def _enrich_transaction(self, raw_transaction: dict) -> TransactionEnriched:
        """
        Enrich a single transaction using Claude API with merchant caching.

        Args:
            raw_transaction: Raw transaction document from MongoDB

        Returns:
            Enriched transaction model
        """
        raw_data = raw_transaction["raw_data"]
        source_bank = raw_transaction["source_bank"]

        # Extract merchant name based on source bank
        if source_bank == "amex":
            merchant_name_raw = raw_data.get("Description", "").strip()
        elif source_bank == "citi":
            merchant_name_raw = raw_data.get("Description", "").strip()
        elif source_bank == "wells":
            # Wells has description in "Transaction Type" field
            merchant_name_raw = raw_data.get("Transaction Type", "").strip()
        else:
            merchant_name_raw = raw_data.get("Description", "").strip()

        # Step 1: Check merchant cache
        cached_merchant = await self._lookup_merchant(merchant_name_raw)

        if cached_merchant:
            # Use cached merchant data
            merchant_info = MerchantInfo(
                name=cached_merchant["name"],
                category=cached_merchant.get("category"),
                subcategory=cached_merchant.get("subcategory"),
                location=Location(**cached_merchant["location"])
                if cached_merchant.get("location")
                else None,
            )
            tags = cached_merchant.get("tags", [])
            confidence = cached_merchant.get("enrichment_confidence", 0.9)
            is_recurring = cached_merchant.get("is_subscription", False)
        else:
            # Step 2: Call Claude API for enrichment
            enrichment_result = await self._call_claude_api(raw_data)

            # Check if this is income
            is_income = enrichment_result.get("is_income", False)

            # Extract merchant info
            merchant_info = MerchantInfo(
                name=enrichment_result["merchant_name"],
                category=enrichment_result.get("category"),
                subcategory=enrichment_result.get("subcategory"),
                location=Location(**enrichment_result["location"])
                if enrichment_result.get("location")
                else None,
            )
            tags = enrichment_result.get("tags", [])
            confidence = enrichment_result.get("confidence", 0.8)
            is_recurring = enrichment_result.get("is_recurring", False) or is_income

            # Step 3: Cache the merchant for future use
            await self._cache_merchant(
                raw_name=merchant_name_raw,
                enrichment=enrichment_result,
            )

        # Parse date
        date_str = raw_data.get("Date", "")
        transaction_date = self._parse_date(date_str)

        # Parse amount and type based on source bank
        if source_bank == "amex":
            amount_str = str(raw_data.get("Amount", "0"))
            amount = abs(float(amount_str.replace(",", "")))
            transaction_type = "debit"  # AMEX amounts are positive, assume debit

            account_info = AccountInfo(
                name=f"AMEX {raw_data.get('Account #', '').replace('-', '')}",
                account_number=raw_data.get("Account #", "").replace("-", ""),
                card_member=raw_data.get("Card Member"),
            )
            description = raw_data.get("Description", "")

        elif source_bank == "citi":
            amount = raw_data.get("_amount", 0.0)
            transaction_type = raw_data.get("_transaction_type", "debit")

            account_info = AccountInfo(
                name="Citi Costco Visa",
                account_number=None,
                card_member=raw_data.get("Member Name"),
            )
            description = raw_data.get("Description", "")

        elif source_bank == "wells":
            amount = raw_data.get("_amount", 0.0)
            transaction_type = raw_data.get("_transaction_type", "debit")

            account_info = AccountInfo(
                name="Wells Fargo Checking",
                account_number=None,
                card_member=None,  # Wells doesn't provide card member in CSV
            )
            description = raw_data.get("Transaction Type", "")
        else:
            # Fallback
            amount = abs(float(str(raw_data.get("Amount", "0")).replace(",", "")))
            transaction_type = "debit"
            account_info = AccountInfo(name=f"{source_bank.upper()} Account")
            description = raw_data.get("Description", "")

        # Override transaction type if income detected by Claude
        if merchant_info.category == "Income" or is_recurring and "income" in tags:
            transaction_type = "income"

        # Create enriched transaction
        enriched = TransactionEnriched(
            transaction_id=str(uuid.uuid4()),
            source_bank=raw_transaction["source_bank"],
            import_id=self.import_id,
            raw_id=str(raw_transaction["_id"]),
            enrichment_version=self.enrichment_version,
            date=transaction_date,
            description=description,
            amount=amount,
            type=transaction_type,
            currency="USD",
            merchant=merchant_info,
            account=account_info,
            tags=tags,
            notes=None,
            is_recurring=is_recurring,
            enriched_confidence=confidence,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        return enriched

    async def _call_claude_api(self, raw_data: dict) -> dict:
        """
        Call Claude API to extract structured enrichment data.

        Args:
            raw_data: Raw CSV row data

        Returns:
            Enrichment data dictionary
        """
        # Extract relevant fields (handle different bank formats)
        description = (
            raw_data.get('Description') or
            raw_data.get('Transaction Type') or
            ''
        )
        amount = raw_data.get('Amount') or raw_data.get('_amount') or ''
        category = raw_data.get('Category', '')
        extended = raw_data.get('Extended Details', '')
        address = raw_data.get('Address', '')
        city_state = raw_data.get('City/State', '')

        # Build prompt with transaction data
        prompt = f"""You are a financial transaction enrichment AI. Analyze the following transaction and extract structured information.

Transaction Data:
- Description: {description}
- Amount: {amount}
- Category: {category}
- Extended Details: {extended}
- Address: {address}
- City/State: {city_state}

Extract and return ONLY valid JSON with this exact structure:
{{
  "merchant_name": "Clean, standardized merchant name or employer/income source",
  "category": "Top-level category",
  "subcategory": "Specific subcategory",
  "location": {{
    "city": "City name or null",
    "state": "State abbreviation or null",
    "country": "United States"
  }},
  "tags": ["tag1", "tag2"],
  "is_subscription": false,
  "is_recurring": false,
  "is_income": false,
  "confidence": 0.95
}}

Rules:
- merchant_name: Remove location, normalize spelling. For income: use employer name (e.g., "UnitedHealthcare", "Lifetime Fitness")
- category: Categories include:
  * "Income" - for payroll, direct deposits, salary, benefits
  * "Shopping", "Restaurants", "Transportation", "Subscriptions", "Cash Withdrawal", etc. for spending
- subcategory: Be specific (e.g., "Salary", "Benefits", "Online Retail", "Fast Food", "EV Charging", "Streaming Service")
- tags: 2-4 relevant keywords
- is_subscription: TRUE if merchant is a subscription service (Netflix, Spotify, HBO, Discord, etc.)
- is_recurring: TRUE if this specific transaction appears to be recurring (monthly/annual charges)
- is_income: TRUE if this is income/payroll (keywords: PAYROLL, DIR DEP, DIRECT DEPOSIT, salary, wages, benefits, employer payment)
- confidence: 0-1 score for extraction quality

IMPORTANT: If description contains PAYROLL, DIR DEP, DIRECT DEPOSIT, salary keywords → set is_income: true, category: "Income"

Return ONLY the JSON, no other text"""

        try:
            # Call Claude API
            message = await self.client.messages.create(
                model=settings.claude_model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response
            response_text = message.content[0].text.strip()

            # Extract JSON from response (in case Claude adds markdown)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            enrichment = json.loads(response_text)
            return enrichment

        except Exception as e:
            print(f"Claude API error: {e}")
            # Fallback: basic enrichment
            return {
                "merchant_name": raw_data.get("Description", "Unknown")[:50],
                "category": raw_data.get("Category", "Uncategorized"),
                "subcategory": None,
                "location": {
                    "city": None,
                    "state": None,
                    "country": "United States",
                },
                "tags": [],
                "is_subscription": False,
                "is_recurring": False,
                "is_income": False,
                "confidence": 0.3,
            }

    async def _lookup_merchant(self, raw_name: str) -> Optional[dict]:
        """
        Look up merchant in cache by raw name or alias.

        Args:
            raw_name: Raw merchant name from transaction

        Returns:
            Merchant document if found, None otherwise
        """
        merchant = await self.db.merchants.find_one(
            {"aliases": {"$in": [raw_name.upper()]}}
        )
        return merchant

    async def _cache_merchant(self, raw_name: str, enrichment: dict):
        """
        Cache enriched merchant data for future reuse.

        Args:
            raw_name: Raw merchant name to use as alias
            enrichment: Enrichment data from Claude
        """
        merchant_id = enrichment["merchant_name"].lower().replace(" ", "-")

        # Check if merchant already exists
        existing = await self.db.merchants.find_one({"merchant_id": merchant_id})

        if existing:
            # Add alias to existing merchant
            await self.db.merchants.update_one(
                {"merchant_id": merchant_id},
                {"$addToSet": {"aliases": raw_name.upper()}},
            )
        else:
            # Create new merchant
            merchant = Merchant(
                merchant_id=merchant_id,
                name=enrichment["merchant_name"],
                aliases=[raw_name.upper()],
                category=enrichment.get("category"),
                subcategory=enrichment.get("subcategory"),
                tags=enrichment.get("tags", []),
                location=enrichment.get("location"),
                is_subscription=enrichment.get("is_subscription", False),
                enrichment_confidence=enrichment.get("confidence", 0.8),
                enrichment_version=self.enrichment_version,
            )

            await self.db.merchants.insert_one(merchant.model_dump())

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string into datetime object.

        Args:
            date_str: Date string (e.g., "10/25/2025")

        Returns:
            Datetime object
        """
        try:
            return datetime.strptime(date_str, "%m/%d/%Y")
        except Exception:
            return datetime.utcnow()
