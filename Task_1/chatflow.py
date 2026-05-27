chat_flow = {
    "start": {
        "text": "Hey! What do you need help with?",
        "options": {
            "Stimuli Analysis": "stimuli_analysis",
            "Stimuli Generation": "set_limits",  # was "stimuli_generation"
        }
    },
    "stimuli_analysis": {
        "text": "Attach the PDF, XLSX, or CSV that you want analyzed!",
        "text_hint": "If you attach a PDF, make sure the file has a table with columns containing fraction pairs or something similar.",
        "expects_file": True,
        "next_state": "start"
    },
    "stimuli_generation": {
        "text": "Which filters do you want to choose? (Select all that apply)",
        "multi_select": True,
        "filters": ["Unit", "Benchmark", "Relation_To_Half", "Compatibility",
                     "Digit_Label_Pair", "Common_Components", "Component_Type", "Gap_Type", "Pair_Order"],
        "next_state": "follow_up_filters"
    },
    "set_limits": {
        "text": "Set the range for numerators and denominators.",
        "text_hint": "Lower limit is the lowest a numerator or denominator can be. Upper limit is the highest a numerator or denominator can be.",
        "expects_limits": True,
    },
    "generate_results": {
        "text": "Generating stimuli using selected filters...",
        "options": {
            "Start over": "start"
        }
    }
}

follow_up_options = {
    "Unit":             ["Both_Unit", "Includes_Unit", "Excludes_Unit"],
    "Benchmark":        ["Both_Benchmark", "Includes_Benchmark", "Excludes_Benchmark"],
    "Relation_To_Half": ["Both_Above_Half", "Both_Below_Half", "Crosses", "Both_Half"],
    "Compatibility":    ["Compatible", "Misleading"],
    "Digit_Label_Pair": ["Both_Only_Double_Digit", "Both_Only_Single_Digit", "Both_Mixed_Digits", "Different_Digit_Labels"],
    "Common_Components":["Common_Numerator", "Common_Denominator", "No_Common_Components"],
    "Component_Type":   ["Common_Components", "Without_Common_Components"],
    "Gap_Type":         ["Gap_Compatible", "Gap_Incompatible", "Gap_Neutral"],
    "Pair_Order":       ["Left_Larger", "Right_Larger", "Equal"],
}