"""
Configuration and slider management callbacks for lickcalc webapp.
"""
import dash
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import yaml
import base64

from app_instance import app
from config_manager import config
from tooltips import TOOLTIP_TEXTS, get_binsize_tooltip

def generate_slider_marks(min_val, max_val, num_marks=6):
    """Generate evenly spaced marks for sliders."""
    if max_val <= min_val:
        return {min_val: str(min_val)}
    
    mark_range = max_val - min_val
    mark_step = mark_range / (num_marks - 1)
    
    marks = {}
    for i in range(num_marks):
        val = min_val + (i * mark_step)
        if mark_step >= 1:
            val = round(val, 0)
            if val == int(val):
                val = int(val)
        elif mark_step >= 0.1:
            val = round(val, 1)
        else:
            val = round(val, 2)
        
        if isinstance(val, int):
            marks[val] = str(val)
        elif val == int(val):
            marks[int(val)] = str(int(val))
        else:
            marks[val] = str(val)
    
    return marks

# Config file management callback
@app.callback(
    Output('custom-config-store', 'data'),
    Output('session-bin-slider', 'value'),
    Output('session-bin-slider-seconds', 'data', allow_duplicate=True),
    Output('interburst-slider', 'min'),
    Output('interburst-slider', 'max'),
    Output('interburst-slider', 'step'),
    Output('interburst-slider', 'marks'),
    Output('interburst-slider', 'value'),
    Output('minlicks-slider', 'min'),
    Output('minlicks-slider', 'max'),
    Output('minlicks-slider', 'step'),
    Output('minlicks-slider', 'marks'),
    Output('minlicks-slider', 'value'),
    Output('longlick-threshold', 'min'),
    Output('longlick-threshold', 'max'),
    Output('longlick-threshold', 'step'),
    Output('longlick-threshold', 'marks'),
    Output('longlick-threshold', 'value'),
    Output('session-fig-type', 'value'),
    Output('session-length-input', 'value', allow_duplicate=True),
    Output('session-length-unit', 'value'),
    Output('input-file-type', 'value'),
    Output('config-button-content', 'children'),
    Output('config-button-content', 'className'),
    Input('upload-config', 'contents'),
    State('upload-config', 'filename'),
    State('session-length-input', 'value'),
    prevent_initial_call=True
)
def load_config(config_contents, config_filename, current_session_length):
    """Handle custom config file upload"""
    if not config_contents:
        raise PreventUpdate
    
    try:
        content_type, content_string = config_contents.split(',')
        decoded = base64.b64decode(content_string)
        config_text = decoded.decode('utf-8')
        
        # Parse YAML
        import yaml
        custom_config = yaml.safe_load(config_text)
        
        # Extract values with fallbacks to defaults
        session_bin = custom_config.get('session', {}).get('bin_size', config.get('session.bin_size', 30))
        ibi = custom_config.get('microstructure', {}).get('interburst_interval', config.get('microstructure.interburst_interval', 0.5))
        minlicks = custom_config.get('microstructure', {}).get('min_licks_per_burst', config.get('microstructure.min_licks_per_burst', 1))
        longlick = custom_config.get('microstructure', {}).get('long_lick_threshold', config.get('microstructure.long_lick_threshold', 0.3))
        figtype = custom_config.get('session', {}).get('fig_type', config.get('session.fig_type', 'hist'))
        session_length_config = custom_config.get('session', {}).get('length', 3600)
        session_length_unit = custom_config.get('session', {}).get('length_unit', config.get('session.length_unit', 's'))
        file_type = custom_config.get('files', {}).get('default_file_type', config.get('files.default_file_type', 'med'))
        
        # Helper function to generate reasonable slider marks
        def generate_slider_marks(min_val, max_val, num_marks=5):
            """Generate evenly spaced marks for a slider"""
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
                elif mark_step >= 0.1:
                    val = round(val, 1)
                else:
                    val = round(val, 2)
                marks[val] = str(val)
            
            return marks
        
        # Extract slider range configurations with fallbacks to defaults
        analysis_config = custom_config.get('analysis', {})
        
        # Interburst slider config
        ibi_min = analysis_config.get('min_interburst_interval', config.get('analysis.min_interburst_interval', 0))
        ibi_max = analysis_config.get('max_interburst_interval', config.get('analysis.max_interburst_interval', 3))
        ibi_step = analysis_config.get('interburst_step', config.get('analysis.interburst_step', 0.25))
        ibi_marks = generate_slider_marks(ibi_min, ibi_max, num_marks=6)
        
        # Minlicks slider config (typically fixed but allow override)
        minlicks_min = analysis_config.get('min_licks_per_burst_range', 1)
        minlicks_max = analysis_config.get('max_licks_per_burst_range', 5)
        minlicks_step = 1
        minlicks_marks = {i: str(i) for i in range(int(minlicks_min), int(minlicks_max) + 1)}
        
        # Longlick slider config
        longlick_min = analysis_config.get('min_long_lick_threshold', config.get('analysis.min_long_lick_threshold', 0.1))
        longlick_max = analysis_config.get('max_long_lick_threshold', config.get('analysis.max_long_lick_threshold', 1.0))
        longlick_step = analysis_config.get('long_lick_step', config.get('analysis.long_lick_step', 0.1))
        longlick_marks = generate_slider_marks(longlick_min, longlick_max, num_marks=5)
        
        # Handle 'auto' value for session length
        # If config says 'auto', keep the current value (don't override existing auto-detected value)
        if session_length_config == 'auto':
            session_length = current_session_length if current_session_length else 3600
        else:
            # Use the specified value from config
            session_length = session_length_config
        
        return (
            custom_config,  # Store the full custom config
            session_bin,
            session_bin,  # Also update the seconds store with the same value (it's already in seconds)
            ibi_min,
            ibi_max,
            ibi_step,
            ibi_marks,
            ibi,
            minlicks_min,
            minlicks_max,
            minlicks_step,
            minlicks_marks,
            minlicks,
            longlick_min,
            longlick_max,
            longlick_step,
            longlick_marks,
            longlick,
            figtype,
            session_length,
            session_length_unit,
            file_type,
            "✅ Custom Config Loaded",  # Change button text
            "btn btn-success btn-sm"  # Change to green button
        )
        
    except yaml.YAMLError as e:
        # Return current values on error
        return (
            dash.no_update,  # custom-config-store
            dash.no_update,  # session-bin-slider value
            dash.no_update,  # session-bin-slider-seconds
            dash.no_update,  # interburst-slider min
            dash.no_update,  # interburst-slider max
            dash.no_update,  # interburst-slider step
            dash.no_update,  # interburst-slider marks
            dash.no_update,  # interburst-slider value
            dash.no_update,  # minlicks-slider min
            dash.no_update,  # minlicks-slider max
            dash.no_update,  # minlicks-slider step
            dash.no_update,  # minlicks-slider marks
            dash.no_update,  # minlicks-slider value
            dash.no_update,  # longlick-threshold min
            dash.no_update,  # longlick-threshold max
            dash.no_update,  # longlick-threshold step
            dash.no_update,  # longlick-threshold marks
            dash.no_update,  # longlick-threshold value
            dash.no_update,  # session-fig-type
            dash.no_update,  # session-length-input
            dash.no_update,  # session-length-unit
            dash.no_update,  # input-file-type
            "❌ YAML Error",
            "btn btn-danger btn-sm"
        )
        
    except Exception as e:
        # Return current values on error
        return (
            dash.no_update,  # custom-config-store
            dash.no_update,  # session-bin-slider value
            dash.no_update,  # session-bin-slider-seconds
            dash.no_update,  # interburst-slider min
            dash.no_update,  # interburst-slider max
            dash.no_update,  # interburst-slider step
            dash.no_update,  # interburst-slider marks
            dash.no_update,  # interburst-slider value
            dash.no_update,  # minlicks-slider min
            dash.no_update,  # minlicks-slider max
            dash.no_update,  # minlicks-slider step
            dash.no_update,  # minlicks-slider marks
            dash.no_update,  # minlicks-slider value
            dash.no_update,  # longlick-threshold min
            dash.no_update,  # longlick-threshold max
            dash.no_update,  # longlick-threshold step
            dash.no_update,  # longlick-threshold marks
            dash.no_update,  # longlick-threshold value
            dash.no_update,  # session-fig-type
            dash.no_update,  # session-length-input
            dash.no_update,  # session-length-unit
            dash.no_update,  # input-file-type
            "❌ Load Error",
            "btn btn-danger btn-sm"
        )

# Callback to update session-length-seconds store whenever session length or unit changes
@app.callback(
    Output('session-length-seconds', 'data'),
    Input('session-length-input', 'value'),
    Input('session-length-unit', 'value')
)
def update_session_length_seconds(session_length, unit):
    """Convert session length to seconds based on the selected unit."""
    if session_length is None or session_length <= 0:
        return None
    
    # Convert to seconds based on unit
    if unit == 'min':
        return session_length * 60
    elif unit == 'hr':
        return session_length * 3600
    else:  # unit == 's' or default
        return session_length
    
# Callback to update the input field when unit changes (convert display value)
@app.callback(
    Output('session-length-input', 'value', allow_duplicate=True),
    Input('session-length-unit', 'value'),
    State('session-length-seconds', 'data'),
    prevent_initial_call=True
)
def convert_display_value_on_unit_change(new_unit, current_seconds):
    """When unit changes, convert the display value to show equivalent in new unit."""
    if current_seconds is None or current_seconds <= 0:
        raise PreventUpdate
    
    # Convert from seconds to the new unit
    if new_unit == 'min':
        new_value = current_seconds / 60
    elif new_unit == 'hr':
        new_value = current_seconds / 3600
    else:  # 's'
        new_value = current_seconds
    
    # Round to reasonable precision
    if new_value >= 10:
        return round(new_value)
    else:
        return round(new_value, 2)

# Callback to dynamically adjust bin slider based on session length
@app.callback(
    Output('session-bin-slider', 'min'),
    Output('session-bin-slider', 'max'),
    Output('session-bin-slider', 'step'),
    Output('session-bin-slider', 'marks'),
    Output('session-bin-slider', 'value', allow_duplicate=True),
    Output('binsize-label-container', 'children'),
    Input('session-length-seconds', 'data'),
    State('session-bin-slider-seconds', 'data'),
    prevent_initial_call=True
)
def update_bin_slider_range(session_length_seconds, current_bin_seconds):
    """Dynamically adjust bin slider based on session length in seconds."""
    
    if not session_length_seconds or session_length_seconds <= 0:
        session_length_seconds = 3600  # Default to 1 hour
    
    # Get config default bin size in seconds
    config_bin_size = config.get('session.bin_size', 30)
    
    # Three tiers based on session length
    if session_length_seconds <= 3600:  # Up to 1 hour: use seconds (5-300s)
        min_val = 5
        max_val = 300
        step = 5
        unit_label = "Bin size (seconds)"
        marks = {i: str(i) for i in range(0, 301, 60)}
        # Keep current value if in range, otherwise use config default
        if current_bin_seconds and min_val <= current_bin_seconds <= max_val:
            value = current_bin_seconds
        else:
            # Use config default, constrained to valid range
            value = max(min_val, min(max_val, config_bin_size))
            
    elif session_length_seconds <= 14400:  # 1-4 hours: use minutes (1-60 min = 60-3600s)
        min_val = 1
        max_val = 60
        step = 1
        unit_label = "Bin size (minutes)"
        marks = {i: str(i) for i in range(0, 61, 10)}
        # Convert current value from seconds to minutes for display
        if current_bin_seconds:
            value = max(min_val, min(max_val, round(current_bin_seconds / 60)))
        else:
            # Use config default converted to minutes, constrained to valid range
            value = max(min_val, min(max_val, round(config_bin_size / 60)))
            
    else:  # Over 4 hours: use hours (0.5-2 hr = 1800-7200s)
        min_val = 0.5
        max_val = 2
        step = 0.25
        unit_label = "Bin size (hours)"
        marks = {0.5: '0.5', 1: '1', 1.5: '1.5', 2: '2'}
        # Convert current value from seconds to hours for display
        if current_bin_seconds:
            value = max(min_val, min(max_val, round(current_bin_seconds / 3600, 2)))
        else:
            # Use config default converted to hours, constrained to valid range
            value = max(min_val, min(max_val, round(config_bin_size / 3600, 2)))
    
    # Update the label
    label_children = [
        html.Div([
            html.Span(unit_label),
            html.Span(" ⓘ", id='binsize-help', style={"color": "#007bff", "cursor": "help", "margin-left": "5px"})
        ]),
        dbc.Tooltip(
            TOOLTIP_TEXTS['binsize'],
            target='binsize-help',
            placement='top'
        )
    ]
    
    return min_val, max_val, step, marks, value, label_children

# Callback to convert bin slider value to seconds
@app.callback(
    Output('session-bin-slider-seconds', 'data'),
    Input('session-bin-slider', 'value'),
    Input('session-length-seconds', 'data')
)
def convert_bin_slider_to_seconds(slider_value, session_length_seconds):
    """Convert bin slider display value to seconds based on current tier."""
    if not slider_value or not session_length_seconds:
        return 30  # Default
    
    if session_length_seconds <= 3600:
        # Slider is in seconds
        return slider_value
    elif session_length_seconds <= 14400:
        # Slider is in minutes, convert to seconds
        return slider_value * 60
    else:
        # Slider is in hours, convert to seconds
        return slider_value * 3600
    