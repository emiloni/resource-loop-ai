# ResourceLoop AI

**AI-Powered Resource Circularity and Redistribution Platform**

> Before an organization buys, manufactures, or discards something, first ask: can an existing resource solve the problem?

## What is ResourceLoop AI?

ResourceLoop AI is a circular resource intelligence platform that helps organizations discover unused potential in existing resources before purchasing new ones or sending usable items to waste.

It combines:
- **Resource Inventory** — Track all organizational resources
- **AI Matching** — Find existing resources that satisfy new requirements
- **Underutilization Analysis** — Detect resources with unused potential
- **Circularity Engine** — Recommend the best next life for unwanted resources
- **Cross-Organization Sharing** — Share resources between participating organizations
- **Impact Analytics** — Measure environmental and financial impact
- **RAG Knowledge Layer** — Query organizational policies and documents

## Core Philosophy

```
"Don't ask 'What should we buy?' first. 
 Ask 'What already exists that can solve the problem?'"
```

```
"Don't ask 'How do we dispose of it?' first. 
 Ask 'What is its best next life?'"
```

## Aligned with UN SDG 12 — Responsible Consumption and Production

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL

### Setup

```bash
# 1. Create PostgreSQL database
createdb resourceloop

# 2. Navigate to backend
cd backend

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 6. Seed database with demo data
python seed_data.py

# 7. Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Access

- **Frontend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## Demo Accounts

| Username | Password | Role | Organization |
|----------|----------|------|-------------|
| admin | admin123 | Admin | ITER |
| ana | ana123 | Manager | ITER (CS Dept) |
| carlos | carlos123 | Manager | ITER (Electronics) |
| maria | maria123 | User | ITER (Admin) |

## Demo Flow

1. **Dashboard** — View resource overview, opportunities, and impact
2. **Find a Resource** — Enter "We need 10 computers for an AI lab with at least 16GB RAM, 512GB SSD and dedicated graphics"
3. **AI parses requirements** — Shows structured requirements
4. **Matching engine** — Finds compatible resources across departments
5. **View matches** — See ranked results with explanations
6. **Circularity** — Describe a damaged chair → Get AI recommendation (Repair → Reuse)
7. **Impact** — View environmental and financial impact metrics

## Architecture

```
resource-loop-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   ├── database/             # Database connection
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── routes/               # API endpoints
│   │   ├── services/             # Business logic
│   │   └── ai/                   # AI services (stub interfaces)
│   ├── static/                   # Frontend SPA
│   │   ├── index.html
│   │   └── js/app.js
│   ├── uploads/                  # Uploaded files
│   ├── seed_data.py              # Demo data seeder
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## API Endpoints

### Resources
- `GET /api/resources` — List resources (filterable, paginated)
- `POST /api/resources` — Create resource
- `GET /api/resources/{id}` — Get resource details
- `PUT /api/resources/{id}` — Update resource
- `DELETE /api/resources/{id}` — Soft-delete resource

### Matching
- `POST /api/matching/parse` — Parse natural language requirements
- `POST /api/matching/search` — Parse + search for matching resources

### Circularity
- `POST /api/circularity/analyze` — Analyze resource and get recommendations

### Import
- `POST /api/upload/import/preview` — Preview CSV/Excel import
- `POST /api/upload/import/confirm` — Confirm and commit import

### Documents
- `GET /api/documents` — List documents
- `POST /api/documents/upload` — Upload document
- `POST /api/documents/query` — Query knowledge base (RAG)

### Organizations
- `GET /api/organizations` — List organizations
- `GET /api/organizations/network/overview` — Network view

### Dashboard & Impact
- `GET /api/dashboard` — Dashboard statistics
- `GET /api/impact` — Impact analytics

## Scalability Model

### Level 1 — Organization (Implemented)
Resources within a single organization.

### Level 2 — Locality (Implemented)
Multiple organizations sharing resources in a network.

### Level 3 — City (Coming Soon)
City-wide resource sharing infrastructure.

## AI Components

| Component | Current Implementation | Production Ready |
|-----------|----------------------|------------------|
| NLP / Requirement Parsing | Keyword-based | → LLM (GPT-4) |
| Resource Matching | Deterministic scoring | + Semantic embeddings |
| Circularity Analysis | Rule-based | + Computer vision |
| RAG / Document Q&A | Keyword search | + Vector DB + LLM |
| Underutilization Detection | Threshold-based | + ML prediction |

All AI service interfaces are designed for easy replacement with real models.

## Responsible AI Principles

- ✅ Human verification for AI-generated inventory
- ✅ Explainability for every recommendation
- ✅ Confidence/uncertainty display
- ✅ No fabricated information
- ✅ Data privacy between organizations
- ✅ Access control per organization

## Technologies

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: HTML/CSS/JS, Tailwind CSS
- **AI**: Pluggable interfaces (ready for OpenAI, embeddings, vision)
- **Import**: openpyxl (Excel), csv (CSV)

## License

MIT
