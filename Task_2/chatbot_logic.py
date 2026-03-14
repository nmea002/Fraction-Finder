from rapidfuzz import fuzz
import re

THRESH = 80

def normalize(prompt):
    prompt = prompt.lower()
    prompt = re.sub(r"et al\.?", "", prompt)
    prompt = re.sub(r"[^\w\s]", "", prompt)
    prompt = prompt.strip()
    return prompt

def match_year(prompt):
    year_match = re.search(r"\b(18|19|20)\d{2}\b", prompt)
    year = int(year_match.group()) 
    return year 

def match_author(prompt, authors, threshold=THRESH):
    prompt = normalize(prompt)

    best_match = None
    best_score = 0

    for name in authors:
        name = normalize(name)
        score = fuzz.partial_ratio(name, prompt)
        if score > best_score:
            best_score = score
            best_match = name

    if best_score >= threshold:
        return best_match, best_score
    else:
        return None, best_score

def similarity(a, b):
    return fuzz.partial_ratio(a, b) 

def match_intents(prompt, master_intents, threshold=float(THRESH)/100.0, exact_boost: float = 0.15):
    prompt = normalize(prompt)

    results = {}  
    for intent, intent_data in master_intents.items():
        best = {"option": None, "score": 0.0, "phrase": None}

        for option, phrases in intent_data["options"].items():
            for phrase in phrases:
                orig_phrase = phrase
                phrase = normalize(phrase)
                score = fuzz.partial_ratio(prompt, phrase) / 100

                if phrase in prompt:
                    score = min(1.0, score + exact_boost + 0.25)

                phrase_tokens = set(phrase.split())
                prompt_tokens = set(prompt.split())
                token_overlap = len(phrase_tokens & prompt_tokens) / max(1, len(phrase_tokens))
                score = max(score, token_overlap)

                if score > best["score"]:
                    best = {"option": option, "score": float(score), "phrase": orig_phrase}

        if best["score"] >= threshold:
            results[intent] = best

    return results
