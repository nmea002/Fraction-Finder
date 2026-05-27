"""
intent_classifier.py
--------------------
100% local intent extraction — no LLMs, no API keys, no credits.

Pipeline:
  1. Regex — infer query_type, extract study name, year, and author lname
  2. Exact substring match — against words.py synonym lists
  3. Fuzzy match — catches typos and paraphrases via rapidfuzz

To improve accuracy: add phrases to words.py. No retraining, no cost.
"""

from __future__ import annotations
import re

from rapidfuzz import fuzz

from words import master_intents


# ---------------------------------------------------------------------------
# Query-type inference
# ---------------------------------------------------------------------------
_COUNT_RE = re.compile(r"\b(how many|count|total|number of)\b", re.I)
_YESNO_RE = re.compile(r"\b(does|is there|are there|any|contain|do .+ have|exist)\b", re.I)


def _infer_query_type(text: str) -> str:
    if _COUNT_RE.search(text):
        return "count"
    if _YESNO_RE.search(text):
        return "yesno"
    return "fetch"


# ---------------------------------------------------------------------------
# Study extraction — "DeWolf 2016", "Braithwaite et al. 2017"
# Captures the full "Author Year" string for fuzzy matching against the DB
# ---------------------------------------------------------------------------
# Matches "Lastname Year" — camelcase allowed (DeWolf), et al. stripped if present
_STUDY_RE = re.compile(
    r"\b([A-Z][a-zA-Z]+)(?:\s+et\s+al\.?)?\s+((?:19|20)\d{2})\b"
)


def _extract_study(text: str) -> str | None:
    m = _STUDY_RE.search(text)
    # Always returns "Lastname Year" — et al. ignored since DB only stores lname
    return f"{m.group(1)} {m.group(2)}" if m else None


# ---------------------------------------------------------------------------
# Standalone year extraction — "from 2016", "year 2020", or bare 4-digit year
# Only fires if no full "Author Year" study string was found
# ---------------------------------------------------------------------------
_YEAR_RE = re.compile(
    r"\b(?:from|in|year|published\s+in)?\s*((?:19|20)\d{2})\b"
)


def _extract_year(text: str, study_found: bool) -> int | None:
    """Extract a standalone year filter. Skipped if a full study was already found."""
    if study_found:
        return None
    m = _YEAR_RE.search(text)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Standalone author extraction — "by DeWolf", "author DeWolf", or a bare
# capitalized word that looks like a surname when no full study was found
# ---------------------------------------------------------------------------
_AUTHOR_EXPLICIT_RE = re.compile(
    r"\b(?:by|author|from|of)\s+([A-Z][a-zA-Z]+)\b"
)
_AUTHOR_BARE_RE = re.compile(
    r"\b([A-Z][a-zA-Z]{2,})\b"  # bare capitalized word ≥3 chars, allows camelcase
)
# Words to ignore when scanning for bare surnames
_STOP_CAPS = {
    "Show", "List", "Find", "Get", "Give", "How", "Many", "Count",
    "Total", "Does", "Are", "There", "Any", "Is", "Both", "All",
    "What", "Which", "Where", "When", "Do", "Have", "Include",
    "Exclude", "With", "Without", "That", "From", "In", "The",
    "Crosses", "Above", "Below", "Half", "Unit", "Both",
}


def _extract_author(text: str, study_found: bool) -> str | None:
    """
    Extract a standalone author last name.
    Explicit patterns ('by DeWolf') take priority over bare-word scanning.
    Skipped if a full 'Author Year' study string already captured the name.
    """
    if study_found:
        return None

    # Priority 1: explicit signal word before the name
    m = _AUTHOR_EXPLICIT_RE.search(text)
    if m:
        return m.group(1)

    # Priority 2: bare capitalized word not in our stop list
    for m in _AUTHOR_BARE_RE.finditer(text):
        word = m.group(1)
        if word not in _STOP_CAPS:
            return word

    return None


# ---------------------------------------------------------------------------
# Build phrase lookup from words.py → [(phrase, category, label), ...]
# Sorted longest-first so specific phrases beat short ones
# ---------------------------------------------------------------------------
def _build_lookup(master: dict) -> list[tuple[str, str, str]]:
    rows = []
    for category, cfg in master.items():
        for label, phrases in cfg["options"].items():
            for phrase in phrases:
                rows.append((phrase.lower().strip(), category, label))
    rows.sort(key=lambda r: len(r[0]), reverse=True)
    return rows


_PHRASE_TABLE = _build_lookup(master_intents)


# ---------------------------------------------------------------------------
# Pass 1 — exact substring match
# ---------------------------------------------------------------------------
def _exact_pass(text: str) -> dict[str, str]:
    text_lower = text.lower()
    hits: dict[str, str] = {}
    for phrase, category, label in _PHRASE_TABLE:
        if category in hits:
            continue
        if phrase in text_lower:
            hits[category] = label
    return hits


# ---------------------------------------------------------------------------
# Pass 2 — fuzzy match for anything exact didn't catch
# ---------------------------------------------------------------------------
def _fuzzy_pass(text: str, resolved: set[str], threshold: int = 82) -> dict[str, str]:
    text_lower = text.lower()
    best: dict[str, tuple[str, int]] = {}

    for phrase, category, label in _PHRASE_TABLE:
        if category in resolved:
            continue
        score = fuzz.partial_ratio(phrase, text_lower)
        if score >= threshold:
            if category not in best or score > best[category][1]:
                best[category] = (label, score)

    return {cat: label for cat, (label, _) in best.items()}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
_ALL_INTENT_FIELDS = [
    "compatibility", "unit", "benchmark", "relation_to_half",
    "digit_label_pair", "common_components", "component_type",
    "gap_type", "pair_order",
]


def extract_intents(user_input: str) -> dict:
    """
    Extract structured intents from a user query with no external dependencies.

    Returned keys:
      query_type  — "count" | "fetch" | "yesno"
      study       — "Author Year" string for fuzzy DB lookup, or None
      year        — int year for direct filter, or None
      author      — author lname string for direct filter, or None
      + all label fields from _ALL_INTENT_FIELDS
    """
    study = _extract_study(user_input)
    study_found = study is not None

    result: dict = {
        "query_type": _infer_query_type(user_input),
        "study":      study,
        "year":       _extract_year(user_input, study_found),
        "author":     _extract_author(user_input, study_found),
    }
    for f in _ALL_INTENT_FIELDS:
        result[f] = None

    exact_hits = _exact_pass(user_input)
    result.update(exact_hits)

    fuzzy_hits = _fuzzy_pass(user_input, resolved=set(exact_hits.keys()))
    result.update(fuzzy_hits)

    return result
