# MindScroll Recommender — Step 1: Database + Ingestion

This starter kit sets up a **PostgreSQL + pgvector** database schema and a Python ingestion script
to load your JSON content and compute embeddings for similarity search.

## 0) Prerequisites

### Install PostgreSQL
- **Ubuntu/Debian**
  ```bash
  sudo apt update
  sudo apt install -y postgresql postgresql-contrib
  ```
- **macOS (Homebrew)**
  ```bash
  brew install postgresql
  brew services start postgresql
  ```
- **Windows**
  - Install from: https://www.postgresql.org/download/
  - During install, also run **StackBuilder** to add the **pgvector** extension if available.

### Install pgvector
- **Ubuntu/Debian** (for PG16, adjust if needed):
  ```bash
  sudo apt install -y postgresql-16-pgvector
  ```
- **macOS (Homebrew)**
  ```bash
  brew install pgvector
  ```
- **Windows**
  - If not provided via StackBuilder, build from source: https://github.com/pgvector/pgvector

> You must enable the extension **inside your database** after it's created:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Python
Create a virtual environment and install deps:
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## 1) Create database & user (example)

Use `psql` (replace passwords and names as you like):

```bash
# open psql as the postgres superuser
sudo -u postgres psql    # Ubuntu/Debian
# or: psql -U postgres   # if you already have a postgres user/pass
```

Inside psql:
```sql
CREATE DATABASE mindscroll;
CREATE USER minduser WITH ENCRYPTED PASSWORD 'mindpass';
GRANT ALL PRIVILEGES ON DATABASE mindscroll TO minduser;
\c mindscroll
CREATE EXTENSION IF NOT EXISTS vector;
```

## 2) Configure environment

Copy `.env.example` to `.env` and update if needed.
```bash
cp .env.example .env
```

## 3) Initialize schema

```bash
python scripts/init_db.py
```

This runs `sql/schema.sql` and `sql/indices.sql` in your target DB.

## 4) Load your JSON content

Place your JSON list file somewhere (e.g., `data/content.json`). The expected format is a **list of article dicts**, e.g.

```json
[
  {
    "guid": "https://example.com/abc123",
    "title": "Sample Title",
    "link": "https://example.com/post",
    "published": "Sun, 17 Aug 2025 07:30:00 +0000",
    "summary": "short summary",
    "description": "<p>html</p>",
    "image_url": "https://example.com/img.jpg",
    "author": "Author",
    "source": "https://example.com/feed/",
    "content": "Full text here",
    "rss_categories": ["Stocks", "News"],
    "categories": [{"category": "Investing & Trading", "score": 0.92}],
    "LLM_CONTENT": {
      "title": "Readable title",
      "content": "Readable content",
      "tags": ["stocks", "investing"],
      "rating": "UA",
      "difficulty": "Beginner"
    },
    "likes": 0,
    "views": 0
  }
]
```

Then run:
```bash
python app/load_content.py /path/to/your/content.json
```

## 5) Next Steps

- Add user profiles and embeddings
- Implement candidate generation + custom reranking
- Expose `/recommend` API

---

### Troubleshooting

- If `CREATE EXTENSION vector` fails, ensure pgvector is installed for your Postgres version.
- If `sentence-transformers` fails to install, ensure a recent `pip` and Python 3.10+.
- On first run, the embedding model will download (internet required).

