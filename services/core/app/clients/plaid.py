# services/core/app/clients/plaid.py
from functools import lru_cache
from plaid import Configuration, ApiClient, Environment
from plaid.api import plaid_api
from app.config import settings

_HOSTS = {
    "sandbox": Environment.Sandbox,
    "production": Environment.Production,
}


@lru_cache
def plaid_client() -> plaid_api.PlaidApi:
    config = Configuration(
        host=_HOSTS[settings.plaid_env],
        api_key={
            "clientId": settings.plaid_client_id,
            "secret": settings.plaid_secret,
        },
    )
    return plaid_api.PlaidApi(ApiClient(config))