"""
Simple configuration management
"""

import json
from pathlib import Path
from typing import Any, Optional


class Config:
    """Minimal configuration storage"""
    
    def __init__(self):
        self._config_dir = Path.home() / ".rivavoice"
        self._config_file = self._config_dir / "config.json"
        self._data = {}
        self._load()
    
    def _load(self):
        """Load configuration from file"""
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}
    
    def save(self):
        """Save configuration to file"""
        self._config_dir.mkdir(exist_ok=True)
        with open(self._config_file, 'w') as f:
            json.dump(self._data, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self._data[key] = value