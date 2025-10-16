"""
App instance creation for lickcalc webapp.
This module creates the Dash app instance that can be imported by callback modules.
"""

import dash
from config_manager import config

# Get app configuration
app_config = config.get_app_config()

# Create Dash app
app = dash.Dash(
    __name__, 
    title=app_config['title'], 
    prevent_initial_callbacks=True
)

# Server for deployment
server = app.server