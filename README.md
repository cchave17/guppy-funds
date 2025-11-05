# Guppy Funds

**Automated personal finance ingestion and enrichment service** that consolidates transactions from multiple banks (AMEX, Citi, Wells Fargo) into a unified, AI-enriched format.

## Features

- **Multi-Bank Support**: Import CSVs from AMEX, Citi, and Wells Fargo
- **AI-Powered Enrichment**: Uses Claude API to normalize merchant names, categorize spending, and extract location data
- **Intelligent Deduplication**: Prevents duplicate transactions across multiple uploads
  - AMEX: Reference field-based
  - Citi/Wells: Fingerprint hash-based
- **Merchant Caching**: Reuses enrichment results to minimize API costs
- **Automated Processing**: Background worker automatically processes uploads
- **Subscription Detection**: Identifies recurring payments (Netflix, Spotify, etc.)
- **MongoDB Atlas Integration**: Cloud-based storage with Compass support

## Quick Start

### Prerequisites

- Docker and Docker Compose
- MongoDB Atlas account (or use local MongoDB)
- Anthropic API key (Claude)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd guppy-funds
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add:
# - MONGODB_URL (your MongoDB Atlas connection string)
# - ANTHROPIC_API_KEY (your Claude API key)
```

3. Start the services:
```bash
docker-compose up -d
```

4. Verify services are running:
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Usage

Upload a CSV file:
```bash
curl -X POST http://localhost:8000/v1/imports \
  -F "file=@your_file.csv" \
  -F "source_bank=amex"
```

The worker will automatically:
1. Parse the CSV into raw transactions
2. Enrich with AI (merchant normalization, categorization)
3. Mark as completed

Typically takes 30-60 seconds depending on number of new merchants.

## Architecture

### Collections

**1. `imports`**
- Tracks upload jobs and their lifecycle states
- States: uploaded → parsing → parsed → enriching → enriched → completed

**2. `transactions_raw`**
- Immutable storage of original CSV data
- Includes deduplication keys

**3. `transactions_enriched`**
- Unified, normalized transaction format
- AI-enriched with merchant data, categories, tags

**4. `merchants`**
- Cached merchant enrichment data
- Reduces API costs by reusing merchant information

### Services

**API Service** (`localhost:8000`)
- FastAPI REST API
- Handles CSV uploads
- Manual parse/enrich triggers

**Worker Service**
- Background job processor
- Automatically processes uploaded files
- Polls every 5 seconds for new jobs

## API Endpoints

### Core Endpoints

**Upload CSV**
```bash
POST /v1/imports
Content-Type: multipart/form-data
Body: file (CSV), source_bank (amex|citi|wells)
```

**Manual Parse** (optional - worker does this automatically)
```bash
POST /v1/imports/{import_id}/parse
```

**Manual Enrich** (optional - worker does this automatically)
```bash
POST /v1/imports/{import_id}/enrich
```

**Health Check**
```bash
GET /health
GET /
```

See `docs/API_USAGE_GUIDE.md` for detailed examples.

## Supported Banks

### AMEX
- **Columns**: Date, Description, Card Member, Account #, Amount, Extended Details, Category, etc.
- **Deduplication**: Reference field (unique transaction ID)
- **Features**: Full merchant details, category pre-assigned

### Citi
- **Columns**: Status, Date, Description, Debit, Credit, Member Name
- **Deduplication**: MD5 fingerprint (date + amount + description + member)
- **Features**: Separate debit/credit columns

### Wells Fargo
- **Columns**: No headers (Date, Amount, Flags, Description)
- **Deduplication**: MD5 fingerprint (date + amount + description)
- **Features**: Handles headerless CSV format

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://admin:admin123@localhost:27017` |
| `MONGODB_DB_NAME` | Database name | `guppy_funds` |
| `ANTHROPIC_API_KEY` | Claude API key | Required |
| `CLAUDE_MODEL` | Claude model to use | `claude-3-5-haiku-20241022` |
| `UPLOAD_DIR` | Directory for uploaded files | `./uploads` |
| `MAX_FILE_SIZE_MB` | Maximum upload size | `25` |

### Switching Between Local and Atlas MongoDB

The system supports both local MongoDB (via Docker) and MongoDB Atlas (cloud).

**Option 1: Local MongoDB (via Docker)**

1. Edit `.env`:
```bash
# Uncomment local, comment Atlas:
MONGODB_URL=mongodb://admin:admin123@mongodb:27017
# MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=guppy_funds
```

2. Start services (includes MongoDB container):
```bash
docker-compose up -d
```

**Option 2: MongoDB Atlas (Cloud)**

1. Edit `.env`:
```bash
# Comment local, uncomment Atlas:
# MONGODB_URL=mongodb://admin:admin123@mongodb:27017
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB_NAME=guppy_funds
```

2. Start services (MongoDB container runs but isn't used):
```bash
docker-compose up -d api worker
```

**That's it!** Just change one line in `.env` and restart. The local MongoDB container stays in docker-compose.yml but can be ignored when using Atlas.

## Development

### Project Structure

```
guppy-funds/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── models/          # Pydantic models
│   ├── parsers/         # CSV parsers (amex, citi, wells)
│   ├── enrichers/       # Claude AI enricher
│   ├── config.py        # Configuration
│   ├── database.py      # MongoDB connection
│   ├── main.py          # FastAPI app
│   └── worker.py        # Background job processor
├── docs/                # Specifications
├── test_files/          # Sample CSV files
├── uploads/             # Uploaded files (gitignored)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Running Locally (without Docker)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start API:
```bash
uvicorn app.main:app --reload
```

3. Start worker (in separate terminal):
```bash
python -m app.worker
```

## Viewing Data

Use **MongoDB Compass** to explore your data:

1. Connect to your MongoDB instance
2. Select `guppy_funds` database
3. Browse collections:
   - `transactions_enriched` - See AI-enriched transactions
   - `merchants` - View cached merchant data
   - `imports` - Monitor upload jobs

## Cost Optimization

The merchant caching system dramatically reduces API costs:

- **First upload**: ~$0.02-0.05 (Claude API calls for new merchants)
- **Subsequent uploads**: ~$0.001 (mostly cached merchants)
- **100 transactions**: Typically 50-70 unique merchants
- **Ongoing**: Most merchants reused, minimal API costs

## Troubleshooting

**Worker not processing:**
```bash
docker logs guppy-funds-worker
```

**API errors:**
```bash
docker logs guppy-funds-api
```

**Restart services:**
```bash
docker-compose restart
```

**Clear database and start fresh:**
Connect to MongoDB and drop collections, or use MongoDB Compass.

## Future Enhancements

- Additional bank parsers
- Transaction analytics endpoints
- Spending insights and trends
- Budget tracking
- Export functionality
- Web dashboard

## License

Personal project for financial management.
