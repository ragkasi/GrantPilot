import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

_DEV_JWT_SECRET = "dev-only-secret-change-in-production"


class Settings(BaseSettings):
    app_name: str = "GrantPilot API"
    debug: bool = False
    max_upload_size_mb: int = 20

    # CORS — comma-separated list of allowed frontend origins.
    # In production set ALLOWED_ORIGINS=https://yourdomain.com
    # Multiple: ALLOWED_ORIGINS=https://app.example.com,https://www.example.com
    allowed_origins: str = "http://localhost:3000"

    # Database — defaults to SQLite for local dev; override for Postgres in prod
    database_url: str = ""

    # Storage — relative to backend working directory
    upload_dir: str = "uploads"

    # Auth — set JWT_SECRET to a strong random value in production
    jwt_secret: str = _DEV_JWT_SECRET
    jwt_expire_days: int = 7

    # AI APIs
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Production flag — when True the entrypoint runs alembic before startup
    # so the lifespan skips create_all_tables().
    run_migrations: bool = False

    # Rate limiting — disable in test environments to avoid cross-test interference
    rate_limit_enabled: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    def get_allowed_origins(self) -> list[str]:
        """Parse comma-separated allowed origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    def warn_if_dev_secrets(self) -> None:
        if self.jwt_secret == _DEV_JWT_SECRET and not self.debug:
            logger.warning(
                "JWT_SECRET is set to the development default. "
                "Set a strong random value before deploying to production."
            )


settings = Settings()
