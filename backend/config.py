import json
import logging
from typing import Dict, Any
from backend.path_manager import PathManager

class ConfigManager:
    """
    Central Configuration Manager for KaRar platform.
    Loads settings.json using PathManager and provides structured configuration access.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        self.path_manager = PathManager()
        self.logger = logging.getLogger('KaRar')
        self.config_path = self.path_manager.get_path('config', 'settings.json')
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._settings = json.load(f)
            self.logger.info(f"Configuration loaded successfully from {self.path_manager.get_relative_path(self.config_path)}")
        except Exception as e:
            self.logger.error(f"Failed to load settings.json: {str(e)}")
            # Fallback defaults in case settings.json is missing or corrupted
            self._settings = {
                "project": {"name": "KaRar Fallback", "version": "0.2", "scale_ratio": 32.0, "default_wall_height": 3.0},
                "tolerances": {"snapping_distance_mm": 5.0, "collinear_angle_threshold_deg": 2.5, "t_junction_threshold_mm": 20.0},
                "layers": {"walls": ["duvar"], "columns": ["kolon"], "doors": ["kapı"], "windows": ["k pencere"], "axes": ["aks"]}
            }

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Retrieves a nested configuration value using dot notation (e.g. 'tolerances.snapping_distance_mm')
        """
        keys = key_path.split('.')
        val = self._settings
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def get_layer_mapping(self, category: str) -> list:
        """Retrieves mapped CAD layer names for a given category (walls, columns, doors, etc.)"""
        return self.get(f"layers.{category}", [])

    def reload(self):
        """Forces a re-read of settings.json from disk."""
        self._load_config()
