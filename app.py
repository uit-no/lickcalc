"""
Main application file for lickcalc webapp.
"""

# Create app instance first
from app_instance import app

# Import layout
from layout import app_layout

# Set layout
app.layout = app_layout

# Import all callbacks (this registers them with the app)
import callbacks

from _version import __version__

# Run the app
if __name__ == '__main__':
    from config_manager import config
    app_config = config.get_app_config()
    app.run(
        debug=app_config.get('debug', True),
        dev_tools_hot_reload=app_config.get('hot_reload', True)
    )
