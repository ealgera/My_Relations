from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    DATABASE_URL: str = Field(default="sqlite:///./my_relations_app.db")
    TESTING: bool = Field(default=False)
    DEBUG: bool = Field(default=False)
    SECRET_KEY: Optional[str] = Field(default=None)
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None)
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None)
    OAUTHLIB_INSECURE_TRANSPORT: bool = Field(default=False)
    PORT: int = Field(default=8000)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.SECRET_KEY is None:
            import secrets
            self.SECRET_KEY = secrets.token_urlsafe(32)

@lru_cache()
def get_settings():
    return Settings()