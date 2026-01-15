import os
import yaml
from pathlib import Path
from typing import Any, Dict
import re

class Config:
    """Configuration loader with environment variable substitution"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._raw_config = self._load_yaml()
        self.config = self._substitute_env_vars(self._raw_config)

    def _load_yaml(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        with open(self.config_path) as f:
            return yaml.safe_load(f)

    def _substitute_env_vars(self, config: Any) -> Any:
        """Recursively substitute ${VAR} with os.environ['VAR']"""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(v) for v in config]
        elif isinstance(config, str):
            # Match ${VAR_NAME}
            pattern = r'\$\{([A-Z_]+)\}'
            def replace(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            return re.sub(pattern, replace, config)
        return config

    def get(self, key_path: str, default=None):
        """
        Get nested config value using dot notation.

        Example: config.get('github.token')
        """
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default
