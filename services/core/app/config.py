# services/core_api/app/config.py
from pathlib import Path
from pydantic_settings import SettingsConfigDict
from shared.config.base import BaseAppSettings

_env_file = next(
    (p / "secrets" / ".env.core"
     for p in Path(__file__).resolve().parents
     if (p / "secrets" / ".env.core").is_file()),
    None,
)

class Settings(BaseAppSettings):
    model_config = SettingsConfigDict(env_file=_env_file, extra="ignore")

    supabase_url: str
    supabase_secret_key: str
    supabase_publishable_key: str
    # plaid_client_id: str
    # plaid_secret: str
    # plaid_env: str = "sandbox"
    # starting_balance_cents: int = 100_000

settings = Settings()