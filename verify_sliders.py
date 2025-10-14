"""
Quick verification that slider configurations are correct
"""
from config_manager import config

print("="*70)
print("SLIDER CONFIGURATION VERIFICATION")
print("="*70)

# Test all sliders
sliders = ['interburst', 'session_bin', 'minlicks', 'longlick']

for slider_name in sliders:
    print(f"\n{slider_name.upper()} SLIDER:")
    print("-" * 70)
    
    try:
        slider_config = config.get_slider_config(slider_name)
        
        # Check required keys
        required_keys = ['min', 'max', 'step', 'value', 'marks']
        for key in required_keys:
            if key not in slider_config:
                print(f"  ❌ Missing key: {key}")
            else:
                if key == 'marks':
                    num_marks = len(slider_config[key])
                    print(f"  ✅ marks: {num_marks} marks present")
                    if num_marks == 0:
                        print(f"     ⚠️  WARNING: No marks defined!")
                    else:
                        # Show first and last mark
                        mark_keys = sorted(slider_config[key].keys())
                        print(f"     Range: {mark_keys[0]} to {mark_keys[-1]}")
                else:
                    print(f"  ✅ {key}: {slider_config[key]}")
        
        # Verify marks are strings
        if 'marks' in slider_config:
            for k, v in slider_config['marks'].items():
                if not isinstance(v, str):
                    print(f"  ⚠️  WARNING: Mark value at {k} is not a string: {v} ({type(v)})")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70)
print("\nIf all sliders show ✅ for all keys and have marks defined,")
print("then the configuration is correct. Restart the app to see changes.")
