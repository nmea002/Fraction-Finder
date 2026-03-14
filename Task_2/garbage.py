import chatbot_logic as cl
from words import master_intents
import supabase 

prompt = "What were the misleading stimuli in DeWolf, 2016?"
authors = ["lee", "dewolf", "steiner"]

author, score = cl.match_author(prompt, authors)
year = cl.match_year(prompt)
results = cl.match_intents(prompt, master_intents)

query = supabase.table("stimuli_with_authors").select("*")

if author:
    query = query.eq("author_lname", author)

if year:
    query = query.eq("year", year)

for filter_name, info in results.items():
    query = query.eq(filter_name, info["option"])

resp = query.execute()
data = resp.data