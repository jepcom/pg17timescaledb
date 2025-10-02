from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd
import plotly.graph_objects as go

try:
    from lida import Manager, TextGenerationConfig
except Exception:  # pragma: no cover
    Manager = None  # type: ignore
    TextGenerationConfig = None  # type: ignore


def init_lida():
    if Manager is None:
        raise RuntimeError("lida package not available")
    return Manager()


def visualize_dataframe(lida_mgr, df: pd.DataFrame, goal: str, n: int = 1) -> Tuple[Optional[go.Figure], str]:
    try:
        summary = lida_mgr.summarize(df)
        goals = lida_mgr.goals(summary=summary, n=n, user_query=goal)
        charts = lida_mgr.visualize(summary=summary, goal=goals[0], library="plotly", n=1)
        code = charts[0].code
        # Execute generated code in a controlled local namespace
        local_ns = {"pd": pd, "df": df, "go": go}
        exec(code, {}, local_ns)
        fig = local_ns.get("fig")
        explanation = lida_mgr.explain(code=code)
        return fig, explanation
    except Exception as e:
        # Fallback: simple table view
        return None, f"Visualization fallback due to error: {e}"

