"""Configuration management using Pydantic settings."""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", case_sensitive=False)

    # E*TRADE OAuth - Sandbox
    etrade_consumer_key_sandbox: str = ""
    etrade_consumer_secret_sandbox: str = ""

    # E*TRADE OAuth - Production
    etrade_consumer_key_prod: str = ""
    etrade_consumer_secret_prod: str = ""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True

    # Sandbox Mode
    etrade_sandbox: bool = True

    # MCP Configuration
    mcp_enabled: bool = True
    mcp_transport: str = "stdio"
    mcp_port: int = 3000

    # Logging
    log_level: str = "INFO"

    @property
    def consumer_key(self) -> str:
        """Get appropriate consumer key based on sandbox mode."""
        if self.etrade_sandbox:
            return self.etrade_consumer_key_sandbox
        return self.etrade_consumer_key_prod

    @property
    def consumer_secret(self) -> str:
        """Get appropriate consumer secret based on sandbox mode."""
        if self.etrade_sandbox:
            return self.etrade_consumer_secret_sandbox
        return self.etrade_consumer_secret_prod

    @property
    def etrade_base_url(self) -> str:
        """Get E*TRADE base URL based on sandbox mode."""
        if self.etrade_sandbox:
            return "https://apisb.etrade.com/v1"
        return "https://api.etrade.com/v1"


# Global settings instance
settings = Settings()
