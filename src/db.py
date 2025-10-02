import os
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from pgvector.psycopg import register_vector


def get_engine() -> Engine:
    host = os.getenv("DB_HOST", _get_secret("DB_HOST", "localhost"))
    port = os.getenv("DB_PORT", _get_secret("DB_PORT", "5432"))
    user = os.getenv("DB_USER", _get_secret("DB_USER", "postgres"))
    password = os.getenv("DB_PASSWORD", _get_secret("DB_PASSWORD", ""))
    dbname = os.getenv("DB_NAME", _get_secret("DB_NAME", "postgres"))
    sslmode = os.getenv("DB_SSLMODE", _get_secret("DB_SSLMODE", "prefer"))

    url = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
    engine = create_engine(url, pool_pre_ping=True)
    _register_pgvector_on_connect(engine)
    return engine


def _get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    try:
        import streamlit as st  # loaded only when running app
        return st.secrets.get(key, default)
    except Exception:
        return default


def ensure_vector_schema(engine: Engine) -> None:
    dim = int(os.getenv("VECTOR_DIM", _get_secret("VECTOR_DIM", "1536")))
    with engine.begin() as conn:
        register_vector(conn.connection)
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        ddl = f"
            CREATE TABLE IF NOT EXISTS schema_index (
                id BIGSERIAL PRIMARY KEY,
                kind TEXT NOT NULL,
                identifier TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding vector({dim})
            )
        "
        conn.execute(text(ddl))
        conn.execute(text("CREATE INDEX IF NOT EXISTS schema_index_embedding_idx ON schema_index USING ivfflat (embedding) WITH (lists = 100)"))


def run_sql(engine: Engine, sql_text: str) -> Optional[pd.DataFrame]:
    if not sql_text:
        return None
    with engine.connect() as conn:
        register_vector(conn.connection)
        result = conn.execute(text(sql_text))
        try:
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
        except Exception:
            return None


def _register_pgvector_on_connect(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, connection_record):  # type: ignore[unused-variable]
        try:
            register_vector(dbapi_conn)
        except Exception:
            pass

