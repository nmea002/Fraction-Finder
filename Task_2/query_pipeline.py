from __future__ import annotations

from dataclasses import dataclass
import re
import sqlite3
from typing import Any

try:
	import psycopg
except Exception:
	psycopg = None

try:
	from supabase import Client, create_client
except Exception:
	Client = Any
	create_client = None

from Task_2.words import master_intents


@dataclass
class ParsedQuery:
	raw_prompt: str
	intent_values: list[str]
	unit_values: list[str]
	benchmark_values: list[str]
	relation_values: list[str]
	year: int | None
	search_name: str | None


def _normalize(text: str) -> str:
	return re.sub(r"\s+", " ", text.lower().strip())


def _extract_year(prompt: str) -> int | None:
	match = re.search(r"\b(19\d{2}|20\d{2}|21\d{2})\b", prompt)
	if not match:
		return None
	return int(match.group(1))


def _extract_name_hint(prompt: str) -> str | None:
	cleaned = re.sub(r"\b(19\d{2}|20\d{2}|21\d{2})\b", " ", prompt.lower())
	cleaned = re.sub(
		r"[^a-z\s]",
		" ",
		cleaned,
	)
	stop_words = {
		"does",
		"do",
		"is",
		"are",
		"contain",
		"contains",
		"have",
		"has",
		"any",
		"stimuli",
		"stimulus",
		"show",
		"find",
		"get",
		"with",
		"for",
		"the",
		"a",
		"an",
		"in",
		"of",
		"on",
		"to",
		"and",
		"or",
		"compatible",
		"misleading",
		"unit",
		"benchmark",
		"half",
		"above",
		"below",
		"crosses",
		"both",
	}
	tokens = [t for t in cleaned.split() if len(t) > 1 and t not in stop_words]
	if not tokens:
		return None
	return " ".join(tokens[:2])


def _match_intent_options(prompt: str, intent_group: str) -> list[str]:
	text = _normalize(prompt)
	options = master_intents[intent_group]["options"]
	matches: list[str] = []

	for canonical, phrases in options.items():
		all_phrases = [_normalize(p) for p in phrases]
		if canonical.lower() in text or any(phrase in text for phrase in all_phrases):
			matches.append(canonical)

	return matches


def parse_user_prompt(prompt: str) -> ParsedQuery:
	return ParsedQuery(
		raw_prompt=prompt,
		intent_values=_match_intent_options(prompt, "compatibility"),
		unit_values=_match_intent_options(prompt, "unit"),
		benchmark_values=_match_intent_options(prompt, "benchmark"),
		relation_values=_match_intent_options(prompt, "relation_to_half"),
		year=_extract_year(prompt),
		search_name=_extract_name_hint(prompt),
	)


def _make_placeholders(count: int, placeholder_style: str) -> str:
	if placeholder_style == "format":
		return ", ".join("%s" for _ in range(count))
	return ", ".join("?" for _ in range(count))


def build_sql(parsed: ParsedQuery, placeholder_style: str = "qmark") -> tuple[str, list[Any]]:
	where_clauses: list[str] = []
	params: list[Any] = []

	if parsed.intent_values:
		placeholders = _make_placeholders(len(parsed.intent_values), placeholder_style)
		where_clauses.append(f"s.compatibility IN ({placeholders})")
		params.extend(parsed.intent_values)

	if parsed.unit_values:
		placeholders = _make_placeholders(len(parsed.unit_values), placeholder_style)
		where_clauses.append(f"s.unit IN ({placeholders})")
		params.extend(parsed.unit_values)

	if parsed.benchmark_values:
		placeholders = _make_placeholders(len(parsed.benchmark_values), placeholder_style)
		where_clauses.append(f"s.benchmark IN ({placeholders})")
		params.extend(parsed.benchmark_values)

	if parsed.relation_values:
		placeholders = _make_placeholders(len(parsed.relation_values), placeholder_style)
		where_clauses.append(f"s.relation_to_half IN ({placeholders})")
		params.extend(parsed.relation_values)

	if parsed.year is not None:
		year_placeholder = "%s" if placeholder_style == "format" else "?"
		where_clauses.append(f"st.year = {year_placeholder}")
		params.append(parsed.year)

	if parsed.search_name:
		like_term = f"%{parsed.search_name.lower()}%"
		text_placeholder = "%s" if placeholder_style == "format" else "?"
		where_clauses.append(
			"(" 
			f"LOWER(st.title) LIKE {text_placeholder} "
			"OR EXISTS ("
			"SELECT 1 FROM stimuli_authors sa "
			"JOIN authors a ON a.id = sa.author_id "
			f"WHERE sa.stimuli_id = s.id AND LOWER(a.lname) LIKE {text_placeholder}"
			")"
			")"
		)
		params.extend([like_term, like_term])

	sql = (
		"SELECT COUNT(DISTINCT s.id) AS match_count "
		"FROM stimuli s "
		"JOIN stimuli_studies ss ON ss.stimuli_id = s.id "
		"JOIN studies st ON st.id = ss.study_id"
	)

	if where_clauses:
		sql += " WHERE " + " AND ".join(where_clauses)

	return sql, params


def run_sql_query(db_target: str, sql: str, params: list[Any], backend: str = "sqlite") -> int:
	if backend == "postgres":
		if psycopg is None:
			raise RuntimeError(
				"psycopg is not installed. Install psycopg[binary] to query Supabase Postgres."
			)
		with psycopg.connect(db_target) as conn:
			with conn.cursor() as cur:
				cur.execute(sql, params)
				row = cur.fetchone()
				return int(row[0]) if row else 0

	if backend != "sqlite":
		raise ValueError(f"Unsupported backend: {backend}")

	with sqlite3.connect(db_target) as conn:
		row = conn.execute(sql, params).fetchone()
		if not row:
			return 0
		return int(row[0])


def _extract_id_set(rows: list[dict[str, Any]], id_key: str) -> set[int]:
	values: set[int] = set()
	for row in rows:
		val = row.get(id_key)
		if val is None:
			continue
		values.add(int(val))
	return values


def _rows_from_response(response: Any) -> list[dict[str, Any]]:
	rows = getattr(response, "data", None)
	if not rows:
		return []
	return rows


def _fuzzy_like_pattern(text: str) -> str:
	# Make name matching robust to spaces/punctuation differences (e.g., DeWolf vs De Wolf).
	compact = re.sub(r"[^a-z0-9]", "", text.lower())
	if not compact:
		return "%"
	return "%" + "%".join(compact) + "%"


def _collect_ids_by_patterns(client: Any, table: str, id_key: str, column: str, patterns: list[str]) -> set[int]:
	matched_ids: set[int] = set()
	seen_patterns: set[str] = set()
	for pattern in patterns:
		if pattern in seen_patterns:
			continue
		seen_patterns.add(pattern)
		resp = client.table(table).select(id_key).ilike(column, pattern).execute()
		matched_ids |= _extract_id_set(_rows_from_response(resp), id_key)
	return matched_ids


def _apply_stimuli_value_filters(query: Any, parsed: ParsedQuery) -> Any:
	if parsed.intent_values:
		query = query.in_("compatibility", parsed.intent_values)
	if parsed.unit_values:
		query = query.in_("unit", parsed.unit_values)
	if parsed.benchmark_values:
		query = query.in_("benchmark", parsed.benchmark_values)
	if parsed.relation_values:
		query = query.in_("relation_to_half", parsed.relation_values)
	return query


def _stimuli_ids_from_study_ids(client: Any, study_ids: set[int]) -> set[int]:
	if not study_ids:
		return set()
	response = (
		client.table("stimuli_studies")
		.select("stimuli_id")
		.in_("study_id", sorted(study_ids))
		.execute()
	)
	return _extract_id_set(_rows_from_response(response), "stimuli_id")


def _stimuli_ids_from_author_ids(client: Any, author_ids: set[int]) -> set[int]:
	if not author_ids:
		return set()
	response = (
		client.table("stimuli_authors")
		.select("stimuli_id")
		.in_("author_id", sorted(author_ids))
		.execute()
	)
	return _extract_id_set(_rows_from_response(response), "stimuli_id")


def run_supabase_query(
	supabase_url: str,
	supabase_anon_key: str,
	parsed: ParsedQuery,
) -> int:
	if create_client is None:
		raise RuntimeError("supabase is not installed. Install supabase to use client mode.")

	client = create_client(supabase_url, supabase_anon_key)
	eligible_ids: set[int] | None = None

	if parsed.year is not None:
		study_resp = client.table("studies").select("id").eq("year", parsed.year).execute()
		study_ids = _extract_id_set(_rows_from_response(study_resp), "id")
		title_year_ids: set[int] = set()
		if not study_ids:
			title_year_resp = (
				client.table("studies")
				.select("id")
				.ilike("title", f"%{parsed.year}%")
				.execute()
			)
			title_year_ids = _extract_id_set(_rows_from_response(title_year_resp), "id")
			study_ids = study_ids | title_year_ids
		year_ids = _stimuli_ids_from_study_ids(client, study_ids)
		eligible_ids = year_ids

	if parsed.search_name:
		name_like = f"%{parsed.search_name}%"
		fuzzy_name_like = _fuzzy_like_pattern(parsed.search_name)
		name_patterns = [name_like, fuzzy_name_like]

		study_name_ids = _collect_ids_by_patterns(
			client,
			"studies",
			"id",
			"title",
			name_patterns,
		)
		title_ids = _stimuli_ids_from_study_ids(client, study_name_ids)

		author_ids = _collect_ids_by_patterns(
			client,
			"authors",
			"id",
			"lname",
			name_patterns,
		)
		author_stimuli_ids = _stimuli_ids_from_author_ids(client, author_ids)

		name_ids = title_ids | author_stimuli_ids
		if eligible_ids is None:
			eligible_ids = name_ids
		else:
			eligible_ids = eligible_ids & name_ids

	if eligible_ids is not None and not eligible_ids:
		return 0

	query = client.table("stimuli").select("id", count="exact")
	query = _apply_stimuli_value_filters(query, parsed)
	if eligible_ids is not None:
		query = query.in_("id", sorted(eligible_ids))

	response = query.execute()
	count = getattr(response, "count", None)
	if count is not None:
		return int(count)

	row_count = len(_rows_from_response(response))
	return row_count

