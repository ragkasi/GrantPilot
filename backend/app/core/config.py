from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "GrantPilot API"
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:3000"]
    max_upload_size_mb: int = 20
    # Populated via .env in Phase 3 when real services are wired in
    anthropic_api_key: str = ""
    openai_api_key: str = ""       # Optional: enables OpenAI embeddings over TF-IDF fallback
    database_url: str = ""
    upload_dir: str = "uploads"    # Relative to backend working directory
    # Auth — set JWT_SECRET to a strong random string in production
    jwt_secret: str = "dev-only-secret-change-in-production"
    jwt_expire_days: int = 7

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
