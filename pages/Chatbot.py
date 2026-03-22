from chatbot_interface import render_chat_interface
from Task_2.chatbot_logic import respond_to_prompt


def main() -> None:
	render_chat_interface(
		title="Stimuli Query Chatbot",
		welcome_text=(
			"Ask about stimuli in your database and I will translate your request "
			"into SQL."
		),
		responder=respond_to_prompt,
		state_prefix="stimuli_chatbot",
		suggestions=[
			"Does dewolf 2016 contain any misleading stimuli?",
			"How many compatible stimuli are in 2014?",
			"Find stimuli with both above half and benchmark included",
		],
		input_placeholder="Ask about studies, authors, years, and intent filters...",
	)


if __name__ == "__main__":
	main()

