from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

Env = Literal["local", "dev", "stage", "prod"]

# Environments offered in the docs "Servers" dropdown.
# prod is deliberately EXCLUDED: docs never render in prod anyway, and
# listing it lets someone on the dev docs page fire a live request at
# production data with whatever token is in Authorize.
DOC_ENVS: tuple[Env, ...] = ("local", "dev", "stage")


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    env: Env = "dev"
    app_name: str = "template"
    port: int = 8080
    log_level: str = "INFO"

    # Escape hatch: overrides the derived hostname entirely (raw *.run.app
    # URL, PR preview environment, custom domain).
    api_host: str | None = None

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

    def base_url_for(self, env: str) -> str:
        """Prod has no env label; everything else is a subdomain."""
        if env == "prod":
            return f"https://api.{self.app_name}.com"
        return f"https://api.{env}.{self.app_name}.com"

    @property
    def public_base_url(self) -> str:
        if self.api_host:
            return self.api_host.rstrip("/")
        return self.base_url_for(self.env)

    def doc_servers(self, path_prefix: str = "") -> list[dict[str, str]]:
        """Servers dropdown: current environment first, then other non-prod
        environments. Never includes prod."""
        seen: set[str] = set()
        out: list[dict[str, str]] = []

        def add(url: str, label: str) -> None:
            url = url.rstrip("/") + path_prefix
            if url not in seen:
                seen.add(url)
                out.append({"url": url, "description": label})

        add(self.public_base_url, f"{self.env} (current)")
        for e in DOC_ENVS:
            if e != self.env:
                add(self.base_url_for(e), e)
        return out