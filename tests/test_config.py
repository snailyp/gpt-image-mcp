import os
import json
import tempfile
from pathlib import Path
import pytest
from src.config import Config, load_config


def test_load_config_from_env():
    os.environ["OPENAI_API_KEY"] = "test-key"
    os.environ["LOG_LEVEL"] = "DEBUG"

    config = load_config()

    assert config.openai.api_key == "test-key"
    assert config.logging.level == "DEBUG"

    # Cleanup
    del os.environ["OPENAI_API_KEY"]
    del os.environ["LOG_LEVEL"]


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

    os.environ["OPENAI_API_KEY"] = "env-key"

    try:
        config = load_config(config_file=config_file)
        assert config.openai.api_key == "env-key"
    finally:
        os.unlink(config_file)
        del os.environ["OPENAI_API_KEY"]
