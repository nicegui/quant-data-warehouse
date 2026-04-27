"""Centralized configuration using Pydantic Settings + YAML overrides."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    db: str = Field(default="quantdb", validation_alias="POSTGRES_DB")
    user: str = Field(default="quant", validation_alias="POSTGRES_USER")
    password: str = Field(default="quant_pass", validation_alias="POSTGRES_PASSWORD")

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @property
    def dsn_async(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class TushareSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    token: str = Field(default="", validation_alias="TUSHARE_TOKEN")

    @field_validator("token")
    @classmethod
    def token_required(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "TUSHARE_TOKEN is empty. Set it in .env or export it."
            )
        return v


class CryptoSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    exchanges: list[str] = ["okx"]
    okx_api_key: str = Field(default="", validation_alias="OKX_API_KEY")
    okx_api_secret: str = Field(default="", validation_alias="OKX_API_SECRET")
    okx_passphrase: str = Field(default="", validation_alias="OKX_PASSPHRASE")


class LogSettings(BaseSettings):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", validation_alias="LOG_LEVEL"
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    db: DatabaseSettings = DatabaseSettings()
    tushare: TushareSettings = TushareSettings()
    crypto: CryptoSettings = CryptoSettings()
    log: LogSettings = LogSettings()

    timezone: str = Field(default="Asia/Shanghai", validation_alias="TIMEZONE")
    data_dir: Path = Field(default=Path("./data"), validation_alias="DATA_DIR")

    def load_source_config(self, name: str) -> dict:
        """Load YAML config for a specific data source."""
        config_path = Path(__file__).parent / "sources" / f"{name}.yaml"
        if not config_path.exists():
            return {}
        with open(config_path) as f:
            return yaml.safe_load(f) or {}

    def dump(self) -> dict:
        """Serializable config snapshot for logging."""
        return {
            "db": self.db.model_dump(),
            "log_level": self.log.level,
            "timezone": self.timezone,
            "data_dir": str(self.data_dir),
        }


settings = Settings()
