Analyst Notebook Platform (Streamlit + LIDA + MindsDB/pgvector)

Overview
This project provides a notebook-style analyst platform using Streamlit for UI, LIDA for automated visualization generation, OpenAI for text-to-SQL, and PostgreSQL with pgvector for schema/document embeddings. Optionally integrate MindsDB for model hosting/AutoML.

Quickstart
1) Install Python 3.10+
2) Create virtualenv and install deps:
   pip install -r requirements.txt
3) Configure secrets in .streamlit/secrets.toml (see below)
4) Run:
   streamlit run app.py

Docker
1) Build and start stack (Postgres + MindsDB + app):
   docker compose up --build -d
2) App at http://localhost:8501, Postgres at localhost:5432, MindsDB at http://localhost:47334
3) Container aliases (internal network):
   - pgvector: Postgres with pgvector
   - missen: MindsDB service alias
4) Env overrides via .env (OPENAI_API_KEY etc.)

Configuration
Create .streamlit/secrets.toml with:

OPENAI_API_KEY = "your-openai-key"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "password"
DB_NAME = "analytics"
DB_SSLMODE = "prefer"
VECTOR_DIM = "1536"  # match embedding model dim

# Optional MindsDB
MINDSDB_HOST = "http://127.0.0.1:47334"

Features
- Text-to-SQL via OpenAI
- Schema embeddings via pgvector for better SQL grounding
- Automated chart selection and generation via LIDA (Plotly backend)
- Streamlit UI with chat-like flow and refinement hooks

Structure
app.py
src/db.py
src/indexer.py
src/t2sql.py
src/viz_lida.py

Notes
- Ensure pgvector extension is installed on the target Postgres: CREATE EXTENSION IF NOT EXISTS vector;
- LIDA performs best with narrow tables (< ~10 columns). For wider tables, subset to relevant columns.

