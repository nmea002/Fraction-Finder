import re

import streamlit as st

from chatbot_interface import render_chat_interface
from Task_2.chatbot_logic import match_intents
from Task_2.words import master_intents


KNOWN_AUTHORS = ["Lee", "DeWolf", "Steiner"]


def _contains_any(text: str, terms: list[str]) -> bool:
	lowered = text.lower()
	return any(term in lowered for term in terms)


def _extract_year(text: str) -> str | None:
	found = re.search(r"\b(18|19|20)\d{2}\b", text)
	return found.group(0) if found else None


def site_responder(prompt: str, _history: list[dict[str, str]]) -> str:
	"""General site-aware response strategy for the chatbot page."""
	if _contains_any(prompt, ["hi", "hello", "hey"]):
		return (
			"Hi! I can help with Fraction Finder tasks:\n\n"
			"- explain stimuli generation filters\n"
			"- guide you through stimuli analysis uploads\n"
			"- interpret filter language in your prompt"
		)

	if _contains_any(prompt, ["what can you do", "help", "how does this work"]):
		return (
			"I am a general assistant for this site. Try asking:\n\n"
			"- `How do I generate stimuli?`\n"
			"- `What does misleading mean?`\n"
			"- `Find misleading stimuli in DeWolf 2016`\n"
			"- `What filters are available?`"
		)

	if _contains_any(prompt, ["generate", "generation", "filters", "stimuli generation"]):
		return (
			"Stimuli generation supports these filter groups:\n\n"
			"- Unit: Both_Unit, Includes_Unit, Excludes_Unit\n"
			"- Benchmark: Both_Benchmark, Includes_Benchmark, Excludes_Benchmark\n"
			"- Relation_To_Half: Both_Above_Half, Both_Below_Half, Crosses, Both_Half\n"
			"- Compatibility: Compatible, Misleading\n\n"
			"In the main page, select one or more groups and the app will ask follow-up options."
		)

	if _contains_any(prompt, ["analysis", "upload", "pdf", "csv"]):
		return (
			"For stimuli analysis, upload a CSV or PDF from the main workflow. "
			"The app processes it and prepares an output CSV for download."
		)

	detected_intents = match_intents(prompt, master_intents)
	year = _extract_year(prompt)
	mentioned_authors = [name for name in KNOWN_AUTHORS if name.lower() in prompt.lower()]

	if detected_intents or year or mentioned_authors:
		lines: list[str] = ["I parsed this from your question:"]
		if mentioned_authors:
			lines.append(f"- Author(s): {', '.join(mentioned_authors)}")
		if year:
			lines.append(f"- Year: {year}")
		if detected_intents:
			lines.append("- Filters:")
			for intent_name, info in detected_intents.items():
				lines.append(f"  - {intent_name}: {info['option']} (score={info['score']:.2f})")

		lines.append(
			"If you want, I can help you rewrite this as a clean database query prompt next."
		)
		return "\n".join(lines)

	return (
		"I can help with Fraction Finder workflows and filter language. "
		"Try asking about stimuli generation, analysis uploads, or specific filter meanings."
	)


st.set_page_config(page_title="Chatbot", layout="centered")

render_chat_interface(
	title="Fraction Finder Chatbot",
	welcome_text=(
		"Welcome to the Fraction Finder chatbot. "
		"Ask about generation filters, analysis workflow, or a natural-language stimuli request."
	),
	responder=site_responder,
	state_prefix="site_chatbot",
	suggestions=[
		"How do I generate stimuli?",
		"What does misleading mean?",
		"Find misleading stimuli in DeWolf 2016",
	],
	input_placeholder="Ask about filters, uploads, or stimuli prompts...",
)