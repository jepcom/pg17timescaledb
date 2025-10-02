import os
import json
import pandas as pd
import streamlit as st

from src.db import get_engine, run_sql, ensure_vector_schema
from src.indexer import build_schema_index, retrieve_relevant_schema
from src.t2sql import generate_sql
from src.viz_lida import init_lida, visualize_dataframe


st.set_page_config(page_title="Analyst Notebook", layout="wide")


@st.cache_resource
def _engine():
    return get_engine()


@st.cache_resource
def _lida():
    return init_lida()


def sidebar_config():
    st.sidebar.header("Configuration")
    with st.sidebar.expander("Database", expanded=False):
        st.write("Configured via .streamlit/secrets.toml")
        if st.button("Ensure pgvector schema"):
            ensure_vector_schema(_engine())
            st.success("pgvector extension and index table ensured")
    with st.sidebar.expander("Indexing", expanded=True):
        if st.button("Build/Refresh Schema Index"):
            count = build_schema_index(_engine())
            st.success(f"Indexed schema entries: {count}")


def main():
    sidebar_config()
    st.title("Analyst Notebook - Streamlit + LIDA + pgvector")

    user_query = st.text_input("What do you want to analyze?", placeholder="e.g., Show top 10 customers by revenue in 2024")
    intent_choice = st.radio("Intent", options=["auto", "table", "chart"], horizontal=True)

    if st.button("Run") and user_query:
        with st.spinner("Retrieving relevant schema context..."):
            context = retrieve_relevant_schema(_engine(), user_query)
        with st.expander("Retrieved Schema Context"):
            st.code(context or "(none)")

        with st.spinner("Generating SQL..."):
            sql_text = generate_sql(user_query, context)
        st.subheader("Generated SQL")
        st.code(sql_text)

        with st.spinner("Executing SQL..."):
            df = run_sql(_engine(), sql_text)

        if df is None or df.empty:
            st.warning("No rows returned.")
            return

        st.subheader("Results Preview")
        st.dataframe(df.head(200))

        if intent_choice in ("auto", "chart"):
            with st.spinner("Creating visualization with LIDA..."):
                lida_app = _lida()
                fig, info = visualize_dataframe(lida_app, df, goal=user_query)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            if info:
                st.info(info)

        # Refinement UI
        st.divider()
        refine_col1, refine_col2 = st.columns([2,1])
        with refine_col1:
            refinement = st.text_input("Refine visualization (optional)", placeholder="e.g., change to stacked bar, group by region")
        with refine_col2:
            if st.button("Apply Refinement") and refinement:
                lida_app = _lida()
                fig2, info2 = visualize_dataframe(lida_app, df, goal=refinement)
                if fig2 is not None:
                    st.plotly_chart(fig2, use_container_width=True)
                if info2:
                    st.info(info2)


if __name__ == "__main__":
    main()

