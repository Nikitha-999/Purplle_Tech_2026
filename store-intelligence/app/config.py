from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./var/store_intelligence.db"
    store_layout_path: str = "data/layouts/store_layout.json"
    pos_csv_path: str = "data/transactions/brigade_pos.csv"
    log_level: str = "INFO"
    stale_feed_minutes: int = 10

    @property
    def layout_path(self) -> Path:
        return Path(self.store_layout_path)

    @property
    def db_path(self) -> Path | None:
        if self.database_url.startswith("sqlite:///"):
            raw = self.database_url.replace("sqlite:///", "", 1)
            if raw.startswith("/") or (len(raw) > 1 and raw[1] == ":"):
                return Path(raw)
            return Path(raw)
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
