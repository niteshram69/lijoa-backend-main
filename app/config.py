from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Environment settings
    APP_ENV: str = Field(default="local")
    
    # Database settings
    POSTGRES_USER: str = "lijoa"
    POSTGRES_PASSWORD: str = "lijoa"
    POSTGRES_DB: str = "lijoa"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: str = "5432"
    
    # Redis settings (for rate limiting)
    REDIS_URL: str = "redis://redis:6379/0"
    
    # API key encryption secret
    API_KEY_ENC_SECRET: str = Field(default="")
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components"""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

# Create settings instance that reads from environment variables
settings = Settings()