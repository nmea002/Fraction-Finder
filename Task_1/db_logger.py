# db_logger.py
import json
import streamlit as st

def _conn():
    return st.connection("neon", type="sql")

def get_or_create_user(participant_id: str) -> int:
    """Returns the user's id, creating them if they don't exist."""
    df = _conn().query(
        "SELECT id FROM users WHERE participant_id = :pid",
        params={"pid": participant_id}, ttl=0
    )
    if not df.empty:
        return int(df.iloc[0]["id"])
    
    df = _conn().query(
        "INSERT INTO users (participant_id) VALUES (:pid) RETURNING id",
        params={"pid": participant_id}, ttl=0
    )
    return int(df.iloc[0]["id"])

def log_fraction_generation(user_id: int, filters: list, lower: int, upper: int, pairs_generated: int):
    try:
        _conn().query("""
            INSERT INTO fraction_generation_logs (user_id, filters, lower_limit, upper_limit, pairs_generated)
            VALUES (:uid, :filters, :lower, :upper, :count)
        """, params={
            "uid":     user_id,
            "filters": json.dumps(filters),
            "lower":   lower,
            "upper":   upper,
            "count":   pairs_generated
        }, ttl=0)
    except Exception as e:
        print(f"[LOG ERROR] {e}")

def log_chatbot_query(user_id: int, user_query: str, intents: dict, results_count: int):
    try:
        _conn().query("""
            INSERT INTO chatbot_logs (user_id, user_query, intents, results_count)
            VALUES (:uid, :query, :intents, :count)
        """, params={
            "uid":     user_id,
            "query":   user_query,
            "intents": json.dumps(intents),
            "count":   results_count
        }, ttl=0)
    except Exception as e:
        print(f"[LOG ERROR] {e}")