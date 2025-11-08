"""Configuration settings for the diamond painting backend."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DEFAULT_GRID_W: int = 100
    DEFAULT_GRID_H: int = 140
    MAX_UPLOAD_MB: int = 15
    OUTPUT_DPI: int = 300
    CORS_ORIGINS: str = "http://localhost:*,http://127.0.0.1:*"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
