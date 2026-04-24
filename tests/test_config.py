import os
import json
import tempfile
from pathlib import Path
import pytest
from src.config import Config, load_config


def test_load_config_from_env():
    os.environ["OPENAI__API_KEY"] = "test-key"
    os.environ["LOGGING__LEVEL"] = "DEBUG"

    config = load_config()

    assert config.openai.api_key == "test-key"
    assert config.logging.level == "DEBUG"

    # Cleanup
    del os.environ["OPENAI__API_KEY"]
    del os.environ["LOGGING__LEVEL"]


def test_load_config_from_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "openai": {"api_key": "file-key", "default_model": "gpt-4-turbo"},
            "image": {"default_size": "512x512"}
        }, f)
        config_file = f.name

    try:
        config = load_config(config_file=config_file)
        assert config.openai.api_key == "file-key"
        assert config.openai.default_model == "gpt-4-turbo"
        assert config.image.default_size == "512x512"
    finally:
        os.unlink(config_file)


def test_config_priority_env_over_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"openai": {"api_key": "file-key"}}, f)
        config_file = f.name

    os.environ["OPENAI__API_KEY"] = "env-key"

    try:
        config = load_config(config_file=config_file)
        assert config.openai.api_key == "env-key"
    finally:
        os.unlink(config_file)
        del os.environ["OPENAI__API_KEY"]


def test_load_config_with_cli_args():
    """Test CLI arguments override env vars and file config."""
    config = load_config(cli_args={
        "openai.api_key": "cli-key",
        "openai.default_model": "gpt-4-turbo",
        "http.port": 9000
    })

    assert config.openai.api_key == "cli-key"
    assert config.openai.default_model == "gpt-4-turbo"
    assert config.http.port == 9000


def test_cli_args_override_env():
    """Test CLI args have highest priority over env vars."""
    os.environ["OPENAI__API_KEY"] = "env-key"

    try:
        config = load_config(cli_args={"openai.api_key": "cli-key"})
        assert config.openai.api_key == "cli-key"
    finally:
        del os.environ["OPENAI__API_KEY"]


def test_cli_args_type_conversion():
    """Test CLI args are properly type-converted."""
    config = load_config(cli_args={
        "http.port": "8080",  # String should be converted to int
        "openai.timeout": "120"
    })

    assert config.http.port == 8080
    assert isinstance(config.http.port, int)
    assert config.openai.timeout == 120
    assert isinstance(config.openai.timeout, int)


def test_cli_args_invalid_type():
    """Test error handling for invalid type conversions."""
    with pytest.raises(ValueError, match="Configuration error"):
        load_config(cli_args={"http.port": "not-a-number"})


def test_comprehensive_env_vars():
    """Test that all config fields can be set via environment variables."""
    os.environ["OPENAI__BASE_URL"] = "https://custom.api.com"
    os.environ["OPENAI__DEFAULT_MODEL"] = "gpt-4-turbo"
    os.environ["OPENAI__TIMEOUT"] = "90"
    os.environ["IMAGE__DEFAULT_SIZE"] = "512x512"
    os.environ["IMAGE__DEFAULT_QUALITY"] = "hd"
    os.environ["SERVER__TRANSPORT"] = "http"
    os.environ["HTTP__PORT"] = "9000"

    try:
        config = load_config()
        assert config.openai.base_url == "https://custom.api.com"
        assert config.openai.default_model == "gpt-4-turbo"
        assert config.openai.timeout == 90
        assert config.image.default_size == "512x512"
        assert config.image.default_quality == "hd"
        assert config.server.transport == "http"
        assert config.http.port == 9000
    finally:
        for key in ["OPENAI__BASE_URL", "OPENAI__DEFAULT_MODEL", "OPENAI__TIMEOUT",
                    "IMAGE__DEFAULT_SIZE", "IMAGE__DEFAULT_QUALITY",
                    "SERVER__TRANSPORT", "HTTP__PORT"]:
            if key in os.environ:
                del os.environ[key]


def test_env_var_type_conversion_error():
    """Test error handling for invalid env var type conversion."""
    os.environ["HTTP__PORT"] = "invalid-port"

    try:
        with pytest.raises(ValueError):
            load_config()
    finally:
        del os.environ["HTTP__PORT"]
