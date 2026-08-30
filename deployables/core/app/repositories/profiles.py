"""Data access for the `profiles` table.

The ONLY layer that knows this database speaks PostgREST. Swapping Supabase
for something else means rewriting files in this package and nothing above it.
"""
from shared.db.client import DBClient, Role


async def get_for_caller(db: DBClient, *, access_token: str) -> dict | None:
    """Runs as the user, so RLS restricts the read to their own row."""
    rows = await db.select(
        "profiles",
        params={"select": "*", "limit": "1"},
        role=Role.USER,
        access_token=access_token,
    )
    return rows[0] if rows else None