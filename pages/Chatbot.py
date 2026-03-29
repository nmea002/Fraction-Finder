from Task_2.chatbot_interface import render_chat_interface
from Task_2.chatbot_logic import respond_to_prompt, _df_to_csv_string
import streamlit as st


def main() -> None:
    render_chat_interface(
        title="Stimuli Query Chatbot",
        welcome_text=(
            "Ask about stimuli used in studies, their authors, or publication years!"
        ),
        responder=respond_to_prompt,
        state_prefix="stimuli_chatbot",
        suggestions=[
            "Does DeWolf 2016 contain any misleading stimuli?",
            "How many unit fractions are in DeWolf 2016?",
            "Show me all compatible stimuli in DeWolf 2016",
        ],
        input_placeholder="Ask about studies, authors, or years",
    )

    # Render download button if a result df is available
    if "download_df" in st.session_state:
        csv = _df_to_csv_string(st.session_state["download_df"])
        st.download_button(
            label="⬇️ Download Stimuli CSV",
            data=csv,
            file_name="stimuli_results.csv",
            mime="text/csv",
        )

if __name__ == "__main__":
    main()
