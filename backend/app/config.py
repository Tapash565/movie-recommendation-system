import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""

    # Core
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # Firebase
    FIREBASE_SERVICE_ACCOUNT_PATH: str = ""
    GOOGLE_CLOUD_PROJECT: str = ""

    # Server
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # HuggingFace
    HUGGINGFACEHUB_API_TOKEN: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT == "staging"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_test(self) -> bool:
        return self.ENVIRONMENT == "test"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        """Pydantic settings configuration."""
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"

    @classmethod
    def settings_custom_init(cls, environment: str):
        """Create settings with custom environment file loading."""
        # Set environment before loading
        import os
        os.environ["ENVIRONMENT"] = environment
        # Load the appropriate .env file
        env_file = f".env.{environment}"
        if os.path.exists(env_file):
            from dotenv import load_dotenv
            load_dotenv(env_file)
        return cls()


def _load_environment_file():
    """Load the appropriate .env file based on ENVIRONMENT variable."""
    # Get environment from os.getenv to avoid circular import
    env = os.getenv("ENVIRONMENT", "development")
    env_file = f".env.{env}"

    if os.path.exists(env_file):
        from dotenv import load_dotenv
        load_dotenv(env_file)
        return True
    elif os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv(".env")
        return True
    return False


# Load environment on module import
_load_environment_file()


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
