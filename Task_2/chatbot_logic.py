from __future__ import annotations

import io
import re
from typing import List, Dict

import pandas as pd
import streamlit as st
from rapidfuzz import process, fuzz
from sentence_transformers import SentenceTransformer, util

import sys, os
sys.path.append(os.path.dirname(__file__))
from words import master_intents

# ── Model (cached so it only loads once) ─────────────────────────────────────
@st.cache_resource
def _load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


# ── DB connection (cached via Streamlit) ──────────────────────────────────────
def _conn():
    return st.connection("neon", type="sql")


# ═════════════════════════════════════════════════════════════════════════════
# 1. STUDY EXTRACTION  (rapidfuzz against real study names in the DB)
# ═════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def _fetch_study_names() -> Dict[str, int]:
    """Return {display_label: study_id} e.g. {'DeWolf 2016': 3}"""
    df = _conn().query(
        """
        SELECT s.id, s.year, STRING_AGG(DISTINCT a.lname, ', ') AS authors
        FROM studies s
        JOIN stimuli_studies ss ON ss.study_id = s.id
        JOIN stimuli_authors sa ON sa.stimuli_id = ss.stimuli_id
        JOIN authors a          ON a.id = sa.author_id
        GROUP BY s.id, s.year
        """,
        ttl=300
    )
    return {f"{row.authors} {row.year}": row.id for row in df.itertuples()}


def extract_study(text: str) -> tuple[str | None, int | None]:
    """Fuzzy-match a study name in the user's text. Returns (label, study_id)."""
    study_map = _fetch_study_names()
    if not study_map:
        return None, None
    match, score, _ = process.extractOne(
        text, list(study_map.keys()), scorer=fuzz.partial_ratio
    )
    if score >= 60:
        return match, study_map[match]
    return None, None


# ═════════════════════════════════════════════════════════════════════════════
# 2. INTENT EXTRACTION  (sentence-transformers against master_intents)
# ═════════════════════════════════════════════════════════════════════════════
# Keywords that suggest a category is being referenced at all
_CATEGORY_GATES = {
    "unit":             re.compile(r"\bunit\b", re.I),
    "benchmark":        re.compile(r"\bbenchmark\b", re.I),
    "relation_to_half": re.compile(r"\bhalf\b|\b1/2\b", re.I),
    "compatibility":    re.compile(r"\bmislead|compatible|bias|incompatible\b", re.I),
}

def extract_filters(text: str) -> Dict[str, str | None]:
    """
    Only match a category if the query actually mentions a relevant keyword,
    then use semantic similarity to pick the best label within that category.
    """
    model = _load_model()
    query_emb = model.encode(text, convert_to_tensor=True)
    filters: Dict[str, str | None] = {}

    for category, cfg in master_intents.items():
        # Skip this category entirely if no gate keyword is found
        if not _CATEGORY_GATES[category].search(text):
            filters[category] = None
            continue

        options = cfg["options"]
        choices: Dict[str, str] = {}
        for label, phrases in options.items():
            for phrase in phrases:
                choices[phrase] = label

        phrase_list = list(choices.keys())
        embs = model.encode(phrase_list, convert_to_tensor=True)
        scores = util.cos_sim(query_emb, embs)[0]
        best_idx = int(scores.argmax())
        best_score = float(scores[best_idx])

        filters[category] = choices[phrase_list[best_idx]] if best_score >= 0.35 else None

    return filters


# ═════════════════════════════════════════════════════════════════════════════
# 3. QUERY INTENT  (count / fetch rows / yes-no)
# ═════════════════════════════════════════════════════════════════════════════
_COUNT_RE   = re.compile(r"\b(how many|count|number of|total)\b", re.I)
_YESNO_RE   = re.compile(r"\b(does|do|is|are|has|have|any|contain|include)\b", re.I)
_FETCH_RE   = re.compile(r"\b(show|list|give me|return|get|what are|display|all stimuli|just get|fetch)\b", re.I)

def detect_query_type(text: str) -> str:
    if _COUNT_RE.search(text):  return "count"
    if _FETCH_RE.search(text):  return "fetch"
    if _YESNO_RE.search(text):  return "yesno"
    return "fetch"


# ═════════════════════════════════════════════════════════════════════════════
# 4. SQL BUILDER
# ═════════════════════════════════════════════════════════════════════════════
_FILTER_COLS = {
    "compatibility":    "s.compatibility",
    "unit":             "s.unit",
    "benchmark":        "s.benchmark",
    "relation_to_half": "s.relation_to_half",
}

def build_query(
    query_type: str,
    study_id: int | None,
    filters: Dict[str, str | None],
) -> tuple[str, dict]:
    """Return (sql, params)."""
    conditions: List[str] = []
    params: Dict[str, object] = {}

    if study_id is not None:
        conditions.append("ss.study_id = :study_id")
        params["study_id"] = study_id

    for category, label in filters.items():
        if label is None:
            continue
        col = _FILTER_COLS[category]
        key = f"p_{category}"
        conditions.append(f"{col} = :{key}")
        params[key] = label

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    base = """
        FROM stimuli s
        JOIN stimuli_studies ss  ON s.id = ss.stimuli_id
        JOIN studies st          ON ss.study_id = st.id
        JOIN stimuli_authors sa  ON s.id = sa.stimuli_id
        JOIN authors a           ON sa.author_id = a.id
    """

    if query_type == "count":
        sql = f"SELECT COUNT(*) AS cnt {base} {where}"
    else:
        sql = f"""
            SELECT s.fraction_1, s.fraction_2, s.fraction_pair,
                   s.compatibility, s.unit, s.benchmark, s.relation_to_half,
                   st.title AS study_title, st.year AS study_year,
                   STRING_AGG(a.lname, ', ') AS authors
            {base} {where}
            GROUP BY s.id, s.fraction_1, s.fraction_2, s.fraction_pair,
                     s.compatibility, s.unit, s.benchmark, s.relation_to_half,
                     st.title, st.year
        """

    return sql.strip(), params


# ═════════════════════════════════════════════════════════════════════════════
# 5. RESPONSE FORMATTER
# ═════════════════════════════════════════════════════════════════════════════
def _df_to_csv_string(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def format_response(
    query_type: str,
    df: pd.DataFrame,
    study_label: str | None,
    filters: Dict[str, str | None],
) -> str:
    active = {k: v for k, v in filters.items() if v}
    filter_desc = ", ".join(f"{k}={v}" for k, v in active.items())
    study_desc  = f" in **{study_label}**" if study_label else ""
    filter_str  = f" with filters `{filter_desc}`" if filter_desc else ""

    if df.empty:
        return f"No stimuli found{study_desc}{filter_str}."

    if query_type == "count":
        n = int(df.iloc[0]["cnt"])
        return f"There are **{n}** stimuli{study_desc}{filter_str}. Download them below ⬇️"

    if query_type == "yesno":
        n = len(df)
        return f"Yes — there are **{n}** matching stimuli{study_desc}{filter_str}."

    # fetch → summary only; download button rendered in Chatbot.py
    return f"Found **{len(df)}** stimuli{study_desc}{filter_str}. Download the CSV below ⬇️"


# ═════════════════════════════════════════════════════════════════════════════
# 6. MAIN RESPONDER  (plug into render_chat_interface)
# ═════════════════════════════════════════════════════════════════════════════
def respond_to_prompt(user_input: str, history: list) -> str:
    study_label, study_id = extract_study(user_input)
    filters    = extract_filters(user_input)
    query_type = detect_query_type(user_input)

    # Clear any previous download
    st.session_state.pop("download_df", None)

    active_filters = {k: v for k, v in filters.items() if v}
    if study_id is None and not active_filters:
        return (
            "I couldn't find a study or any filter in your question. "
            "Try something like: *'How many misleading stimuli are in DeWolf 2016?'* "
            "or *'Get all stimuli from DeWolf 2016'*"
        )

    sql, params = build_query(query_type, study_id, filters)

    try:
        df = _conn().query(sql, params=params, ttl=0)
    except Exception as e:
        return f"Database error: {e}"

    # Always fetch rows too so download is available
    if query_type == "count":
        fetch_sql, fetch_params = build_query("fetch", study_id, filters)
        try:
            fetch_df = _conn().query(fetch_sql, params=fetch_params, ttl=0)
            if not fetch_df.empty:
                st.session_state["download_df"] = fetch_df
        except Exception:
            pass
    elif not df.empty:
        st.session_state["download_df"] = df

    return format_response(query_type, df, study_label, filters)