"""
Callback registration for lickcalc webapp.
Import all callback modules to register their callbacks with the app.
"""

# Import all callback modules to register them
from . import config_callbacks
from . import data_callbacks
from . import graph_callbacks
from . import export_callbacks
from . import about_callbacks

__all__ = [
    'config_callbacks',
    'data_callbacks',
    'graph_callbacks',
    'export_callbacks',
    'about_callbacks',
]