"""
Configuration management for Analytics Engine
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/analytics")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # ClickHouse (optional)
    clickhouse_url: str = os.getenv("CLICKHOUSE_URL", "")
    
    # Application
    app_name: str = "Analytics Engine"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Integration
    global_state_manager_url: str = os.getenv("GLOBAL_STATE_MANAGER_URL", "http://localhost:8035")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
