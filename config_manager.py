"""
Configuration module for lickcalc webapp.
Handles loading and validation of configuration from config.yaml
"""

import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """Manages configuration loading and access for lickcalc."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration manager.
        
        Parameters:
        -----------
        config_path : str
            Path to the configuration YAML file
        """
        self.config_path = Path(config_path)
        self._config = None
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file with error handling."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self._config = yaml.safe_load(file)
                print(f"Configuration loaded from {self.config_path}")
            else:
                print(f"Configuration file {self.config_path} not found. Using defaults.")
                self._config = self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing YAML configuration: {e}")
            print("Using default configuration.")
            self._config = self._get_default_config()
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration.")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file is not available."""
        return {
            'session': {
                'bin_size': 30,
                'fig_type': 'hist',
                'length_unit': 's'
            },
            'microstructure': {
                'interburst_interval': 0.5,
                'min_licks_per_burst': 1,
                'long_lick_threshold': 0.3
            },
            'files': {
                'default_file_type': 'med'
            },
            'ui': {
                'title': 'lickcalc',
                'debug': True,
                'hot_reload': True
            },
            'analysis': {
                'max_session_bins': 300,
                'min_session_bins': 5,
                'session_bin_step': 5,
                'max_interburst_interval': 3.0,
                'min_interburst_interval': 0.0,
                'interburst_step': 0.25,
                'max_long_lick_threshold': 1.0,
                'min_long_lick_threshold': 0.1,
                'long_lick_step': 0.1
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Parameters:
        -----------
        key_path : str
            Dot-separated path to configuration value (e.g., 'session.bin_size')
        default : Any
            Default value if key is not found
            
        Returns:
        --------
        Any : Configuration value or default
        """
        if self._config is None:
            return default
            
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            print(f"Configuration key '{key_path}' not found. Using default: {default}")
            return default
    
    def get_session_defaults(self) -> Dict[str, Any]:
        """Get all session-related default values."""
        return {
            'bin_size': self.get('session.bin_size', 30),
            'fig_type': self.get('session.fig_type', 'hist')
        }
    
    def get_microstructure_defaults(self) -> Dict[str, Any]:
        """Get all microstructure analysis default values."""
        return {
            'interburst_interval': self.get('microstructure.interburst_interval', 0.5),
            'min_licks_per_burst': self.get('microstructure.min_licks_per_burst', 1),
            'long_lick_threshold': self.get('microstructure.long_lick_threshold', 0.3)
        }
    
    def get_slider_config(self, slider_name: str) -> Dict[str, Any]:
        """
        Get complete slider configuration including min, max, step, and default value.
        
        Parameters:
        -----------
        slider_name : str
            Name of the slider ('session_bin', 'interburst', 'minlicks', 'longlick')
            
        Returns:
        --------
        Dict[str, Any] : Slider configuration dictionary
        """
        if slider_name == 'session_bin':
            return {
                'min': self.get('analysis.min_session_bins', 5),
                'max': self.get('analysis.max_session_bins', 300),
                'step': self.get('analysis.session_bin_step', 5),
                'value': self.get('session.bin_size', 30),
                'marks': {i: str(i) for i in [10, 30, 60, 120, 300]}
            }
        elif slider_name == 'interburst':
            return {
                'min': self.get('analysis.min_interburst_interval', 0),
                'max': self.get('analysis.max_interburst_interval', 3),
                'step': self.get('analysis.interburst_step', 0.25),
                'value': self.get('microstructure.interburst_interval', 0.5),
                'marks': {i: str(i) for i in [0.5, 1, 1.5, 2, 2.5, 3]}
            }
        elif slider_name == 'minlicks':
            return {
                'min': 1,
                'max': 5,
                'step': 1,
                'value': self.get('microstructure.min_licks_per_burst', 1),
                'marks': {i: str(i) for i in [1, 2, 3, 4, 5]}
            }
        elif slider_name == 'longlick':
            return {
                'min': self.get('analysis.min_long_lick_threshold', 0.1),
                'max': self.get('analysis.max_long_lick_threshold', 1.0),
                'step': self.get('analysis.long_lick_step', 0.1),
                'value': self.get('microstructure.long_lick_threshold', 0.3),
                'marks': {i: str(i) for i in [0.2, 0.4, 0.6, 0.8, 1.0]}
            }
        else:
            raise ValueError(f"Unknown slider name: {slider_name}")
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application-level configuration."""
        return {
            'title': self.get('ui.title', 'lickcalc'),
            'debug': self.get('ui.debug', True),
            'hot_reload': self.get('ui.hot_reload', True)
        }
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.load_config()

# Global configuration instance
config = ConfigManager()