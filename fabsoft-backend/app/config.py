from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # --- Required Settings ---
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # --- Optional Mail Settings ---
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_port: Optional[int] = None
    mail_server: Optional[str] = None
    mail_starttls: Optional[bool] = None
    mail_ssl_tls: Optional[bool] = None

    # This will read the .env file and ignore any extra variables
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()