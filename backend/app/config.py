from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All variables from docs/ARCHITECTURE.md §3. Real env vars (Docker) override the .env file."""

    # "../.env" is the repo-root .env when running from backend/ locally
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    POSTGRES_USER: str = "soa"
    POSTGRES_PASSWORD: str = "soa_dev_pw"
    POSTGRES_DB: str = "soa"
    DATABASE_URL: str = "postgresql+psycopg://soa:soa_dev_pw@localhost:5433/soa"
    MODEL_DIR: str = "../ml/artifacts"
    DATA_DIR: str = "../data/generated"
    ML_MODE: Literal["stub", "live"] = "stub"
    SIM_TICK_SECONDS: int = 2
    CORS_ORIGINS: str = "http://localhost:5173"
    DEFAULT_OPERATOR_ID: str = "OP1001"
    VITE_API_BASE_URL: str = "http://localhost:8000/api"
    VITE_USE_MOCKS: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
