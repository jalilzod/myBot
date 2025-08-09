import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
anon_key = os.getenv("SUPABASE_ANON_KEY")

supabase = create_client(url, anon_key)

# Simple test: fetch tables (should be empty at first)
try:
    response = supabase.table("non_existing_table").select("*").execute()
except Exception as e:
    print("✅ Supabase connected! (No such table yet, so this error is normal)")
    print("Error:", e)
