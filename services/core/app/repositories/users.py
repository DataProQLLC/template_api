# services/core_api/app/repositories/users.py
from supabase import Client

def username_taken(db: Client, username: str) -> bool:
    r = db.table("profiles").select("id").eq("username", username).limit(1).execute()
    return bool(r.data)

def get_profile(db: Client, user_id: str) -> dict | None:
    r = db.table("profiles").select("*").eq("user_id", user_id).limit(1).execute()
    return r.data[0] if r.data else None