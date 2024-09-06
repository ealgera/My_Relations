from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

class Settings(BaseSettings):
    DATABASE_URL        : str           = Field(default="sqlite:///./my_relations_app.db")
    SECRET_KEY          : Optional[str] = Field(default=None)
    GOOGLE_CLIENT_ID    : Optional[str] = Field(default=None)
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None)
    OAUTHLIB_INSECURE_TRANSPORT: bool   = Field(default=False)
    PORT                : int           = Field(default=8000)
    DEVELOPMENT         : bool          = Field(default=True) # True is value 1.
    FOTO_DIR            : str           = Field(default=str(PROJECT_ROOT / "data" / "fotos"))

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.SECRET_KEY is None:
            import secrets
            self.SECRET_KEY = secrets.token_urlsafe(32)
        
        # Convert FOTO_DIR to Path and ensure it exists
        self.FOTO_DIR = Path(self.FOTO_DIR)
        self.FOTO_DIR.mkdir(parents=True, exist_ok=True)

@lru_cache()
def get_settings():
    return Settings()