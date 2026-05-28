from __future__ import annotations
import sys, os
sys.path.append(os.path.dirname(__file__))

from intent_classifier import extract_intents
import io
from typing import List, Dict

import pandas as pd
import streamlit as st
from rapidfuzz import process, fuzz
from Task_1 import db_logger

def _conn():
    return st.connection("neon", type="sql")

# ═══════════════════════════════════════════════════════
# 1. STUDY FUZZY RESOLUTION
# ═══════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def _fetch_study_names() -> Dict[str, int]:
    """Returns {"DeWolf 2016": study_id, ...} for fuzzy matching."""
    df = _conn().query(
        """
        SELECT s.id, s.year, STRING_AGG(DISTINCT a.lname, ', ') AS authors
        FROM studies s
        JOIN stimuli_studies ss ON ss.study_id = s.id
        JOIN stimuli_authors sa ON sa.stimuli_id = ss.stimuli_id
        JOIN authors a          ON a.id = sa.author_id
        GROUP BY s.id, s.year
        """,
        ttl=300,
    )
    return {f"{row.authors} {row.year}": int(row.id) for row in df.itertuples()}


def _resolve_study(raw_label: str | None) -> tuple[str | None, int | None]:
    """Fuzzy-match an 'Author Year' string to a real study_id."""
    if not raw_label:
        return None, None
    study_map = _fetch_study_names()
    if not study_map:
        return None, None
    match, score, _ = process.extractOne(
        raw_label, list(study_map.keys()), scorer=fuzz.partial_ratio
    )
    if score >= 60:
        return match, study_map[match]
    return None, None


# ═══════════════════════════════════════════════════════
# 2. SQL BUILDER
# ═══════════════════════════════════════════════════════

# Columns that live directly on the stimuli table
_STIMULI_FILTER_COLS = {
    "compatibility":     "s.compatibility",
    "unit":              "s.unit",
    "benchmark":         "s.benchmark",
    "relation_to_half":  "s.relation_to_half",
    "digit_label_pair":  "s.digit_label_pair",
    "common_components": "s.common_components",
    "component_type":    "s.component_type",
    "gap_type":          "s.gap_type",
    "pair_order":        "s.pair_order",
}


def build_query(
    query_type: str,
    study_id: int | None,
    intents: dict,
) -> tuple[str, dict]:
    conditions: List[str] = []
    params: Dict[str, object] = {}

    # --- study_id (resolved from "Author Year" fuzzy match) ---
    if study_id is not None:
        conditions.append("ss.study_id = :study_id")
        params["study_id"] = study_id

    # --- standalone year filter (e.g. "show stimuli from 2016") ---
    year = intents.get("year")
    if year is not None:
        conditions.append("st.year = :year")
        params["year"] = int(year)

    # --- standalone author lname filter (e.g. "show stimuli by DeWolf") ---
    author = intents.get("author")
    if author:
        conditions.append("a.lname ILIKE :author")
        params["author"] = author  # ILIKE = case-insensitive match

    # --- stimuli column filters (compatibility, unit, benchmark, relation_to_half) ---
    for category, col in _STIMULI_FILTER_COLS.items():
        label = intents.get(category)
        if not label:
            continue
        key = f"p_{category}"
        conditions.append(f"{col} = :{key}")
        params[key] = label

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    base = """
        FROM stimuli s
        JOIN stimuli_studies ss ON s.id = ss.stimuli_id
        JOIN studies st         ON ss.study_id = st.id
        JOIN stimuli_authors sa ON s.id = sa.stimuli_id
        JOIN authors a          ON sa.author_id = a.id
    """

    if query_type == "count":
        sql = f"SELECT COUNT(*) AS cnt {base} {where}"
    else:
        sql = f"""
            SELECT s.fraction_pair, s.left_fraction, s.right_fraction,
                   s.compatibility, s.unit, s.benchmark, s.relation_to_half,
                   st.year AS study_year,
                   STRING_AGG(DISTINCT a.lname, ', ') AS authors
            {base} {where}
            GROUP BY s.id, s.left_fraction, s.right_fraction, s.fraction_pair,
                     s.compatibility, s.unit, s.benchmark, s.relation_to_half,
                     st.year
        """

    return sql.strip(), params


# ═══════════════════════════════════════════════════════
# 3. RESPONSE FORMATTER
# ═══════════════════════════════════════════════════════
def _df_to_csv_string(df: pd.DataFrame) -> str:
    out = df.copy()
    for col in ['left_fraction', 'right_fraction', 'fraction_pair']:
        if col in out.columns:
            out[col] = "" + out[col].astype(str)
    buf = io.StringIO()
    out.to_csv(buf, index=False)
    return buf.getvalue()


def format_response(
    query_type: str,
    df: pd.DataFrame,
    study_label: str | None,
    intents: dict,
) -> str:
    # Separate label filters from source filters (year/author)
    skip = {"query_type", "study", "year", "author"}
    label_filters = {k: v for k, v in intents.items() if v and k not in skip}
    year   = intents.get("year")
    author = intents.get("author")

    # Build a natural source description
    if study_label:
        source_desc = f" in **{study_label}**"
    elif author and year:
        source_desc = f" by **{author}** from **{year}**"
    elif author:
        source_desc = f" by **{author}** across various studies"
    elif year:
        source_desc = f" from studies published in **{year}**"
    else:
        source_desc = " across various studies"

    # Build filter description for label columns
    filter_str = ""
    if label_filters:
        filter_str = " with filters `" + ", ".join(f"{k}={v}" for k, v in label_filters.items()) + "`"

    if df.empty:
        return f"No stimuli found{source_desc}{filter_str}."

    if query_type == "count":
        n = int(df.iloc[0]["cnt"])
        return f"There are **{n}** stimuli{source_desc}{filter_str}. Download them below ⬇️"

    if query_type == "yesno":
        n = len(df)
        return f"Yes — there are **{n}** matching stimuli{source_desc}{filter_str}."

    return f"Here are stimuli{source_desc}{filter_str}. Download the CSV below ⬇️"


# ═══════════════════════════════════════════════════════
# 4. MAIN RESPONDER
# ═══════════════════════════════════════════════════════
def respond_to_prompt(user_input: str, history: list) -> str:
    intents = extract_intents(user_input)
    print(f"[DEBUG] intents={intents}")  # remove when stable

    query_type = intents.get("query_type", "fetch")
    study_label, study_id = _resolve_study(intents.get("study"))

    st.session_state.pop("download_df", None)

    # Check that at least one filter was found before hitting the DB
    has_filter = (
        study_id is not None
        or intents.get("year")
        or intents.get("author")
        or any(
            intents.get(k)
            for k in _STIMULI_FILTER_COLS
        )
    )
    if not has_filter:
        return (
            "I couldn't find a study, author, year, or any filter in your question. "
            "Try something like:\n"
            "- *'How many misleading stimuli are in DeWolf 2016?'*\n"
            "- *'Show all pairs where both fractions are above half'*\n"
            "- *'List stimuli by DeWolf'*\n"
            "- *'Count stimuli from 2016'*"
        )

    sql, params = build_query(query_type, study_id, intents)

    try:
        df = _conn().query(sql, params=params, ttl=0)
    except Exception as e:
        return f"Database error: {e}"
    
    participant_id = st.session_state.get("participant_id")
    if participant_id:
        user_id = db_logger.get_or_create_user(participant_id)
        db_logger.log_chatbot_query(user_id, user_input, intents, len(df))
    # For count queries, also fetch the rows so the user can download them
    if query_type == "count":
        fetch_sql, fetch_params = build_query("fetch", study_id, intents)
        try:
            fetch_df = _conn().query(fetch_sql, params=fetch_params, ttl=0)
            if not fetch_df.empty:
                st.session_state["download_df"] = fetch_df
        except Exception:
            pass
    elif not df.empty:
        st.session_state["download_df"] = df

    return format_response(query_type, df, study_label, intents)
