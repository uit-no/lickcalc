"""
Data loading and validation callbacks for lickcalc webapp.
"""

import io
from dash import html, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import base64
import json
import pandas as pd
import logging

from app_instance import app
from utils import validate_onset_times, validate_onset_offset_pairs, parse_medfile, parse_med_arraystyle, parse_csvfile, parse_ddfile, parse_kmfile, parse_ohrbets

# Callback to show/hide dropdowns based on analysis epoch selection
@app.callback(
    Output('division-method-col', 'style'),
    Output('n-bursts-col', 'style'),
    Output('between-start-col', 'style'),
    Output('between-stop-col', 'style'),
    Output('between-unit-col', 'style'),
    Output('trial-detection-col', 'style'),
    Output('trials-detected-col', 'style'),
    Output('trial-min-iti-col', 'style'),
    Output('trial-exclude-col', 'style'),
    Output('trial-load-col', 'style'),
    Input('division-number', 'value')
)
def toggle_dropdown_visibility(division_number):
    """Show division method dropdown only for 'divide by n' options, n-bursts dropdown only for 'first n bursts', between-times inputs only for 'between', and trial controls only for 'trial_based'."""
    # Show division method dropdown for numeric division values (2, 3, 4)
    if isinstance(division_number, int) and division_number > 1:
        division_method_style = {'display': 'block'}
    else:
        division_method_style = {'display': 'none'}
    
    # Show n-bursts dropdown only for 'first_n_bursts'
    if division_number == 'first_n_bursts':
        n_bursts_style = {'display': 'block'}
    else:
        n_bursts_style = {'display': 'none'}
    
    # Show between-times inputs only for between-times analysis
    if division_number == 'between':
        between_start_style = {'display': 'block'}
        between_stop_style = {'display': 'block'}
        between_unit_style = {'display': 'block'}
    else:
        between_start_style = {'display': 'none'}
        between_stop_style = {'display': 'none'}
        between_unit_style = {'display': 'none'}
    
    # Show trial-based controls only for 'trial_based' analysis
    if division_number == 'trial_based':
        trial_detection_style = {'display': 'block'}
        trials_detected_style = {'display': 'block'}
        trial_min_iti_style = {'display': 'block'}
        trial_exclude_style = {'display': 'block'}
        trial_load_style = {'display': 'block'}
    else:
        trial_detection_style = {'display': 'none'}
        trials_detected_style = {'display': 'none'}
        trial_min_iti_style = {'display': 'none'}
        trial_exclude_style = {'display': 'none'}
        trial_load_style = {'display': 'none'}
    
    return (division_method_style, n_bursts_style, between_start_style, between_stop_style, 
            between_unit_style, trial_detection_style, trials_detected_style, trial_min_iti_style, 
            trial_exclude_style, trial_load_style)

# Callback to control visibility of longlick controls based on offset data availability
@app.callback(Output('longlick-controls-column', 'style'),
              Input('offset-array', 'value'),
              Input('data-store', 'data'))  # Add data-store as input to trigger on file load
def toggle_longlick_controls_visibility(offset_key, data_store):
    """Show/hide longlick controls based on whether offset data is selected"""
    if offset_key is None or offset_key == 'none':
        # Hide longlick controls when no offset data is available
        return {'display': 'none'}
    else:
        # Show longlick controls when offset data is available
        return {'display': 'block', 'width': '33.33%'}  # Maintain the 4-column width (width=4 = 33.33%)
    
@app.callback(Output('data-store', 'data'),
              Output('fileloadLbl', 'children'),
              Output('onset-array', 'options'),
              Output('onset-array', 'value'),
              Output('offset-array', 'options'),
              Output('offset-array', 'value'),
              Output('filename-store', 'data'),
              Output('validation-status', 'children', allow_duplicate=True),
              Input('upload-data', 'contents'),
              Input('input-file-type', 'value'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              prevent_initial_call=True)
def load_and_clean_data(list_of_contents, input_file_type, list_of_names, list_of_dates):

    if list_of_contents is None:
        raise PreventUpdate
    else:
        try:
            content_type, content_string = list_of_contents.split(',')
            decoded = base64.b64decode(content_string)
            f = io.StringIO(decoded.decode('utf-8'))
            
            # Try to parse the file based on selected type
            # Parse based on selected type (ordered to mirror dropdown: med, med_array, csv, ohrbets, dd, km)
            if input_file_type == 'med':
                data_array = parse_medfile(f)
            elif input_file_type == 'med_array':
                data_array = parse_med_arraystyle(f)
            elif input_file_type == 'csv':
                data_array = parse_csvfile(f)
            elif input_file_type == 'ohrbets':
                data_array = parse_ohrbets(f)
            elif input_file_type == 'dd':
                data_array = parse_ddfile(f)
            elif input_file_type == 'km':
                data_array = parse_kmfile(f)
            else:
                raise ValueError(f"Unknown file type: {input_file_type}")
            
            # Check if parsing returned valid data
            if not data_array or len(data_array) == 0:
                raise ValueError("No data columns found in file")
            
            # Create options for dropdowns
            column_names = list(data_array.keys())
            
            # For onset array, include all columns
            onset_options = [{'label': key, 'value': key} for key in column_names]
            
            # For offset array, include all columns plus "None" option
            offset_options = [{'label': 'None (onset only)', 'value': 'none'}] + [{'label': key, 'value': key} for key in column_names]
            
            # Set default values
            if len(column_names) > 0:
                # Try to find common column names for onsets
                onset_default = None
                for potential_name in ['licks', 'onset', 'timestamps', 'time', 'Col. 1', column_names[0]]:
                    if potential_name in column_names:
                        onset_default = potential_name
                        break
                if onset_default is None:
                    onset_default = column_names[0]
                
                # Try to find common column names for offsets
                # Default to 'none' to prevent automatic triggering of lick duration analysis
                # User can manually select offset column after data is properly loaded
                offset_default = 'none'
                # Note: Automatic offset detection disabled to prevent cross-file contamination
                # for potential_name in ['offset', 'offsets', 'end', 'stop', 'Col. 2']:
                #     if potential_name in column_names:
                #         offset_default = potential_name
                #         break
            else:
                onset_default = 'none'
                offset_default = 'none'
            
            jsonified_dict = json.dumps(data_array)
            
            file_info = f"✅ Loaded: {list_of_names} ({len(column_names)} columns)"
            
            # Clear any previous error messages
            validation_msg = ""
                
            return jsonified_dict, file_info, onset_options, onset_default, offset_options, offset_default, list_of_names, validation_msg
            
        except Exception as e:
            # Simple error indicator for file label
            file_error_label = html.Span("❌ File not loaded", style={"color": "red", "font-weight": "bold"})
            
            # Detailed error message for validation area
            detailed_error = dbc.Alert([
                html.H5("❌ File Loading Error", className="alert-heading"),
                html.P(f"Failed to parse '{list_of_names}' as {input_file_type.upper()} format."),
                html.Hr(),
                html.P([
                    "Error details: ", html.Code(str(e))
                ], className="mb-2"),
                html.P([
                    html.Strong("Suggestions:"),
                    html.Ul([
                        html.Li("Try selecting a different file format from the dropdown above"),
                        html.Li("Check that your file matches the expected format"),
                        html.Li([
                            "Consult the ",
                            html.A("Help documentation", href="/help", target="_blank", style={"color": "white", "text-decoration": "underline"}),
                            " for file format examples"
                        ]),
                        html.Li("Ensure your file contains valid timestamp data")
                    ])
                ], className="mb-0")
            ], color="danger", dismissable=True)
            
            # Return empty/default values for other outputs
            return None, file_error_label, [], 'none', [{'label': 'None', 'value': 'none'}], 'none', None, detailed_error

# Callback to clear dependent stores when new data is loaded (prevents cross-file contamination)
@app.callback(Output('lick-data', 'data', allow_duplicate=True),
              Output('figure-data-store', 'data', allow_duplicate=True),
              Output('session-duration-store', 'data', allow_duplicate=True),
              Output('session-length-seconds', 'data', allow_duplicate=True),
              Input('data-store', 'data'),
              prevent_initial_call=True)
def clear_dependent_stores_on_new_file(data_store):
    """Clear dependent stores when new file data is loaded to prevent cross-file contamination"""
    # This callback triggers whenever data-store changes (new file loaded)
    # Clear all dependent stores to ensure clean state for new file
    return None, None, None, None

# Callback to validate onset/offset data and display status
@app.callback(Output('validation-status', 'children', allow_duplicate=True),
              Input('data-store', 'data'),
              Input('onset-array', 'value'),
              Input('offset-array', 'value'),
              prevent_initial_call=True)
def update_validation_status(data_store, onset_key, offset_key):
    """Display validation status for onset/offset data"""
    if not data_store:
        # Don't clear validation status if data_store is None (could be error message from file loading)
        raise PreventUpdate
    
    if not onset_key or onset_key == 'none':
        return ""
    
    try:
        data_array = json.loads(data_store)
        
        if onset_key not in data_array:
            return ""
        
        # Get the onset data first to validate ordering
        onset_df = pd.read_json(io.StringIO(data_array[onset_key]), orient='split')
        onset_times = onset_df["licks"].to_list()
        
        # Additional safety check - ensure we have meaningful data
        if not onset_times:
            return ""
        
        # First, validate that onset times are monotonically increasing
        onset_validation = validate_onset_times(onset_times)
        
        if not onset_validation['valid']:
            return dbc.Alert(
                f"❌ Onset time validation failed: {onset_validation['message']}",
                color="danger",
                dismissable=True
            )
        
        # If no offset column selected, show info and return early
        if not offset_key or offset_key == 'none':
            return dbc.Alert(
                "ℹ️ Onset-only data loaded (no offset column selected). Lick duration analysis will not be available.",
                color="info",
                dismissable=True
            )
        
        # Continue with offset validation if offset key is selected
        if offset_key not in data_array:
            return ""
        
        # Additional safeguard: Ensure both arrays exist and are non-empty
        # This helps prevent validation against stale/mismatched data
        if not data_array[offset_key]:
            return ""
        
        offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
        offset_times = offset_df["licks"].to_list()
        
        # Additional safety check for offset data
        if not offset_times:
            return ""
        
        # Critical fix: Check if this appears to be cross-file contamination
        # If we get a severe length mismatch (>1 difference), it might be old data
        if abs(len(onset_times) - len(offset_times)) > 1:
            # This suggests possible cross-file contamination
            # Return empty instead of showing misleading error
            return ""
        
        # Validate the onset-offset pairs
        validation = validate_onset_offset_pairs(onset_times, offset_times)
        
        if validation['valid']:
            if "Warning" in validation['message']:
                return dbc.Alert(
                    f"⚠️ Data loaded with warnings: {validation['message']}",
                    color="warning",
                    dismissable=True
                )
            else:
                return dbc.Alert(
                    f"✅ Data validation successful: {validation['message']}",
                    color="success",
                    dismissable=True
                )
        else:
            return dbc.Alert(
                f"❌ Data validation failed: {validation['message']}",
                color="danger",
                dismissable=True
            )
            
    except Exception as e:
        return dbc.Alert(
            f"❌ Error during validation: {str(e)}",
            color="danger",
            dismissable=True
        )

@app.callback(Output('lick-data', 'data'),
              Output('session-duration-store', 'data'),
              Input('data-store', 'data'),
              Input('onset-array', 'value'))
def get_lick_data(jsonified_dict, df_key):
    if jsonified_dict is None:
        # Clear lick data when data-store is cleared (e.g., file load error)
        return None, None
    
    if not df_key or df_key == 'none':
        return None, None
    
    data_array = json.loads(jsonified_dict)
    
    if df_key not in data_array:
        return None, None
    
    jsonified_df = data_array[df_key]
    
    # Get session duration and validate onset times
    df = pd.read_json(io.StringIO(jsonified_df), orient='split')
    
    if len(df) > 0:
        onset_times = df["licks"].to_list()
        
        # Validate that onset times are monotonically increasing
        validation = validate_onset_times(onset_times)
        
        if not validation['valid']:
            # Log the error and return None to prevent any data processing
            logging.error(f"Onset validation failed: {validation['message']}")
            # Return None for both outputs to completely stop downstream processing
            return None, None
        
        session_duration = max(onset_times)
    else:
        session_duration = 3600  # Default to 1 hour if no data

    return jsonified_df, session_duration

# Callback to update trials detected display
@app.callback(
    Output('trials-detected-display', 'children'),
    Input('division-number', 'value'),
    Input('lick-data', 'data'),
    Input('trial-detection-method', 'value'),
    Input('trial-min-iti', 'value')
)
def update_trials_detected(division_number, lick_data, detection_method, min_iti):
    """Update the trials detected display when in trial-based mode."""
    from utils.calculations import detect_trials
    
    # Only update if trial-based is selected
    if division_number != 'trial_based':
        return 'No trials detected'
    
    # If using manual loading, instruct the user
    if detection_method and detection_method != 'auto':
        return 'Awaiting loaded trials'
    
    # Check if we have data
    if not lick_data:
        return 'Load data file'
    
    # Check if min_iti is valid
    if not min_iti or min_iti <= 0:
        return 'Set ITI > 0'
    
    try:
        # Parse lick data - handle different formats
        if isinstance(lick_data, str):
            # If it's a JSON string, parse it
            lick_df = pd.read_json(io.StringIO(lick_data), orient='split')
            lick_times = lick_df["licks"].to_list()
        elif isinstance(lick_data, list):
            # If it's already a list, use it directly
            lick_times = lick_data
        else:
            logging.error(f"Unexpected lick_data type: {type(lick_data)}")
            return 'Invalid data format'
        
        if not lick_times or len(lick_times) == 0:
            return 'No licks in data'
        
    # Detect trials
        trial_info = detect_trials(lick_times, min_iti)
        n_trials = trial_info['n_trials']
        
        if n_trials == 0:
            return 'No trials detected'
        elif n_trials == 1:
            return '1 trial detected'
        else:
            return f'{n_trials} trials detected'
            
    except Exception as e:
        logging.error(f"Error detecting trials: {e}", exc_info=True)
        return f'Error: {str(e)[:30]}...'

# Flask route for help documentation
@app.server.route('/help')
def serve_help():
    """Serve the help documentation page using template system"""
    from flask import render_template
    return render_template('help.html')