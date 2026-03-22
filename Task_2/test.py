import os
from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_ANON_KEY")

client = create_client(url, key)

response = client.table("stimuli").select("*").execute()
print(response.data)   # actual rows
print(response.count)  # row count
# print(f"Supabase URL: {url}"
#       f"\nSupabase Anon Key: {key}")

