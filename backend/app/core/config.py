from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "GrantPilot API"
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:3000"]
    max_upload_size_mb: int = 20
    # Populated via .env in Phase 3 when real services are wired in
    anthropic_api_key: str = ""
    database_url: str = ""
    upload_dir: str = "uploads"  # Relative to backend working directory

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
