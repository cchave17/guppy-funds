from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://admin:admin123@localhost:27017"
    mongodb_db_name: str = "guppy_funds"
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 25

    # Claude API settings
    anthropic_api_key: str = ""
    claude_model: str = "claude-3-5-haiku-20241022"  # Fast and cheap for structured extraction

    class Config:
        env_file = ".env"


settings = Settings()
