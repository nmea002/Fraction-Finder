chat_flow = {
    "start": {
        "text": "Hey! What do you need help with?",
        "options": {
            "Stimuli Analysis": "stimuli_analysis",
            "Stimuli Generation": "stimuli_generation",
        }
    },
    "stimuli_analysis": {
        "text": "Attach the PDF or CSV that you want analyzed!",
        "expects_file": True,
        "next_state": "start"
    },
    "stimuli_generation": {
        "text": "Which filters do you want to choose? (Select all that apply)",
        "multi_select": True,
        "filters": ["Unit", "Benchmark", "Relation_To_Half", "Compatibility"],
        "next_state": "follow_up_filters"  # dynamic follow-ups handled in main code
    },
    "generate_results": {
        "text": "Generating stimuli using selected filters...",
        "options": {
            "Start over": "start"
        }
    }
}

follow_up_options = {
    "Unit": ["Both_Unit", "Includes_Unit", "Excludes_Unit"],
    "Benchmark": ["Both_Benchmark", "Includes_Benchmark", "Excludes_Benchmark"],
    "Relation_To_Half": ["Both_Above_Half", "Both_Below_Half", "Crosses", "Both_Half"],
    "Compatibility": ["Compatible", "Misleading"]
}