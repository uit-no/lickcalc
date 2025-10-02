"""
Test script to verify configuration loading works correctly.
"""

try:
    from config_manager import config
    
    print("Configuration Manager Test")
    print("=" * 40)
    
    # Test basic configuration loading
    print("✓ Configuration module imported successfully")
    
    # Test getting default values
    session_defaults = config.get_session_defaults()
    print(f"Session defaults: {session_defaults}")
    
    microstructure_defaults = config.get_microstructure_defaults()
    print(f"Microstructure defaults: {microstructure_defaults}")
    
    # Test slider configurations
    slider_configs = {}
    for slider_name in ['session_bin', 'interburst', 'minlicks', 'longlick']:
        slider_configs[slider_name] = config.get_slider_config(slider_name)
        print(f"Slider '{slider_name}' config: {slider_configs[slider_name]}")
    
    # Test app configuration
    app_config = config.get_app_config()
    print(f"App config: {app_config}")
    
    print("\n✓ All configuration tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure PyYAML is installed: pip install PyYAML")
except Exception as e:
    print(f"❌ Configuration error: {e}")
    print("Check that config.yaml exists and is properly formatted")