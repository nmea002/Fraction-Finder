import streamlit as st
from Task_1 import FractionGeneration as fg
from Task_1 import chatflow as cf
from Task_1 import StimuliAnalysis as sa 
import tempfile

st.set_page_config(page_title="Fraction Finder", layout="centered")
st.title("Fraction Finder")
st.sidebar.title("Navigation")
st.sidebar.page_link("FractionFinder.py", label="Fraction Finder")
st.sidebar.page_link("pages/Stimuli_Query_Chatbot.py", label="Stimuli Query Chatbot")
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
if "lower_limit" not in st.session_state:
    st.session_state["lower_limit"] = 1
if "upper_limit" not in st.session_state:
    st.session_state["upper_limit"] = 10

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
should_show_uploader = state_info.get("expects_file") and st.session_state.get("generated_file") is None

with st.chat_message("assistant"):
    # Assistant message
    if not state_info.get("expects_file") or should_show_uploader:
        st.write(state_info.get("text", ""))
        if hint := state_info.get("text_hint"):
            st.markdown(f"<p style='font-size:0.85em; color:#888;'>{hint}</p>", unsafe_allow_html=True)

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

    if state_info.get("expects_limits"):
        col1, col2 = st.columns(2)
        with col1:
            lower = st.number_input("Lower limit", min_value=1, max_value=98, value=1)
        with col2:
            upper = st.number_input("Upper limit", min_value=2, max_value=99, value=10)
        
        if st.button("Continue"):
            st.session_state["lower_limit"] = lower
            st.session_state["upper_limit"] = upper
            st.session_state["messages"].append({
                "role": "user", 
                "content": f"Range: {lower} to {upper}"
            })
            st.session_state["state"] = "stimuli_generation"
            st.rerun()

    # Expects file
    if state_info.get("expects_file") and st.session_state.get("generated_file") is None:
        uploaded_file = st.file_uploader("Upload CSV, XLSX, or PDF", type=["csv","xlsx","pdf"])
        if uploaded_file is not None:
            # Saves the uploaded file to a temporary path
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            generated_file = sa.stimuli_analysis(tmp_path)
            st.session_state["generated_file"] = {
                "data": generated_file,
                "filename": f"{uploaded_file.name.rsplit('.', 1)[0]}_annotated.csv",
                "task": "stimuli_analysis"
            }

            # Log user action
            st.session_state["messages"].append({
                "role": "user",
                "content": uploaded_file.name
            })

            # Add a new message saying the file is generated
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"Analysis complete! {len(generated_file)} pairs found."
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
        output_file = fg.getFilteredPairs(
            st.session_state["sub_filters"],
            lower=st.session_state["lower_limit"],
            upper=st.session_state["upper_limit"]
        )
        st.session_state["generated_file"] = {
            "data": output_file,
            "filename": "stimuli_output.csv",
            "task": "fraction_generation"
        }
        st.session_state["messages"].append({
            "role": "assistant",
            "content": f"Done! {len(output_file)} pairs generated."
        })
        st.session_state["state"] = "download_files"
        st.rerun()

# Show download button if the CSV exists
if st.session_state["generated_file"] is not None:
    gf = st.session_state["generated_file"]
    csv_bytes = gf["data"].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Stimuli CSV",
        data=csv_bytes,
        file_name=gf["filename"],
        mime="text/csv"
    )

    if st.button("Start Over"):
        st.session_state.clear()
        st.rerun()