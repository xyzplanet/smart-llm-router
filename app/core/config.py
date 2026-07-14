import os

class Settings:
    PROJECT_NAME: str = "Smart LLM Router Gateway"
    
    # Local LLM Configuration (Defaulted to a standard Ollama setup)
    LOCAL_URL: str = os.getenv("LOCAL_URL", "http://127.0.0.1:11434")
    LOCAL_MODEL: str = os.getenv("LOCAL_MODEL", "deepseek-r1:8b")
    
    # Default target configurations for Module 1 (Fully routing to local model for testing)
    DEFAULT_TARGET_URL: str = LOCAL_URL
    DEFAULT_MODEL: str = LOCAL_MODEL

settings = Settings()

