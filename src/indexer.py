import os
from typing import List

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .t2sql import embed_texts


def _fetch_schema_descriptions(engine: Engine) -> List[dict]:
    sql = """
    SELECT table_schema, table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name, ordinal_position
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).mappings().all()
    return rows


def build_schema_index(engine: Engine) -> int:
    dim = int(os.getenv("VECTOR_DIM", "1536"))
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM schema_index"))

    rows = _fetch_schema_descriptions(engine)
    # Aggregate per-table description
    by_table = {}
    for r in rows:
        key = f"{r['table_schema']}.{r['table_name']}"
        by_table.setdefault(key, [])
        by_table[key].append(f"{r['column_name']}:{r['data_type']}")

    payloads = []
    for table_name, cols in by_table.items():
        content = f"Table {table_name} with columns: " + ", ".join(cols)
        payloads.append({"kind": "table", "identifier": table_name, "content": content})

    embeddings = embed_texts([p["content"] for p in payloads])

    with engine.begin() as conn:
        for p, e in zip(payloads, embeddings):
            conn.execute(
                text(
                    "INSERT INTO schema_index(kind, identifier, content, embedding) VALUES (:k, :i, :c, :e)"
                ),
                {"k": p["kind"], "i": p["identifier"], "c": p["content"], "e": e},
            )

    return len(payloads)


def retrieve_relevant_schema(engine: Engine, query: str, k: int = 5) -> str:
    query_vec = embed_texts([query])[0]
    sql = """
    SELECT identifier, content
    FROM schema_index
    ORDER BY embedding <-> :q
    LIMIT :k
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql), {"q": query_vec, "k": k}).mappings().all()
    parts = [f"[{r['identifier']}] {r['content']}" for r in rows]
    return "\n".join(parts)

