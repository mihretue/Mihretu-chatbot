from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    supabase_jwt_secret: str
    
    # Tavily Configuration
    tavily_api_key: Optional[str] = None

    # SerpAPI Configuration (for Google Trends)
    serpapi_key: Optional[str] = None
    
    # OpenAI Configuration (optional, for backward compatibility)
    openai_api_key: Optional[str] = None
    
    # Groq Configuration (free AI API)
    groq_api_key: Optional[str] = None
    
    # Backend Configuration
    environment: str = "production"
    log_level: str = "INFO"
    debug: bool = False
    
    # MCP Configuration (not used - trends data is mocked)
    mcp_url: str = "http://mcp:5000"
    mcp_timeout: int = 10
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://frontend:3000","http://localhost:3001"]
    
    # Agent Configuration
    agent_max_iterations: int = 10
    agent_timeout: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
