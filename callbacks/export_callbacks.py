"""
Export and results table callbacks for lickcalc webapp.
"""

import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import numpy as np
import io
from datetime import datetime

from app_instance import app
from config_manager import config

# Excel export callback
@app.callback(Output("download-excel", "data"),
              Output("export-status", "children"),
              Input('export-btn', 'n_clicks'),
              State('animal-id-input', 'value'),
              State('export-data-checklist', 'value'),
              State('figure-data-store', 'data'),
              State('filename-store', 'data'),
              prevent_initial_call=True)
def export_to_excel(n_clicks, animal_id, selected_data, figure_data, source_filename):
    """Export selected data to Excel with multiple sheets"""
    if n_clicks == 0 or not figure_data:
        raise PreventUpdate
    
    try:
        # Create Excel writer object
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"lickcalc_Export_{animal_id}_{timestamp}.xlsx"
        
        # Create a BytesIO buffer
        import io
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main summary sheet
            if 'summary_stats' in figure_data:
                stats = figure_data['summary_stats']
                
                # Check minimum burst threshold for Weibull analysis in export
                min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                export_n_bursts = stats.get('n_bursts', 0)
                
                # Format Weibull parameters based on burst threshold
                weibull_alpha_text = 'N/A (insufficient bursts)' if export_n_bursts < min_bursts_required else (f"{stats.get('weibull_alpha', 'N/A'):.3f}" if stats.get('weibull_alpha') else 'N/A')
                weibull_beta_text = 'N/A (insufficient bursts)' if export_n_bursts < min_bursts_required else (f"{stats.get('weibull_beta', 'N/A'):.3f}" if stats.get('weibull_beta') else 'N/A')
                weibull_rsq_text = 'N/A (insufficient bursts)' if export_n_bursts < min_bursts_required else (f"{stats.get('weibull_rsq', 'N/A'):.3f}" if stats.get('weibull_rsq') else 'N/A')
                
                summary_df = pd.DataFrame([
                    ['Animal ID', animal_id],
                    ['Source Filename', source_filename if source_filename else 'N/A'],
                    ['Export Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    ['Total Licks', stats.get('total_licks', 'N/A')],
                    ['Intraburst Frequency (Hz)', f"{stats.get('intraburst_freq', 'N/A'):.3f}" if stats.get('intraburst_freq') else 'N/A'],
                    ['Number of Bursts', stats.get('n_bursts', 'N/A')],
                    ['Mean Licks per Burst', f"{stats.get('mean_licks_per_burst', 'N/A'):.2f}" if stats.get('mean_licks_per_burst') else 'N/A'],
                    ['Weibull Alpha', weibull_alpha_text],
                    ['Weibull Beta', weibull_beta_text],
                    ['Weibull R-squared', weibull_rsq_text],
                    ['Number of Long Licks', stats.get('n_long_licks', 'N/A')],
                    ['Maximum Lick Duration (s)', f"{stats.get('max_lick_duration', 'N/A'):.4f}" if isinstance(stats.get('max_lick_duration'), (int, float)) else stats.get('max_lick_duration', 'N/A')]
                ], columns=['Property', 'Value'])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Export selected figure data
            if 'session_hist' in selected_data and 'session_hist' in figure_data:
                data = figure_data['session_hist']
                df = pd.DataFrame({
                    'Time_Bin_Center_s': data['bin_centers'],
                    'Lick_Count': data['counts']
                })
                df.to_excel(writer, sheet_name='Session_Histogram', index=False)
            
            if 'intraburst_freq' in selected_data and 'intraburst_freq' in figure_data:
                data = figure_data['intraburst_freq']
                df = pd.DataFrame({
                    'ILI_Bin_Center_s': data['ili_centers'],
                    'Frequency': data['counts']
                })
                df.to_excel(writer, sheet_name='Intraburst_Frequency', index=False)
            
            if 'lick_lengths' in selected_data and figure_data.get('lick_lengths'):
                data = figure_data['lick_lengths']
                df = pd.DataFrame({
                    'Duration_Bin_Center_s': data['duration_centers'],
                    'Frequency': data['counts']
                })
                df.to_excel(writer, sheet_name='Lick_Lengths', index=False)
            
            if 'burst_hist' in selected_data and 'burst_hist' in figure_data:
                data = figure_data['burst_hist']
                df = pd.DataFrame({
                    'Burst_Size': data['burst_sizes'],
                    'Frequency': data['counts']
                })
                df.to_excel(writer, sheet_name='Burst_Histogram', index=False)
            
            if 'burst_prob' in selected_data and 'burst_prob' in figure_data:
                data = figure_data['burst_prob']
                df = pd.DataFrame({
                    'Burst_Size': data['burst_sizes'],
                    'Probability': data['probabilities']
                })
                df.to_excel(writer, sheet_name='Burst_Probability', index=False)
            
            if 'burst_details' in selected_data and figure_data.get('burst_details'):
                data = figure_data['burst_details']
                df = pd.DataFrame({
                    'Burst_Number': data['burst_numbers'],
                    'N_Licks': data['n_licks'],
                    'Start_Time_s': data['start_times'],
                    'End_Time_s': data['end_times'],
                    'Duration_s': data['durations']
                })
                df.to_excel(writer, sheet_name='Burst_Details', index=False)
        
        # Get the value from the buffer
        output.seek(0)
        excel_data = output.getvalue()
        
        status_msg = dbc.Alert(
            f"✅ Successfully exported data for {animal_id} to {filename}",
            color="success",
            dismissable=True,
            duration=4000
        )
        
        return dcc.send_bytes(excel_data, filename), status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Export failed: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return None, error_msg

# Results table callbacks

# Add current results to table
@app.callback(Output('results-table-store', 'data'),
              Output('table-status', 'children'),
              Input('add-to-table-btn', 'n_clicks'),
              State('animal-id-input', 'value'),
              State('figure-data-store', 'data'),
              State('results-table-store', 'data'),
              State('filename-store', 'data'),
              State('division-number', 'value'),
              State('division-method', 'value'),
              State('n-bursts-number', 'value'),
              State('session-length-seconds', 'data'),
              State('data-store', 'data'),
              State('onset-array', 'value'),
              State('offset-array', 'value'),
              State('interburst-slider', 'value'),
              State('minlicks-slider', 'value'),
              State('longlick-threshold', 'value'),
              State('remove-longlicks-checkbox', 'value'),
              prevent_initial_call=True)
def add_to_results_table(n_clicks, animal_id, figure_data, existing_data, source_filename, 
                        division_number, division_method, n_bursts_number, session_length_seconds, data_store, onset_key, offset_key,
                        ibi_slider, minlicks_slider, longlick_slider, remove_longlicks):
    """Add current analysis results to the results table with optional divisions"""
    # Use slider values directly
    ibi = ibi_slider
    minlicks = minlicks_slider
    longlick_th = longlick_slider
    remove_long = 'remove' in remove_longlicks
    
    if n_clicks == 0 or not figure_data or 'summary_stats' not in figure_data:
        raise PreventUpdate
    
    try:
        # If no division (whole session), recalculate with proper onset/offset validation
        if division_number == 'whole_session':
            # Load the data and recalculate to ensure proper long lick statistics
            import json
            data_array = json.loads(data_store)
            df = pd.read_json(io.StringIO(data_array[onset_key]), orient='split')
            lick_times = df["licks"].to_list()
            
            # Get offset data if available
            offset_times = None
            if offset_key and offset_key != 'none':
                offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                offset_times = offset_df["licks"].to_list()
            
            # For whole session: start time is always 0, end time uses session length input
            start_time = 0
            
            # Use session length from input box (already converted to seconds), or fall back to max lick time
            if session_length_seconds and session_length_seconds > 0:
                end_time = session_length_seconds
            else:
                end_time = max(lick_times) if lick_times else 0
            
            # Recalculate stats with proper onset/offset validation
            try:
                # Use enhanced lickcalc with current parameters to get accurate long lick stats
                enhanced_results = lickcalc(
                    licks=lick_times,
                    offset=offset_times if offset_times else [],
                    burstThreshold=ibi,
                    minburstlength=minlicks,
                    longlickThreshold=longlick_th,
                    remove_longlicks=remove_long if offset_times else False
                )
                
                # Create new row with recalculated stats
                # Check minimum burst threshold for Weibull analysis
                min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                num_bursts = enhanced_results.get('bNum', 0)
                
                new_row = {
                    'id': animal_id or 'Unknown',
                    'source_filename': source_filename if source_filename else 'N/A',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'interburst_interval': ibi,
                    'min_burst_size': minlicks,
                    'longlick_threshold': longlick_th,
                    'total_licks': enhanced_results.get('total', np.nan),
                    'intraburst_freq': enhanced_results.get('freq', np.nan),
                    'n_bursts': enhanced_results.get('bNum', np.nan),
                    'mean_licks_per_burst': enhanced_results.get('bMean', np.nan),
                    'weibull_alpha': enhanced_results.get('weib_alpha', np.nan) if (enhanced_results.get('weib_alpha') is not None and num_bursts >= min_bursts_required) else np.nan,
                    'weibull_beta': enhanced_results.get('weib_beta', np.nan) if (enhanced_results.get('weib_beta') is not None and num_bursts >= min_bursts_required) else np.nan,
                    'weibull_rsq': enhanced_results.get('weib_rsq', np.nan) if (enhanced_results.get('weib_rsq') is not None and num_bursts >= min_bursts_required) else np.nan,
                    'n_long_licks': len(enhanced_results.get('longlicks', [])) if offset_times else np.nan,
                    'max_lick_duration': np.max(enhanced_results.get('licklength', [])) if offset_times and enhanced_results.get('licklength') is not None and len(enhanced_results.get('licklength', [])) > 0 else np.nan,
                    'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                }
                
            except Exception as e:
                logging.error(f"Error recalculating whole session stats: {e}")
                # Fall back to figure_data stats - check if they contain valid long lick data
                stats = figure_data['summary_stats']
                
                # Try to get properly calculated long lick values from figure_data
                n_long_licks = np.nan
                max_lick_duration = np.nan
                
                if isinstance(stats.get('n_long_licks'), (int, float)):
                    n_long_licks = stats.get('n_long_licks')
                elif offset_times:
                    # If figure_data doesn't have proper values but we have offset data, try a quick calculation
                    try:
                        temp_results = lickcalc(lick_times, offset=offset_times, longlickThreshold=longlick_th)
                        n_long_licks = len(temp_results.get('longlicks', []))
                        licklength_array = temp_results.get('licklength', [])
                        if licklength_array is not None and len(licklength_array) > 0:
                            max_lick_duration = np.max(licklength_array)
                    except Exception:
                        pass
                
                # Only use figure_data value if we haven't calculated it above
                if max_lick_duration is np.nan and isinstance(stats.get('max_lick_duration'), (int, float)):
                    max_lick_duration = stats.get('max_lick_duration')
                
                # Check minimum burst threshold for Weibull analysis in fallback case too
                min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                fallback_n_bursts = stats.get('n_bursts', 0)
                
                new_row = {
                    'id': animal_id or 'Unknown',
                    'source_filename': source_filename if source_filename else 'N/A',
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time,
                    'interburst_interval': ibi,
                    'min_burst_size': minlicks,
                    'longlick_threshold': longlick_th,
                    'total_licks': stats.get('total_licks', np.nan),
                    'intraburst_freq': stats.get('intraburst_freq', np.nan),
                    'n_bursts': stats.get('n_bursts', np.nan),
                    'mean_licks_per_burst': stats.get('mean_licks_per_burst', np.nan),
                    'weibull_alpha': stats.get('weibull_alpha', np.nan) if (stats.get('weibull_alpha') is not None and fallback_n_bursts >= min_bursts_required) else np.nan,
                    'weibull_beta': stats.get('weibull_beta', np.nan) if (stats.get('weibull_beta') is not None and fallback_n_bursts >= min_bursts_required) else np.nan,
                    'weibull_rsq': stats.get('weibull_rsq', np.nan) if (stats.get('weibull_rsq') is not None and fallback_n_bursts >= min_bursts_required) else np.nan,
                    'n_long_licks': n_long_licks,
                    'max_lick_duration': max_lick_duration,
                    'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                }
            
            # Add to existing data
            updated_data = existing_data.copy() if existing_data else []
            updated_data.append(new_row)
            
            status_msg = dbc.Alert(
                f"✅ Added results for {animal_id} to table",
                color="success",
                dismissable=True,
                duration=3000
            )
            
            return updated_data, status_msg
        
        else:
            # Handle divisions - need to reanalyze data in segments
            if not data_store or not onset_key:
                raise Exception("No data available for division analysis")
            
            import json
            data_array = json.loads(data_store)
            df = pd.read_json(io.StringIO(data_array[onset_key]), orient='split')
            lick_times = df["licks"].to_list()
            
            # Get offset data if available
            offset_times = None
            if offset_key and offset_key != 'none':
                offset_df = pd.read_json(io.StringIO(data_array[offset_key]), orient='split')
                offset_times = offset_df["licks"].to_list()
                
                # Adjust arrays if needed
                if len(lick_times) - len(offset_times) == 1:
                    lick_times = lick_times[:-1]
                elif len(lick_times) != len(offset_times):
                    lick_times = lick_times[:len(offset_times)]
            
            # Calculate divisions using enhanced lickcalc function
            division_rows = []
            
            # Check if it's "First n bursts" analysis
            if division_number == 'first_n_bursts':
                # Calculate for first n bursts only
                enhanced_results = lickcalc(
                    licks=lick_times,
                    offset=offset_times if offset_times else [],
                    burstThreshold=ibi,
                    minburstlength=minlicks,
                    longlickThreshold=longlick_th,
                    only_return_first_n_bursts=n_bursts_number,
                    remove_longlicks=remove_long if offset_times else False
                )
                
                # Calculate correct values for first n bursts based on burst information
                burst_licks = enhanced_results.get('bLicks', [])  # Number of licks in each burst
                burst_start = enhanced_results.get('bStart', [])  # Start time of each burst
                burst_end = enhanced_results.get('bEnd', [])      # End time of each burst
                all_ilis = enhanced_results.get('ilis', [])      # All interlick intervals
                
                # Calculate total licks from first n bursts
                total_licks_first_n = sum(burst_licks) if burst_licks else 0
                
                # Calculate start and end times
                start_time = burst_start[0] if burst_start else 0
                end_time = burst_end[-1] if burst_end else 0
                duration = end_time - start_time if burst_start and burst_end else 0
                
                # Calculate intraburst frequency from first n bursts only (using only intraburst ILIs)
                if burst_licks and all_ilis is not None and len(all_ilis) > 0:
                    # Get the end index of the nth burst (total licks in first n bursts)
                    end_of_nth_burst = total_licks_first_n
                    # Get ILIs only from the first n bursts (ILIs array is one element shorter than licks)
                    first_n_ilis = all_ilis[:end_of_nth_burst-1] if end_of_nth_burst > 1 else []
                    
                    # Filter to include only intraburst ILIs (< interburst interval threshold)
                    intraburst_ilis = first_n_ilis[first_n_ilis < ibi] if len(first_n_ilis) > 0 else []
                    
                    if len(intraburst_ilis) > 0:
                        mean_intraburst_ili = np.mean(intraburst_ilis)
                        intraburst_freq = 1.0 / mean_intraburst_ili if mean_intraburst_ili > 0 else 0
                    else:
                        intraburst_freq = 0
                else:
                    intraburst_freq = 0
                
                # Create single row for first n bursts analysis
                # Note: Weibull parameters are excluded for first n bursts as they require full session data
                division_rows.append({
                    'id': f"{animal_id}_F{n_bursts_number}" if animal_id else f"F{n_bursts_number}",
                    'source_filename': f"{source_filename} (First {n_bursts_number} bursts)" if source_filename else f"First {n_bursts_number} bursts",
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'interburst_interval': ibi,
                    'min_burst_size': minlicks,
                    'longlick_threshold': longlick_th,
                    'total_licks': total_licks_first_n,
                    'intraburst_freq': intraburst_freq,
                    'n_bursts': enhanced_results.get('bNum', 0),
                    'mean_licks_per_burst': enhanced_results.get('bMean', 0),
                    'weibull_alpha': np.nan,  # Excluded for first n bursts analysis
                    'weibull_beta': np.nan,   # Excluded for first n bursts analysis
                    'weibull_rsq': np.nan,    # Excluded for first n bursts analysis
                    'n_long_licks': len(enhanced_results.get('longlicks', [])) if offset_times and enhanced_results.get('longlicks') is not None else 0,
                    'max_lick_duration': np.max(enhanced_results.get('licklength', [])) if offset_times and enhanced_results.get('licklength') is not None and len(enhanced_results.get('licklength', [])) > 0 else np.nan,
                    'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                })
                
            # Use enhanced lickcalc with division parameters for numeric divisions
            elif isinstance(division_number, int) and division_number > 1:
                if division_method == 'time':
                    # Calculate with time divisions
                    enhanced_results = lickcalc(
                        licks=lick_times,
                        offset=offset_times if offset_times else [],
                        burstThreshold=ibi,
                        minburstlength=minlicks,
                        longlickThreshold=longlick_th,
                        time_divisions=division_number,
                        session_length=session_length_seconds if session_length_seconds and session_length_seconds > 0 else None,
                        remove_longlicks=remove_long if offset_times else False
                    )
                
                # Convert trompy division results to webapp format
                if 'time_divisions' in enhanced_results:
                    # Determine the total session duration for proper time division calculation
                    total_session_duration = session_length_seconds if session_length_seconds and session_length_seconds > 0 else max(lick_times) if lick_times else 0
                    division_duration = total_session_duration / division_number
                    
                    for i, div in enumerate(enhanced_results['time_divisions']):
                        # Ensure divisions start from 0 and cover the full session
                        division_start = i * division_duration
                        division_end = (i + 1) * division_duration
                        
                        # Check minimum burst threshold for Weibull analysis
                        min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                        div_n_bursts = div['n_bursts']
                        
                        division_rows.append({
                            'id': f"{animal_id}_T{div['division_number']}" if animal_id else f"T{div['division_number']}",
                            'source_filename': f"{source_filename} (Time {div['division_number']}/{division_number}: {division_start:.0f}-{division_end:.0f}s)" if source_filename else f"Time {div['division_number']}/{division_number} ({division_start:.0f}-{division_end:.0f}s)",
                            'start_time': division_start,
                            'end_time': division_end,
                            'duration': division_duration,
                            'interburst_interval': ibi,
                            'min_burst_size': minlicks,
                            'longlick_threshold': longlick_th,
                            'total_licks': div['total_licks'],
                            'intraburst_freq': div['intraburst_freq'],
                            'n_bursts': div['n_bursts'],
                            'mean_licks_per_burst': div['mean_licks_per_burst'],
                            'weibull_alpha': div['weibull_alpha'] if (div['weibull_alpha'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                            'weibull_beta': div['weibull_beta'] if (div['weibull_beta'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                            'weibull_rsq': div['weibull_rsq'] if (div['weibull_rsq'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                            'n_long_licks': div['n_long_licks'],
                            'max_lick_duration': div['max_lick_duration'],
                            'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                        })
            
                elif division_method == 'bursts':
                    # Calculate with burst divisions
                    enhanced_results = lickcalc(
                        licks=lick_times,
                        offset=offset_times if offset_times else [],
                        burstThreshold=ibi,
                        minburstlength=minlicks,
                        longlickThreshold=longlick_th,
                        burst_divisions=division_number,
                        remove_longlicks=remove_long if offset_times else False
                    )
                    
                    # Convert trompy division results to webapp format
                    if 'burst_divisions' in enhanced_results:
                        for div in enhanced_results['burst_divisions']:
                            bursts_in_segment = div['end_burst'] - div['start_burst']
                            
                            # Check minimum burst threshold for Weibull analysis
                            min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
                            div_n_bursts = div['n_bursts']
                            
                            division_rows.append({
                                'id': f"{animal_id}_B{div['division_number']}" if animal_id else f"B{div['division_number']}",
                                'source_filename': f"{source_filename} (Bursts {div['start_burst']+1}-{div['end_burst']}, {bursts_in_segment} bursts)" if source_filename else f"Bursts {div['start_burst']+1}-{div['end_burst']} ({bursts_in_segment} bursts)",
                                'start_time': div['start_time'],
                                'end_time': div['end_time'],
                                'duration': div['duration'],
                                'interburst_interval': ibi,
                                'min_burst_size': minlicks,
                                'longlick_threshold': longlick_th,
                                'total_licks': div['total_licks'],
                                'intraburst_freq': div['intraburst_freq'],
                                'n_bursts': div['n_bursts'],
                                'mean_licks_per_burst': div['mean_licks_per_burst'],
                                'weibull_alpha': div['weibull_alpha'] if (div['weibull_alpha'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                'weibull_beta': div['weibull_beta'] if (div['weibull_beta'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                'weibull_rsq': div['weibull_rsq'] if (div['weibull_rsq'] is not None and div_n_bursts >= min_bursts_required) else np.nan,
                                'n_long_licks': div['n_long_licks'],
                                'max_lick_duration': div['max_lick_duration'],
                                'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                            })
                    else:
                        # Handle case where no burst divisions could be created (e.g., no bursts)
                        for i in range(division_number):
                            division_rows.append({
                                'id': f"{animal_id}_B{i+1}" if animal_id else f"B{i+1}",
                                'source_filename': f"{source_filename} (Bursts {i+1}/{division_number} - no bursts found)" if source_filename else f"Bursts {i+1}/{division_number} (no bursts found)",
                                'start_time': 0,
                                'end_time': 0,
                                'duration': 0,
                                'interburst_interval': ibi,
                                'min_burst_size': minlicks,
                                'longlick_threshold': longlick_th,
                                'total_licks': 0,
                                'intraburst_freq': 0,
                                'n_bursts': 0,
                                'mean_licks_per_burst': 0,
                                'weibull_alpha': 0,
                                'weibull_beta': 0,
                                'weibull_rsq': 0,
                                'n_long_licks': 0,
                                'max_lick_duration': 0,
                                'long_licks_removed': 'Yes' if (remove_long and offset_times) else 'No'
                            })
            
            # Add all division rows to existing data
            updated_data = existing_data.copy() if existing_data else []
            updated_data.extend(division_rows)
            
            status_msg = dbc.Alert(
                f"✅ Added {len(division_rows)} divided results for {animal_id} to table",
                color="success",
                dismissable=True,
                duration=3000
            )
            
            return updated_data, status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Failed to add results: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return existing_data, error_msg

# Update table display with statistics
@app.callback(Output('results-table', 'data'),
              Input('results-table-store', 'data'))
def update_results_table(stored_data):
    """Update the displayed table with stored data plus statistics"""
    if not stored_data:
        # Return placeholder empty rows to make the table look more complete
        empty_rows = []
        for i in range(5):  # Add 5 empty placeholder rows
            empty_row = {
                'id': '',
                'source_filename': '',
                'start_time': None,
                'end_time': None,
                'duration': None,
                'interburst_interval': None,
                'min_burst_size': None,
                'longlick_threshold': None,
                'total_licks': None,
                'intraburst_freq': None,
                'n_bursts': None,
                'mean_licks_per_burst': None,
                'weibull_alpha': None,
                'weibull_beta': None,
                'weibull_rsq': None,
                'n_long_licks': None,
                'max_lick_duration': None
            }
            empty_rows.append(empty_row)
        return empty_rows
    
    # Create copy of data
    table_data = stored_data.copy()
    
    # Calculate statistics (ignoring NaN values)
    if len(table_data) > 1:  # Only add stats if there's more than one row
        numeric_columns = ['duration', 'total_licks', 'intraburst_freq', 'n_bursts', 'mean_licks_per_burst', 
                          'weibull_alpha', 'weibull_beta', 'weibull_rsq', 'n_long_licks', 'max_lick_duration']
        
        # Convert data to DataFrame for easier calculation
        df = pd.DataFrame(table_data)
        
        # Calculate statistics
        stats_rows = []
        
        # Sum (for appropriate columns)
        sum_row = {'id': 'Sum', 'source_filename': ''}
        # Only sum certain columns that make sense to sum
        summable_columns = ['duration', 'total_licks', 'n_bursts', 'n_long_licks']
        for col in numeric_columns:
            if col in summable_columns:
                sum_row[col] = df[col].sum() if not df[col].isna().all() else None
            else:
                sum_row[col] = None  # Don't sum rates, ratios, or other derived metrics
        stats_rows.append(sum_row)
        
        # Mean
        mean_row = {'id': 'Mean', 'source_filename': ''}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                mean_val = values.mean()
                mean_row[col] = mean_val if not pd.isna(mean_val) else np.nan
        stats_rows.append(mean_row)
        
        # Standard Deviation
        sd_row = {'id': 'SD', 'source_filename': ''}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                sd_val = values.std()
                sd_row[col] = sd_val if not pd.isna(sd_val) else np.nan
        stats_rows.append(sd_row)
        
        # N (count of non-NaN values)
        n_row = {'id': 'N', 'source_filename': ''}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                n_val = values.count()
                n_row[col] = n_val
        stats_rows.append(n_row)
        
        # Standard Error
        se_row = {'id': 'SE', 'source_filename': ''}
        for col in numeric_columns:
            if col in df.columns:
                values = pd.to_numeric(df[col], errors='coerce')
                sd_val = values.std()
                n_val = values.count()
                se_val = sd_val / np.sqrt(n_val) if n_val > 0 and not pd.isna(sd_val) else np.nan
                se_row[col] = se_val if not pd.isna(se_val) else np.nan
        stats_rows.append(se_row)
        
        # Add separator and stats
        table_data.extend(stats_rows)
    
    return table_data

# Delete selected row
@app.callback(Output('results-table-store', 'data', allow_duplicate=True),
              Output('table-status', 'children', allow_duplicate=True),
              Input('delete-row-btn', 'n_clicks'),
              State('results-table', 'selected_rows'),
              State('results-table-store', 'data'),
              prevent_initial_call=True)
def delete_selected_row(n_clicks, selected_rows, stored_data):
    """Delete selected row from the results table"""
    if n_clicks == 0 or not selected_rows or not stored_data:
        raise PreventUpdate
    
    try:
        selected_idx = selected_rows[0]
        
        # Don't allow deletion of statistics rows
        if selected_idx >= len(stored_data):
            error_msg = dbc.Alert(
                "❌ Cannot delete statistics rows",
                color="warning",
                dismissable=True,
                duration=3000
            )
            return stored_data, error_msg
        
        # Remove the selected row
        updated_data = stored_data.copy()
        deleted_id = updated_data[selected_idx].get('id', 'Unknown')
        del updated_data[selected_idx]
        
        status_msg = dbc.Alert(
            f"✅ Deleted row for {deleted_id}",
            color="info",
            dismissable=True,
            duration=3000
        )
        
        return updated_data, status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Failed to delete row: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return stored_data, error_msg

# Clear all results
@app.callback(Output('results-table-store', 'data', allow_duplicate=True),
              Output('table-status', 'children', allow_duplicate=True),
              Input('clear-all-btn', 'n_clicks'),
              prevent_initial_call=True)
def clear_all_results(n_clicks):
    """Clear all results from the table"""
    if n_clicks == 0:
        raise PreventUpdate
    
    status_msg = dbc.Alert(
        "✅ All results cleared from table",
        color="info",
        dismissable=True,
        duration=3000
    )
    
    return [], status_msg

# Export selected row
@app.callback(Output("download-table", "data"),
              Output('table-status', 'children', allow_duplicate=True),
              Input('export-row-btn', 'n_clicks'),
              Input('export-table-btn', 'n_clicks'),
              State('results-table', 'selected_rows'),
              State('results-table-store', 'data'),
              prevent_initial_call=True)
def export_table_data(export_row_clicks, export_table_clicks, selected_rows, stored_data):
    """Export selected row or full table to Excel"""
    ctx = dash.callback_context
    if not ctx.triggered or not stored_data:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if button_id == 'export-row-btn':
            if not selected_rows:
                error_msg = dbc.Alert(
                    "❌ Please select a row to export",
                    color="warning",
                    dismissable=True,
                    duration=3000
                )
                return None, error_msg
            
            selected_idx = selected_rows[0]
            if selected_idx >= len(stored_data):
                error_msg = dbc.Alert(
                    "❌ Cannot export statistics rows individually",
                    color="warning",
                    dismissable=True,
                    duration=3000
                )
                return None, error_msg
            
            # Export single row
            export_data = [stored_data[selected_idx]]
            row_id = export_data[0].get('id', 'Unknown')
            filename = f"lickcalc_SingleRow_{row_id}_{timestamp}.xlsx"
            success_msg = f"✅ Exported row for {row_id}"
            
        else:  # export-table-btn
            # Export full table
            export_data = stored_data.copy()
            filename = f"lickcalc_ResultsTable_{timestamp}.xlsx"
            success_msg = f"✅ Exported full table ({len(stored_data)} rows)"
        
        # Create Excel file
        df = pd.DataFrame(export_data)
        
        # Create a BytesIO buffer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Results', index=False)
        
        output.seek(0)
        excel_data = output.getvalue()
        
        status_msg = dbc.Alert(
            success_msg,
            color="success",
            dismissable=True,
            duration=4000
        )
        
        return dcc.send_bytes(excel_data, filename), status_msg
        
    except Exception as e:
        error_msg = dbc.Alert(
            f"❌ Export failed: {str(e)}",
            color="danger",
            dismissable=True,
            duration=4000
        )
        return None, error_msg
