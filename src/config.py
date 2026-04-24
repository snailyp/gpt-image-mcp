"""Configuration management with multi-layer priority loading."""
import os
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.openai.com/v1")
    default_model: str = Field(default="gpt-4o")
    timeout: int = Field(default=60)


class ImageConfig(BaseModel):
    """Image generation configuration."""
    default_size: str = Field(default="1024x1024")
    default_quality: str = Field(default="standard")
    default_output_format: str = Field(default="url")
    save_directory: str = Field(default="./images")
    download_retry: int = Field(default=3)


class ServerConfig(BaseModel):
    """MCP server configuration."""
    name: str = Field(default="gpt-image-mcp")
    version: str = Field(default="1.0.0")
    transport: str = Field(default="stdio")


class HTTPConfig(BaseModel):
    """HTTP server configuration."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    endpoint: str = Field(default="/mcp")


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class Config(BaseSettings):
    """Main configuration class with multi-layer loading support."""
    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore'
    )

    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    http: HTTPConfig = Field(default_factory=HTTPConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(
    config_file: Optional[str] = None,
    cli_args: Optional[dict] = None
) -> Config:
    """
    Load configuration with priority: CLI args > env vars > config file > defaults.

    Args:
        config_file: Path to JSON configuration file
        cli_args: Dictionary of CLI arguments to override config

    Returns:
        Config: Loaded configuration instance
    """
    config_data = {}

    # Step 1: Load from config file if provided
    if config_file and Path(config_file).exists():
        with open(config_file, 'r') as f:
            config_data = json.load(f)

    # Step 2: Create base config from file data
    config = Config(**config_data)

    # Step 3: Override with environment variables
    # Handle OPENAI_API_KEY
    if "OPENAI_API_KEY" in os.environ:
        config.openai.api_key = os.environ["OPENAI_API_KEY"]

    # Handle LOG_LEVEL
    if "LOG_LEVEL" in os.environ:
        config.logging.level = os.environ["LOG_LEVEL"]

    # Handle OPENAI_BASE_URL
    if "OPENAI_BASE_URL" in os.environ:
        config.openai.base_url = os.environ["OPENAI_BASE_URL"]

    # Handle MCP_TRANSPORT
    if "MCP_TRANSPORT" in os.environ:
        config.server.transport = os.environ["MCP_TRANSPORT"]

    # Handle MCP_HTTP_PORT
    if "MCP_HTTP_PORT" in os.environ:
        config.http.port = int(os.environ["MCP_HTTP_PORT"])

    # Step 4: Override with CLI args if provided
    if cli_args:
        for key, value in cli_args.items():
            if '.' in key:
                section, field = key.split('.', 1)
                if hasattr(config, section):
                    section_obj = getattr(config, section)
                    if hasattr(section_obj, field):
                        setattr(section_obj, field, value)
            elif hasattr(config, key):
                setattr(config, key, value)

    return config
