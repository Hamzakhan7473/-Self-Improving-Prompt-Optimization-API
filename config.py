"""Configuration management for the Prompt Optimization API."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    
    # Database
    database_url: str = "sqlite:///./prompt_optimizer.db"
    
    # LLM Providers
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Default LLM Provider
    default_llm_provider: str = "openai"
    default_model: str = "gpt-4-turbo-preview"
    
    # Evaluation Settings
    evaluation_llm_provider: str = "openai"
    evaluation_model: str = "gpt-4-turbo-preview"
    evaluation_temperature: float = 0.0
    evaluation_max_tokens: int = 1000
    
    # Self-Improvement Settings
    min_improvement_threshold: float = 0.05
    min_absolute_score: float = 0.7
    regression_threshold: float = 0.02
    critical_case_pass_rate: float = 0.95
    format_pass_rate: float = 0.98
    max_candidates_per_iteration: int = 5
    
    # Caching
    enable_cache: bool = True
    cache_ttl_seconds: int = 3600
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()



