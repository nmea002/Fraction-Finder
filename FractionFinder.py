import streamlit as st
from Task_1 import FractionGeneration as fg
from Task_1 import chatflow as cf
from Task_1 import StimuliAnalysis as sa 
import tempfile

st.set_page_config(page_title="Fraction Finder", layout="centered")
st.title("Fraction Finder")
CHAT_FLOW = cf.chat_flow

# st.sidebar.title("Navigation")
# if st.sidebar.button("Chatbot"):
#     st.switch_page(r"pages/Chat.py")

# ---------------------------
# Initialize session state
# ---------------------------
if "state" not in st.session_state:
    st.session_state["state"] = "start"
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "filter_queue" not in st.session_state:
    st.session_state["filter_queue"] = []
if "sub_filters" not in st.session_state:
    st.session_state["sub_filters"] = []
if "generated_file" not in st.session_state:
    st.session_state["generated_file"] = None

# ---------------------------
# Display chat history
# ---------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------------------
# Handle current state
# ---------------------------
current_state = st.session_state["state"]
state_info = CHAT_FLOW.get(current_state, {})

# ---------------------------
# UI Rendering 
# ---------------------------
should_show_uploader = state_info.get("expects_file") and not st.session_state.get("generated_file")

with st.chat_message("assistant"):
    # Assistant message
    if not state_info.get("expects_file") or should_show_uploader:
        st.write(state_info.get("text", ""))

    # Multi-select for filters
    if state_info.get("multi_select"):
        selected_filters = []
        for filter in state_info.get("filters", []):
            if st.checkbox(filter, key=f"{current_state}_{filter}"):
                selected_filters.append(filter)

        if st.button("Continue"):
            st.session_state["messages"].append({"role": "user", "content": ", ".join(selected_filters)})
            st.session_state["filter_queue"] = selected_filters.copy()
            st.session_state["state"] = "follow_up_filters"
            st.rerun()

    # Single select navigation
    if isinstance(state_info.get("options"), dict):
        cols = st.columns(len(state_info["options"]))

        for col, (label, next_state) in zip(cols, state_info["options"].items()):
            with col:
                if st.button(label):
                    st.session_state["messages"].append({"role": "user", "content": label})
                    st.session_state.state = next_state
                    st.rerun()
    
    # Expects file
    if state_info.get("expects_file") and not st.session_state.get("generated_file"):
        uploaded_file = st.file_uploader("Upload CSV or PDF", type=["csv", "pdf"])
        if uploaded_file is not None:
            # Saves the uploaded file to a temporary path
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            generated_file = sa.stimuli_analysis(tmp_path)
            st.session_state["generated_file"] = generated_file

            # Log user action
            st.session_state["messages"].append({
                "role": "user",
                "content": uploaded_file.name
            })

            # Add a new message saying the file is generated
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"File generated: {generated_file}"
            })



# ---------------------------
# Handling for All States
# ---------------------------

# Follow-up questions for each selected filter
if current_state == "follow_up_filters" and st.session_state["filter_queue"]:
    current_filter = st.session_state.filter_queue[0]

    follow_up_options = cf.follow_up_options

    with st.chat_message("assistant"):
        st.write(f"For {current_filter}, what do you want?")

    for opt in follow_up_options.get(current_filter, []):
        if st.button(opt, key=f"{current_filter}_{opt}"):
            st.session_state["sub_filters"].append(opt)
            st.session_state["filter_queue"].pop(0)
            st.rerun()

# Generate CSV after all follow-ups
if current_state == "follow_up_filters" and not st.session_state["filter_queue"]:
    if "generated_file" not in st.session_state or st.session_state["generated_file"] is None:
        output_file = fg.getFilteredPairs(st.session_state["sub_filters"])
        st.session_state["generated_file"] = output_file
        st.session_state["state"] = "download_files"

# Show download button if the CSV exists
if st.session_state["generated_file"]:
    with open(st.session_state["generated_file"], "rb") as f:
        st.download_button(
            label="Download Stimuli CSV",
            data=f,
            file_name=st.session_state["generated_file"],
            mime="text/csv"
        )

    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()