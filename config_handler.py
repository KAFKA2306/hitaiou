import json
from pathlib import Path

def load_config(config_path: str = 'config.json') -> dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        # Create default config file if it doesn't exist
        default_config = {
            "api_key": "YOUR-API-KEY",
            "spreadsheet_id": "1k133iin4Fu4SHqSY7qSs9CVWFPAF0PW_F30GBFWIqRg"
        }
        Path(config_path).write_text(json.dumps(default_config, indent=2, ensure_ascii=False))
        print(f"Created default config file at {config_path}")
        print("Please update the API key in the config file")
        return default_config
    except json.JSONDecodeError:
        print(f"Error: {config_path} is not a valid JSON file")
        raise