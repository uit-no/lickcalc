import base64
import io
import json
import logging

import dash
from dash import dcc, html, dash_table, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import numpy as np

from helperfx import parse_medfile, parse_csvfile, parse_ddfile
from trompy import lickcalc

from tooltips import (get_binsize_tooltip, get_ibi_tooltip, get_minlicks_tooltip, 
                     get_longlick_tooltip, get_table_tooltips, get_onset_tooltip, get_offset_tooltip, get_session_length_tooltip, TOOLTIP_TEXTS)
from config_manager import config
from utils import (
    calculate_segment_stats,
    get_licks_for_burst_range,
    get_offsets_for_licks,
    validate_onset_times,
    validate_onset_offset_pairs
)
from layout import app_layout

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Set to WARNING to reduce noise in production
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to console
        # logging.FileHandler('lickcalc.log')  # Uncomment to log to file
    ]
)

# Get app configuration
app_config = config.get_app_config()
app = dash.Dash(__name__, title=app_config['title'], prevent_initial_callbacks=True)

# Get table cells and tooltips
table_cells, table_tooltips = get_table_tooltips()

app.layout = app_layout

# Add CSS for editable fields
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .editable-field {
                transition: all 0.2s ease;
            }
            .editable-field:not(:focus) {
                border: 1px solid transparent !important;
                background: transparent !important;
                box-shadow: none !important;
            }
            .editable-field:hover:not(:focus) {
                border: 1px solid #dee2e6 !important;
                background: rgba(0,0,0,0.02) !important;
            }
            .editable-field:focus {
                border: 1px solid #007bff !important;
                background: white !important;
                box-shadow: 0 0 5px rgba(0,123,255,0.3) !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Flask route to serve help file
@app.server.route('/help')
def serve_help():
    """Serve the help documentation page using template system"""
    from flask import render_template
    return render_template('help.html')







   














if __name__ == '__main__':
    app.run(debug=app_config['debug'], dev_tools_hot_reload=app_config['hot_reload'])
    
"""
TO DO:
    Add log scale option for y axis on intraburst frequency

    8. change slider dynamically to match different length files, e.g. 24h data gets 1, 2, 3, 4 h etc'
    12. multiple sessions in medfiles
    16. make histograms look the same, i.e. space between bars

    
For the histogram bin size, specify if its in minutes or seconds
"intraburst lick frequency" is average number of licks / second, might be nice to have that as a description somewhere to make it super clear what it is

Would be nice to have the sliders for setting intraburst lick interval and minimum licks/burst higher on the page
Maybe an explanation of what the Weibul plot is?
Definition of what a "long lick" is? And perhaps an option to set that, and an option to remove long licks from the data?

    
    
    
"""
    