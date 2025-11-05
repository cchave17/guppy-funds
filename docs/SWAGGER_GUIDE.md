# Swagger/OpenAPI Documentation Guide

## Viewing Interactive API Documentation

Guppy Funds automatically generates interactive API documentation using FastAPI's built-in Swagger/OpenAPI support.

---

## 📖 Option 1: Swagger UI (Recommended)

**Interactive API explorer with "Try it out" functionality**

1. Start the services:
```bash
docker-compose up -d
```

2. Open in your browser:
```
http://localhost:8000/docs
```

**Features:**
- 📝 See all endpoints with descriptions
- 🧪 Test endpoints directly in browser ("Try it out" button)
- 📋 View request/response schemas
- 🔍 See example responses
- ⚙️ Query parameter documentation

---

## 📘 Option 2: ReDoc (Clean Documentation)

**Cleaner, more readable documentation view**

Open in your browser:
```
http://localhost:8000/redoc
```

**Features:**
- 📖 Three-column layout (navigation, content, examples)
- 🎨 Better typography
- 📱 Mobile-friendly
- 🔗 Deep linking to specific endpoints

---

## 💾 Option 3: editor.swagger.io (External Editor)

**Edit and view OpenAPI schema externally**

### Method A: Copy JSON directly

1. Get the OpenAPI JSON:
```bash
curl http://localhost:8000/openapi.json > guppy_funds_api.json
```

2. Go to: https://editor.swagger.io

3. Click **File** → **Import file**

4. Upload `guppy_funds_api.json`

### Method B: Copy from file

The OpenAPI schema has been saved to: `swagger_schema.json`

1. Open `swagger_schema.json` in your project
2. Copy the entire contents
3. Go to: https://editor.swagger.io
4. Paste into the editor

---

## 📚 What You'll See in Swagger

### Current Endpoints (Import Management)

**POST /v1/imports**
- Upload CSV files
- Supported banks: AMEX, Citi, Wells Fargo
- Automatic processing via worker

**POST /v1/imports/{import_id}/parse**
- Manually trigger CSV parsing
- Converts to raw transactions

**POST /v1/imports/{import_id}/enrich**
- Manually trigger AI enrichment
- Uses Claude API for merchant normalization

**GET /health**
- Health check endpoint

**GET /**
- API info endpoint

---

## 🔮 Coming Soon (Planned Endpoints)

The following endpoints will be added in upcoming phases:

### **Transactions**
- `GET /v1/transactions` - Query all transactions with filters
- `GET /v1/transactions/{id}` - Get specific transaction
- `GET /v1/transactions/income` - All income transactions
- `GET /v1/transactions/expenses` - All spending
- `GET /v1/transactions/subscriptions` - Recurring payments
- `GET /v1/transactions/summary` - Financial summary with totals
- `GET /v1/transactions/by-category` - Grouped by category
- `GET /v1/transactions/by-merchant` - Grouped by merchant
- `GET /v1/transactions/by-month` - Monthly breakdown

### **Balances**
- `GET /v1/balances` - Current balance by bank
- `GET /v1/balances/{source_bank}` - Specific bank balance

### **Merchants**
- `GET /v1/merchants` - List all cached merchants
- `GET /v1/merchants/{id}` - Merchant details
- `GET /v1/merchants/{id}/transactions` - Transactions for merchant

### **Categories & Tags**
- `GET /v1/categories` - List categories with totals
- `GET /v1/tags` - List tags with counts

---

## 🎨 Customizing OpenAPI Documentation

The OpenAPI schema is defined in `app/main.py`:

```python
app = FastAPI(
    title="Guppy Funds API",
    description="...",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)
```

### Adding Endpoint Documentation

Each endpoint can have rich documentation:

```python
@router.get(
    "/example",
    summary="Short title",
    description="Detailed markdown description",
    response_model=MyResponseModel,
    tags=["Category"],
)
async def my_endpoint():
    \"\"\"Brief docstring\"\"\"
    pass
```

---

## 📊 Example: Testing via Swagger UI

1. Go to http://localhost:8000/docs
2. Find **POST /v1/imports**
3. Click **"Try it out"**
4. Click **Choose File** and select a CSV
5. Select `source_bank` from dropdown
6. Click **Execute**
7. See the response with `import_id`

---

## 🔍 Endpoint Details in Swagger

For each endpoint, you'll see:

**Parameters:**
- Path parameters (e.g., `{import_id}`)
- Query parameters (filters, pagination)
- Request body schema

**Responses:**
- Success response (200, 201, 202)
- Error responses (400, 404, 500)
- Example values
- Schema definitions

**Models:**
- Pydantic models displayed as JSON schemas
- Example data
- Field descriptions
- Required vs optional fields

---

## 🚀 Using OpenAPI for Code Generation

The OpenAPI schema can be used to generate client code:

### Python Client
```bash
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g python \
  -o ./client
```

### TypeScript Client
```bash
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./client
```

---

## 📋 Summary

**Quick Access:**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json
- **Schema File**: `swagger_schema.json`

**Best For:**
- **Development**: Swagger UI (interactive testing)
- **Reading**: ReDoc (cleaner layout)
- **External Tools**: OpenAPI JSON file

Start with Swagger UI - it's the most useful for development and testing!
