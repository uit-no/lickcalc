#!/usr/bin/env python3
"""
Simple test to validate the app structure without running the full server
"""

try:
    print("Testing app imports...")
    
    # Test configuration
    from config_manager import config
    print("✓ Configuration manager imported")
    
    # Test that we can get the animal ID default
    animal_id = config.get('output.default_animal_id', 'ID1')
    print(f"✓ Default animal ID: {animal_id}")
    
    # Test basic imports
    import dash
    from dash import dcc, html, Input, Output, State
    import dash_bootstrap_components as dbc
    print("✓ Dash imports working")
    
    # Test our helper modules
    from helperfx import parse_medfile, parse_csvfile, parse_ddfile, lickCalc
    print("✓ Helper functions imported")
    
    from tooltips import (get_binsize_tooltip, get_ibi_tooltip, get_minlicks_tooltip, 
                         get_longlick_tooltip, get_table_tooltips, get_onset_tooltip, get_offset_tooltip)
    print("✓ Tooltips imported")
    
    # Test pandas for Excel export
    import pandas as pd
    print("✓ Pandas imported")
    
    try:
        import openpyxl
        print("✓ Openpyxl available for Excel export")
    except ImportError:
        print("⚠ Openpyxl not installed - Excel export will not work")
        print("  Install with: pip install openpyxl")
    
    print("\n✅ All core imports successful!")
    print("🚀 App should be ready to run!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")