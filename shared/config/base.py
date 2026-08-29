# shared/ultra_shared/config/base.py
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    env: Literal["dev", "stage", "prod"] = "dev"
    port: int = 8080
    log_level: str = "INFO"

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"