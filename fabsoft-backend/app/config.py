from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # --- Required Settings ---
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # --- Vercel Blob Storage ---
    BLOB_READ_WRITE_TOKEN: str

    # This will read the .env file and ignore any extra variables
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()