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
            Path to the configuration YAML file (relative or absolute)
        """
        # If path is relative, make it relative to this file's directory
        config_path_obj = Path(config_path)
        if not config_path_obj.is_absolute():
            # Get the directory where this config_manager.py file is located
            this_file_dir = Path(__file__).parent.resolve()
            self.config_path = this_file_dir / config_path_obj
        else:
            self.config_path = config_path_obj
        
        self._config = None
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file with error handling."""
        try:
            print(f"DEBUG: Looking for config file at: {self.config_path.resolve()}")
            print(f"DEBUG: File exists: {self.config_path.exists()}")
            
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self._config = yaml.safe_load(file)
                print(f"✅ Configuration loaded successfully from {self.config_path}")
                print(f"DEBUG: min_licks_per_burst from file: {self._config.get('microstructure', {}).get('min_licks_per_burst', 'NOT FOUND')}")
            else:
                print(f"⚠️ Configuration file {self.config_path} not found. Using defaults.")
                print(f"DEBUG: Current working directory: {Path.cwd()}")
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
    
    def _generate_slider_marks(self, min_val: float, max_val: float, num_marks: int = 5) -> Dict[float, str]:
        """
        Generate evenly spaced marks for a slider.
        
        Parameters:
        -----------
        min_val : float
            Minimum value of the slider
        max_val : float
            Maximum value of the slider
        num_marks : int
            Number of marks to generate
            
        Returns:
        --------
        Dict[float, str] : Dictionary of marks {value: label}
        """
        if max_val <= min_val:
            return {min_val: str(min_val)}
        
        # Calculate step for marks (not the same as slider step)
        mark_range = max_val - min_val
        mark_step = mark_range / (num_marks - 1)
        
        marks = {}
        for i in range(num_marks):
            val = min_val + (i * mark_step)
            # Round to appropriate decimal places based on magnitude
            if mark_step >= 1:
                val = round(val, 0)
                # Convert to int if it's a whole number for cleaner display
                if val == int(val):
                    val = int(val)
            elif mark_step >= 0.1:
                val = round(val, 1)
            else:
                val = round(val, 2)
            
            # Format the label string nicely
            if isinstance(val, int):
                marks[val] = str(val)
            elif val == int(val):
                marks[int(val)] = str(int(val))
            else:
                marks[val] = str(val)
        
        return marks
    
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
            min_val = self.get('analysis.min_session_bins', 5)
            max_val = self.get('analysis.max_session_bins', 300)
            return {
                'min': min_val,
                'max': max_val,
                'step': self.get('analysis.session_bin_step', 5),
                'value': self.get('session.bin_size', 30),
                'marks': {5: '5', 30: '30', 60: '60', 120: '120', 300: '300'}
            }
        elif slider_name == 'interburst':
            min_val = self.get('analysis.min_interburst_interval', 0)
            max_val = self.get('analysis.max_interburst_interval', 3)
            return {
                'min': min_val,
                'max': max_val,
                'step': self.get('analysis.interburst_step', 0.25),
                'value': self.get('microstructure.interburst_interval', 0.5),
                'marks': self._generate_slider_marks(min_val, max_val, num_marks=6)
            }
        elif slider_name == 'minlicks':
            min_val = 1
            max_val = 5
            return {
                'min': min_val,
                'max': max_val,
                'step': 1,
                'value': self.get('microstructure.min_licks_per_burst', 1),
                'marks': {i: str(i) for i in range(int(min_val), int(max_val) + 1)}
            }
        elif slider_name == 'longlick':
            min_val = self.get('analysis.min_long_lick_threshold', 0.1)
            max_val = self.get('analysis.max_long_lick_threshold', 1.0)
            return {
                'min': min_val,
                'max': max_val,
                'step': self.get('analysis.long_lick_step', 0.1),
                'value': self.get('microstructure.long_lick_threshold', 0.3),
                'marks': self._generate_slider_marks(min_val, max_val, num_marks=5)
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