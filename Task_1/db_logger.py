import json
import streamlit as st
import sqlalchemy

def _conn():
    return st.connection("neon", type="sql")

def get_or_create_user(participant_id: str) -> int:
    conn = _conn()
    with conn.session as s:
        result = s.execute(
            sqlalchemy.text("SELECT id FROM users WHERE participant_id = :pid"),
            {"pid": participant_id}
        ).fetchone()
        if result:
            return int(result[0])
        result = s.execute(
            sqlalchemy.text("INSERT INTO users (participant_id) VALUES (:pid) RETURNING id"),
            {"pid": participant_id}
        ).fetchone()
        s.commit()
        return int(result[0])

def log_fraction_generation(user_id: int, filters: list, lower: int, upper: int, pairs_generated: int):
    try:
        conn = _conn()
        with conn.session as s:
            s.execute(sqlalchemy.text("""
                INSERT INTO fraction_generation_logs (user_id, filters, lower_limit, upper_limit, pairs_generated)
                VALUES (:uid, :filters, :lower, :upper, :count)
            """), {
                "uid":     user_id,
                "filters": json.dumps(filters),
                "lower":   lower,
                "upper":   upper,
                "count":   pairs_generated
            })
            s.commit()
    except Exception as e:
        print(f"[LOG ERROR] {e}")

def log_chatbot_query(user_id: int, user_query: str, intents: dict, results_count: int):
    try:
        conn = _conn()
        with conn.session as s:
            s.execute(sqlalchemy.text("""
                INSERT INTO chatbot_logs (user_id, user_query, intents, results_count)
                VALUES (:uid, :query, :intents, :count)
            """), {
                "uid":     user_id,
                "query":   user_query,
                "intents": json.dumps(intents),
                "count":   results_count
            })
            s.commit()
    except Exception as e:
        print(f"[LOG ERROR] {e}")