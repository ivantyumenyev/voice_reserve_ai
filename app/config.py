import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from functools import lru_cache


# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings."""
    
    # API Keys
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    retell_api_key: str = os.getenv("RETELL_API_KEY", "")
    google_credentials_path: str = os.getenv(
        "GOOGLE_CREDENTIALS_PATH",
        "./google_credentials.json"
    )
    
    # Application settings
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # Restaurant settings
    restaurant_name: str = "Pizza Palace"
    restaurant_phone: str = "+1234567890"
    max_party_size: int = 8
    opening_hour: int = 11
    closing_hour: int = 22
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 