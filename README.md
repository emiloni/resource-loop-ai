# ResourceLoop AI

**AI-Powered Resource Circularity & Redistribution Platform**

> **Before buying new resources or discarding usable ones, ask: what already exists that can solve the problem?**

---

## 🚀 Project at a Glance

**ResourceLoop AI** is an AI-powered circular resource intelligence platform that helps organizations **discover, match, reuse, redistribute, and analyze existing resources** before purchasing new ones or sending usable items to waste.

### Key Features

- 📦 **Resource Inventory** — Manage and track organizational resources.
- 🤖 **AI Resource Matching** — Convert natural-language requirements into structured specifications and find suitable existing resources.
- 🔍 **Underutilization Analysis** — Identify resources that are available but not being fully utilized.
- ♻️ **Circularity Engine** — Analyze unwanted or damaged resources and recommend actions such as **Repair → Reuse → Redistribute → Recycle**.
- 🏢 **Cross-Department Matching** — Discover resources available in other departments or organizational units.
- 🌐 **Cross-Organization Sharing** — Support resource discovery across participating organizations.
- 📊 **Impact Analytics** — Estimate environmental, financial, and circularity impact.
- 📄 **CSV / Excel Import** — Upload existing inventory data instead of entering resources manually.
- 🧠 **RAG-Based Policy Assistant** — Ask natural-language questions about organizational policies, guidelines, SOPs, and uploaded documents.
- 🔎 **Source-Grounded Answers** — RAG answers are generated from retrieved organizational documents with source references.
- 👥 **Organization-Based Access** — Keep organizational resources and knowledge separated through access control.
- 💡 **Explainable Recommendations** — Matching and AI recommendations provide reasoning rather than only returning a result.

### Core Idea

```text
              EXISTING RESOURCES
                     ↓
        ┌─────────────────────────┐
        │     ResourceLoop AI     │
        └─────────────────────────┘
             ↓       ↓       ↓
          MATCH    REUSE   REDISTRIBUTE
             ↓       ↓       ↓
        LESS PURCHASE • LESS WASTE • MORE UTILIZATION
```

**Aligned with UN SDG 12 — Responsible Consumption and Production**

---

## 🔗 Demo & Project Links

| Resource | Link |
|---|---|
| 🌐 **Live Deployed Application** | **(https://resource-loop-ai.onrender.com/)** |
| 🎥 **Demo Video** | **(https://youtu.be/Taap_ONBiNQ)** |
| 📊 **Project PPT** | **https://docs.google.com/presentation/d/1hk2MRdR6G089XFJbzdI9umgOiQjtdINM/edit?usp=drive_link&ouid=118124366965706991424&rtpof=true&sd=true** |

> **Start here:** Open the live application to explore the complete ResourceLoop AI workflow.

---

## 🎯 Problem

Organizations often have resources that are:

- unused or underutilized
- stored in another department
- suitable for reuse after minor repair
- available elsewhere within the organization
- discarded even though they still have useful value

At the same time, departments frequently purchase new resources to satisfy requirements that could potentially be fulfilled by existing inventory.

**ResourceLoop AI connects these two sides.**

---

## 💡 How It Works

```text
Resource Inventory
       ↓
Natural-Language Requirement
       ↓
AI Requirement Parsing
       ↓
Resource Matching
       ↓
Ranked Compatible Resources
       ↓
Circularity / Impact Analysis
       ↓
Reuse • Repair • Redistribute • Recycle
```

For organizational knowledge:

```text
Policies / SOPs / Documents
          ↓
      Document Chunking
          ↓
       Retrieval
          ↓
     Relevant Context
          ↓
      LLM via RAG
          ↓
   Answer + Sources
```

---

## 🧪 Demo Flow

### 1. Resource Dashboard
View available resources, utilization information, opportunities, and impact metrics.

### 2. Find a Resource

Example:

> "We need 10 computers for an AI lab with at least 16GB RAM, 512GB SSD and dedicated graphics."

### 3. AI Requirement Parsing

The system extracts structured requirements such as:

```text
Quantity: 10
RAM: ≥ 16 GB
Storage: ≥ 512 GB SSD
GPU: Dedicated
Use Case: AI Lab
```

### 4. AI Resource Matching

The matching engine searches existing resources and returns compatible options with matching details and explanations.

### 5. Circularity Analysis

A resource can be analyzed to determine its possible next life.

Example:

```text
Damaged Chair
     ↓
Repair Possible
     ↓
Reuse
```

Other possible outcomes include redistribution or recycling depending on the resource condition.

### 6. Impact Analysis

View the potential environmental and financial value created through reuse and redistribution.

### 7. RAG Policy Assistant

Upload organizational documents and ask questions such as:

> "Who approves the transfer of unused computers?"

The system retrieves relevant document sections and generates a grounded answer with source references.

---

## 🧠 AI & Intelligence

### AI Resource Matching

Natural-language requirements are converted into structured specifications and compared against available inventory.

The matching system considers relevant attributes such as:

- resource type
- specifications
- quantity
- availability
- condition
- department / organization
- requirement constraints

### RAG-Based Knowledge Assistant

ResourceLoop AI uses a Retrieval-Augmented Generation pipeline:

**Documents → Chunking → TF-IDF Retrieval → Relevant Context → LLM → Answer + Sources**

The system:

- retrieves relevant document chunks
- sends the retrieved context to the LLM
- answers using the organization's documents
- provides source references
- avoids inventing information when the knowledge base does not contain the answer

---

## 📊 Impact

ResourceLoop AI is designed to help organizations:

- reduce unnecessary purchases
- increase utilization of existing resources
- extend resource lifecycles
- reduce avoidable waste
- enable cross-department resource sharing
- quantify environmental and financial benefits

### Circularity Model

```text
          ┌───────────┐
          │   USE     │
          └─────┬─────┘
                ↓
          ┌───────────┐
          │   REUSE   │
          └─────┬─────┘
                ↓
          ┌───────────┐
          │  REPAIR   │
          └─────┬─────┘
                ↓
       ┌──────────────────┐
       │ REDISTRIBUTE /   │
       │    RECYCLE       │
       └──────────────────┘
```

---

## 🏢 Scalability

### Level 1 — Organization
Resource discovery within a single organization.

### Level 2 — Locality
Multiple organizations can participate in a shared resource network.

### Level 3 — City
Future expansion toward city-scale circular resource infrastructure.

---

## 🛠️ Technology Stack

- **Backend:** Python, FastAPI, SQLAlchemy
- **Database:** PostgreSQL / SQLite
- **Frontend:** HTML, CSS, JavaScript
- **AI / LLM:** OpenRouter
- **RAG:** TF-IDF + cosine similarity + LLM generation
- **Data Import:** CSV, Excel
- **Documents:** Organizational policies, SOPs, guidelines and other uploaded files
- **API:** REST APIs with FastAPI

---

## 📁 Project Structure

```text
resource-loop-ai/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routes/
│   │   └── services/
│   │
│   ├── static/
│   │   ├── index.html
│   │   └── js/
│   │
│   ├── uploads/
│   ├── seed_data.py
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## 🔌 Key API Endpoints

### Resources
- `GET /api/resources`
- `POST /api/resources`
- `GET /api/resources/{id}`
- `PUT /api/resources/{id}`
- `DELETE /api/resources/{id}`

### Matching
- `POST /api/matching/parse`
- `POST /api/matching/search`

### Circularity
- `POST /api/circularity/analyze`

### Import
- `POST /api/upload/import/preview`
- `POST /api/upload/import/confirm`

### Documents & RAG
- `GET /api/documents`
- `POST /api/documents/upload`
- `POST /api/documents/query`

### Dashboard & Impact
- `GET /api/dashboard`
- `GET /api/impact`

---

## 🔐 Responsible AI

ResourceLoop AI follows a human-in-the-loop approach:

- AI recommendations can be verified by users.
- Matching results provide explanations.
- RAG answers are grounded in uploaded organizational documents.
- The system does not intentionally fabricate missing policy information.
- Organization-level access controls help separate data.
- AI is used to assist decisions, not replace organizational authorization.

---

## 🚀 Local Setup

### Prerequisites

- Python 3.9+
- PostgreSQL

### Installation

```bash
git clone <repository-url>
cd resource-loop-ai/backend

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate

pip install -r requirements.txt
```

Configure your `.env` file with the required database, security, and AI configuration.

Start the backend:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Local Access

```text
Application:
http://localhost:8000

API Documentation:
http://localhost:8000/docs

Health Check:
http://localhost:8000/api/health
```

---

## 👤 Demo Accounts

| Username | Password | Role |
|---|---|---|
| admin | admin123 | Admin |
| ana | ana123 | Manager |
| carlos | carlos123 | Manager |
| maria | maria123 | User |

> Demo credentials are intended only for local/demo environments.

---

## 🌱 Vision

ResourceLoop AI aims to move organizations from a **linear resource model**

```text
BUY → USE → DISCARD
```

toward a **circular model**

```text
DISCOVER → MATCH → REUSE → REPAIR → REDISTRIBUTE → RECYCLE
```

**The goal is simple: maximize the value of resources that already exist.**

---

## 📄 License

MIT
