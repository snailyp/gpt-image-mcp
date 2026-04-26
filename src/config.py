"""Configuration management with multi-layer priority loading."""
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Type
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.openai.com/v1")
    default_model: str = Field(default="gpt-image-2")
    timeout: int = Field(default=60)


class ImageConfig(BaseModel):
    """Image generation configuration."""
    default_quality: str = Field(default="auto")
    default_output_format: str = Field(default="url")
    save_directory: str = Field(default="./images")
    download_retry: int = Field(default=3)
    auto_upload_to_cloudflare: bool = Field(default=True)


class CloudflareConfig(BaseModel):
    """Cloudflare Images configuration."""
    auth_code: str = Field(default="")
    api_url: str = Field(default="")
    upload_folder: str = Field(default="")


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


class JsonConfigSource(PydanticBaseSettingsSource):
    """Custom settings source for loading from JSON file."""

    def __init__(self, settings_cls: Type[BaseSettings], json_file: Optional[str] = None):
        super().__init__(settings_cls)
        self.json_file = json_file
        self._data: Dict[str, Any] = {}
        if json_file and Path(json_file).exists():
            with open(json_file, 'r') as f:
                self._data = json.load(f)

    def get_field_value(self, field_name: str, field_info: Any) -> Tuple[Any, str, bool]:
        """Get field value from JSON data."""
        _ = field_info  # Unused but required by interface
        if field_name in self._data:
            return self._data[field_name], field_name, False
        return None, field_name, False

    def __call__(self) -> Dict[str, Any]:
        """Return the loaded JSON data."""
        return self._data


class Config(BaseSettings):
    """Main configuration class with multi-layer loading support."""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_nested_delimiter='__',
        case_sensitive=False,
        extra='ignore'
    )

    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    image: ImageConfig = Field(default_factory=ImageConfig)
    cloudflare: CloudflareConfig = Field(default_factory=CloudflareConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    http: HTTPConfig = Field(default_factory=HTTPConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """
        Customize settings sources priority.
        Priority order: init_settings (CLI args) > env_settings > dotenv_settings (.env) > json_file > defaults
        """
        json_file = getattr(settings_cls, '_json_config_file', None)
        json_source = JsonConfigSource(settings_cls, json_file)

        # Return sources in priority order (first = highest priority)
        return (init_settings, env_settings, dotenv_settings, json_source, file_secret_settings)


def load_config(
    config_file: Optional[str] = None,
    cli_args: Optional[dict] = None
) -> Config:
    """
    Load configuration with priority: CLI args > env vars > config file > defaults.

    Environment variables use double underscore (__) as delimiter for nested fields:
    - OPENAI__API_KEY maps to openai.api_key
    - HTTP__PORT maps to http.port
    - LOGGING__LEVEL maps to logging.level

    Args:
        config_file: Path to JSON configuration file
        cli_args: Dictionary of CLI arguments to override config (e.g., {"openai.api_key": "value"})

    Returns:
        Config: Loaded configuration instance

    Raises:
        ValueError: If type conversion fails for environment variables or CLI args
    """
    # Set the JSON config file path as a class attribute for the custom source
    Config._json_config_file = config_file

    # Prepare init_kwargs for CLI args
    init_kwargs = {}
    if cli_args:
        # Convert dot-notation CLI args to nested dict structure
        for key, value in cli_args.items():
            if '.' in key:
                section, field = key.split('.', 1)
                if section not in init_kwargs:
                    init_kwargs[section] = {}
                # Type conversion will be handled by pydantic
                init_kwargs[section][field] = value
            else:
                init_kwargs[key] = value

    # Create config with proper priority: CLI args > env vars > file > defaults
    try:
        config = Config(**init_kwargs)
    except (ValueError, ValidationError) as e:
        raise ValueError(f"Configuration error: {e}") from e
    finally:
        # Clean up the class attribute
        if hasattr(Config, '_json_config_file'):
            delattr(Config, '_json_config_file')

    return config
