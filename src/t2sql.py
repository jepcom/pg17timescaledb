import os
from typing import List

from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


SQL_SYSTEM_PROMPT = (
    "You are a senior data analyst. Generate a single dialect-correct PostgreSQL SQL query to answer the user question."
    " Use only tables and columns that exist based on the provided schema context."
    " Prefer safe aggregates and explicit casts. Limit to 1000 rows unless the task requires full results."
)


def _client():
    if OpenAI is None:
        raise RuntimeError("openai package not available")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # attempt to read from Streamlit secrets
        try:
            import streamlit as st
            api_key = st.secrets.get("OPENAI_API_KEY")
        except Exception:
            api_key = None
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    return OpenAI(api_key=api_key)


@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
def embed_texts(texts: List[str]) -> List[List[float]]:
    client = _client()
    model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]


@retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
def generate_sql(question: str, schema_context: str | None) -> str:
    client = _client()
    model = os.getenv("SQL_MODEL", "gpt-4o-mini")
    prompt_messages = [
        {"role": "system", "content": SQL_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Schema context:\n{schema_context or '(none)'}\n\n"
            f"Question: {question}\n"
            "Return only SQL code in a fenced block or raw text without commentary."
        )},
    ]

    resp = client.chat.completions.create(model=model, messages=prompt_messages, temperature=0)
    content = resp.choices[0].message.content or ""

    # Extract SQL from fenced code if present
    if "```" in content:
        parts = content.split("```")
        if len(parts) >= 2:
            body = parts[1]
            if body.strip().lower().startswith("sql"):
                body = "\n".join(body.splitlines()[1:])
            return body.strip()
    return content.strip()

