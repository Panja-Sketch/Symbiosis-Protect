"""Runtime configuration. Every value comes from the environment (see .env.example)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    carrier_name: str = "Symbiosis Protect"
    carrier_primary_color: str = "#0E9F9A"
    nws_user_agent: str = "SymbiosisProtectDemo/0.1 (set-NWS_USER_AGENT)"
    gemini_model: str = "gemini-2.5-flash-lite"
    google_cloud_project: str = "symbiosis-protect-demo"
    google_cloud_location: str = "us-central1"
    firestore_emulator_host: str | None = None
    storage_backend: str = "local"
    local_storage_dir: str = ".local/storage"
    auth_mode: str = "demo"
    session_secret: str = "dev-only-change-me"
    demo_mode: bool = True
    scheduler_enabled: bool = True
    scheduler_minutes: int = 15
    ai_asks_per_hour: int = 30
    max_proof_bytes: int = 8_000_000
    gcs_bucket: str | None = None
    internal_auth: str = "token"  # token (local) | oidc (Cloud Scheduler ID token)
    scheduler_audience: str | None = None  # API URL the Scheduler token is minted for
    scheduler_service_account: str | None = None  # only this identity may call /internal/evaluate
    ai_enabled: bool = False  # true only where Vertex AI service-account credentials exist


@lru_cache
def get_settings() -> Settings:
    return Settings()
