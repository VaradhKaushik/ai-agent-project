import yaml
import os
from dotenv import load_dotenv
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"
ENV_PATH = CONFIG_DIR / ".env"

_config = None

def load_configuration(config_path: Path = DEFAULT_CONFIG_PATH, env_path: Path = ENV_PATH) -> dict:
    """Loads configuration from YAML and .env file."""
    global _config
    if _config is not None:
        return _config

    # Load .env file first
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        print(f"Warning: .env file not found at {env_path}. Some configurations (like API keys) might be missing.")

    # Load YAML config
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at {config_path}")

    with open(config_path, 'r') as f:
        cfg = yaml.safe_load(f)

    # Override/add with environment variables (e.g., for API keys)
    # Example: if you have WEATHER_API_KEY in .env, it can be accessed here
    if 'tools' not in cfg:
        cfg['tools'] = {}
    cfg['tools']['weather_api_key'] = os.getenv('WEATHER_API_KEY')

    _config = cfg
    return _config

def get_config() -> dict:
    """Returns the loaded configuration."""
    if _config is None:
        return load_configuration()
    return _config

if __name__ == '__main__':
    # Test loading config
    config = get_config()
    print("Successfully loaded configuration:")
    import json
    print(json.dumps(config, indent=2)) 