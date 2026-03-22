from __future__ import annotations

import os
from typing import Dict, List

from Task_2.query_pipeline import (
	build_sql,
	parse_user_prompt,
	run_sql_query,
	run_supabase_query,
)


Message = Dict[str, str]


def _format_filters_for_user(parsed) -> str:
	parts: list[str] = []

	if parsed.intent_values:
		parts.append(f"compatibility={', '.join(parsed.intent_values)}")
	if parsed.unit_values:
		parts.append(f"unit={', '.join(parsed.unit_values)}")
	if parsed.benchmark_values:
		parts.append(f"benchmark={', '.join(parsed.benchmark_values)}")
	if parsed.relation_values:
		parts.append(f"relation_to_half={', '.join(parsed.relation_values)}")
	if parsed.year is not None:
		parts.append(f"year={parsed.year}")
	if parsed.search_name:
		parts.append(f"name~{parsed.search_name}")

	if not parts:
		return "no explicit filters"
	return "; ".join(parts)


def respond_to_prompt(prompt: str, _history: List[Message]) -> str:
	supabase_db_url = os.getenv("SUPABASE_DB_URL")
	supabase_url = os.getenv("SUPABASE_URL")
	supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
	parsed = parse_user_prompt(prompt)

	if supabase_url and supabase_anon_key:
		try:
			match_count = run_supabase_query(supabase_url, supabase_anon_key, parsed)
		except RuntimeError as exc:
			return str(exc)
		except Exception as exc:
			return f"I hit a Supabase client error: {exc}"

		if match_count > 0:
			answer = f"Yes. I found {match_count} matching stimuli."
		else:
			answer = "No. I did not find any matching stimuli."

		debug_summary = _format_filters_for_user(parsed)
		return (
			f"{answer}\n\n"
			f"Filters: {debug_summary}\n"
			"Mode: Supabase client"
		)

	if supabase_db_url:
		backend = "postgres"
		db_target = supabase_db_url
		placeholder_style = "format"
	else:
		backend = "sqlite"
		db_target = os.getenv("FRACTION_DB_PATH", "fraction_finder.db")
		placeholder_style = "qmark"

	sql, params = build_sql(parsed, placeholder_style=placeholder_style)

	try:
		match_count = run_sql_query(db_target, sql, params, backend=backend)
	except FileNotFoundError:
		return (
			"I could not find your database file. "
			"Set FRACTION_DB_PATH to your sqlite database path and try again."
		)
	except RuntimeError as exc:
		return str(exc)
	except Exception as exc:
		return f"I hit a database error: {exc}"

	if match_count > 0:
		answer = f"Yes. I found {match_count} matching stimuli."
	else:
		answer = "No. I did not find any matching stimuli."

	debug_summary = _format_filters_for_user(parsed)
	return (
		f"{answer}\n\n"
		f"Filters: {debug_summary}\n"
		f"SQL: {sql}\n"
		f"Parameters: {params}"
	)

