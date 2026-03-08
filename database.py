import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
service_role_key: str = os.getenv("SERVICE_ROLE_KEY")

if not url or not key:
    print("Warning: SUPABASE_URL or SUPABASE_KEY not found in environment variables.")

# Standard client for user-level operations (obeying RLS)
supabase: Client = create_client(url, key) if url and key else None

# Admin client for operations that bypass RLS (if needed)
supabase_admin: Client = create_client(url, service_role_key) if url and service_role_key else None
