"""
Configuration management for Todo API
Handles environment variables and application settings
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Security Configuration
    secret_key: str = "fallback-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database Configuration
    database_url: str = "sqlite:///./todos.db"
    
    # Application Configuration
    debug: bool = True
    environment: str = "development"
    api_title: str = "Todo API"
    api_version: str = "1.0.0"
    api_description: str = "A secure Todo API with JWT authentication"
    
    # Security Settings
    min_password_length: int = 8
    max_login_attempts: int = 5
    rate_limit_per_minute: int = 60
    
    # CORS Settings
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:8000"]
    cors_allow_credentials: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def is_production() -> bool:
    """Check if running in production environment"""
    return settings.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment"""
    return settings.environment.lower() == "development"


# Validation functions
def validate_secret_key() -> None:
    """Validate that secret key is secure enough for production"""
    if is_production():
        if len(settings.secret_key) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters in production")
        
        if settings.secret_key in [
            "your-super-secret-key-change-this-in-production-minimum-32-characters",
            "dev-key-change-in-production-abc123def456ghi789jkl012mno345pqr",
            "fallback-secret-key-change-in-production"
        ]:
            raise ValueError("Must change default SECRET_KEY in production")


def validate_settings() -> None:
    """Validate all settings for security and correctness"""
    validate_secret_key()
    
    if settings.min_password_length < 6:
        raise ValueError("MIN_PASSWORD_LENGTH should be at least 6 characters")
    
    if settings.access_token_expire_minutes < 1:
        raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
    
    print(f"✅ Configuration loaded for {settings.environment} environment")
    if is_development():
        print(f"🔧 Debug mode: {settings.debug}")
        print(f"🔑 Secret key length: {len(settings.secret_key)} characters")
        print(f"🗄️ Database: {settings.database_url}")