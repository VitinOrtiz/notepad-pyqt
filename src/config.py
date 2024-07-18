__all__ = ['readConfig', 'config']
__version__ = '0.1'
__author__ = 'Victor M. Ortiz <Victor.M.Ortiz@outlook.com>'

import json
from typing import Any 
from .logger import showError, logger

# Configuration
try:
    config_file = 'config/app.json'
    with open(config_file, 'r', encoding='utf-8') as app_config:
        config = json.load(app_config)
except FileNotFoundError as e:
    showError(f"File {config_file} not found. {e}")
except PermissionError as e:
    showError(f"Permission denied to open {config_file}. {e}")
except UnicodeDecodeError as e:
    showError(f"File encoding error while reading file {config_file}. {e}")
except Exception as e:
    showError(f"Error parsing JSON file {config_file}. {e}")

def readConfig(key) -> Any:
    try:
        value = config[key]
    except KeyError:
        logger.warn(f"Configuration key {key} is missing in config {config_file}")
        return None
    else:
        return value