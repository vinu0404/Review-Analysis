"""
Configuration settings loaded from environment variables
"""

from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "feedback_db"
    openai_api_key: str = ""
    admin_password: str = "admin123"
    frontend_url: str = "http://localhost:8000"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    llm_model: str = "gpt-4o-mini"
    llm_timeout: int = 30
    session_expire_hours: int = 24
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
