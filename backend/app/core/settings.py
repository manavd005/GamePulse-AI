"""
Modular Application Settings Management using Pydantic Settings.

Separates application configuration into logical sub-settings:
- SecuritySettings (Mandatory SECRET_KEY, algorithm)
- RiotApiSettings (API key, default region, timeouts, retry policy)
- DatabaseSettings (PostgreSQL / SQLite connection string & pool config)
- PipelineSettings (Raw & Processed data paths, dataset export format, batch sizes)
- AppSettings (Environment mode, debug, logging)

Strictly validates environment variables and raises ConfigError on missing mandatory secrets.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions import ConfigError

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
ENV_FILE = BACKEND_DIR / ".env"


class SecuritySettings(BaseSettings):
    """Security and cryptographic signing configuration."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str = Field(..., description="Mandatory application secret key for signing tokens")
    ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Token expiration duration in minutes")

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ConfigError("SECRET_KEY environment variable is missing or empty. Insecure defaults are forbidden.")
        if len(v.strip()) < 16:
            raise ConfigError("SECRET_KEY must be at least 16 characters long for cryptographic security.")
        return v.strip()


class RiotApiSettings(BaseSettings):
    """Riot Games Developer API connection and policy configuration."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    RIOT_API_KEY: str = Field(..., description="Mandatory Riot Games Developer API Key")
    RIOT_DEFAULT_REGION: str = Field(default="ap", description="Default platform routing region (e.g. ap, na, eu, kr)")
    RIOT_REQUEST_TIMEOUT: float = Field(default=10.0, description="HTTP request timeout in seconds")
    RIOT_MAX_RETRIES: int = Field(default=3, description="Max retries for rate limits & transient errors")
    RIOT_BACKOFF_FACTOR: float = Field(default=1.5, description="Exponential backoff multiplier")

    @field_validator("RIOT_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or not v.strip():
            raise ConfigError("RIOT_API_KEY environment variable is missing or empty.")
        return v.strip()


class DatabaseSettings(BaseSettings):
    """Database persistence configuration."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = Field(
        default="sqlite:///./gamepulse.db",
        description="Database connection URL (PostgreSQL in production, SQLite in dev)",
    )
    DB_POOL_SIZE: int = Field(default=5, description="SQLAlchemy connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="SQLAlchemy connection pool max overflow")


class PipelineSettings(BaseSettings):
    """Data Pipeline and Feature Extraction Configuration."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    RAW_DATA_DIR: str = Field(
        default=str(PROJECT_ROOT / "data" / "raw"),
        description="Directory storing raw JSON payloads",
    )
    PROCESSED_DATA_DIR: str = Field(
        default=str(PROJECT_ROOT / "data" / "processed"),
        description="Target directory for processed CSV & Parquet datasets",
    )
    DEFAULT_DATASET_FORMAT: str = Field(default="parquet", description="Dataset export format (csv, parquet, both)")
    BATCH_SIZE: int = Field(default=50, description="Pipeline batch processing size")
    MAX_MATCHES_PER_RUN: int = Field(default=100, description="Maximum matches per pipeline execution run")
    OVERWRITE_EXISTING: bool = Field(default=True, description="Overwrite existing dataset files")


class AppSettings(BaseSettings):
    """General application metadata and environment settings."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = Field(default="GamePulse AI", description="Application Title")
    PROJECT_VERSION: str = Field(default="1.0.0", description="Application Version")
    ENVIRONMENT: str = Field(default="development", description="Environment mode (development, staging, production)")
    LOG_LEVEL: str = Field(default="INFO", description="Global log output level (DEBUG, INFO, WARNING, ERROR)")
    DEBUG: bool = Field(default=False, description="Debug mode toggle")


class Settings:
    """
    Composite Settings Container.

    Aggregates SecuritySettings, RiotApiSettings, DatabaseSettings, PipelineSettings, and AppSettings.
    """

    def __init__(self) -> None:
        try:
            self.security = SecuritySettings()
            self.riot = RiotApiSettings()
            self.db = DatabaseSettings()
            self.pipeline = PipelineSettings()
            self.app = AppSettings()
        except ConfigError:
            raise
        except Exception as err:
            raise ConfigError(f"Failed to initialize settings configuration: {err}") from err

    @property
    def RIOT_API_KEY(self) -> str:
        return self.riot.RIOT_API_KEY

    @property
    def RIOT_DEFAULT_REGION(self) -> str:
        return self.riot.RIOT_DEFAULT_REGION

    @property
    def RIOT_REQUEST_TIMEOUT(self) -> float:
        return self.riot.RIOT_REQUEST_TIMEOUT

    @property
    def RIOT_MAX_RETRIES(self) -> int:
        return self.riot.RIOT_MAX_RETRIES

    @property
    def RIOT_BACKOFF_FACTOR(self) -> float:
        return self.riot.RIOT_BACKOFF_FACTOR

    @property
    def SECRET_KEY(self) -> str:
        return self.security.SECRET_KEY

    @property
    def ENVIRONMENT(self) -> str:
        return self.app.ENVIRONMENT

    @property
    def LOG_LEVEL(self) -> str:
        return self.app.LOG_LEVEL

    @property
    def DATABASE_URL(self) -> str:
        return self.db.DATABASE_URL


settings = Settings()


def get_settings() -> Settings:
    """FastAPI Dependency Provider for Settings."""
    return settings
