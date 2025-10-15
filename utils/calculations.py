"""
Calculation utilities for lickcalc webapp.
Functions for burst analysis, segment statistics, and lick data processing.
"""

import numpy as np
import logging

from trompy import lickcalc
from config_manager import config
from .validation import validate_onset_offset_pairs


def calculate_segment_stats(segment_licks, segment_offsets, ibi, minlicks, longlick_th, remove_long=False):
    """
    Calculate statistics for a segment of licks.
    
    Parameters:
        segment_licks (list): Lick onset times for this segment
        segment_offsets (list): Lick offset times for this segment (optional)
        ibi (float): Inter-burst interval threshold in seconds
        minlicks (int): Minimum number of licks per burst
        longlick_th (float): Long lick threshold in seconds
        remove_long (bool): Whether to remove long licks from analysis
        
    Returns:
        dict: Statistics including total licks, burst metrics, Weibull parameters, and lick durations
    """
    if not segment_licks:
        return {
            'total_licks': 0,
            'intraburst_freq': np.nan,
            'n_bursts': 0,
            'mean_licks_per_burst': np.nan,
            'weibull_alpha': np.nan,
            'weibull_beta': np.nan,
            'weibull_rsq': np.nan,
            'n_long_licks': np.nan,
            'max_lick_duration': np.nan
        }
    
    # Calculate basic burst statistics
    burst_lickdata = lickcalc(segment_licks, burstThreshold=ibi, minburstlength=minlicks, remove_longlicks=remove_long)
    
    # Check minimum burst threshold for Weibull parameters
    min_bursts_required = config.get('analysis.min_bursts_for_weibull', 10)
    num_bursts = burst_lickdata['bNum']
    
    stats = {
        'total_licks': burst_lickdata['total'],
        'intraburst_freq': burst_lickdata['freq'],
        'n_bursts': burst_lickdata['bNum'],
        'mean_licks_per_burst': burst_lickdata['bMean'],
        'weibull_alpha': burst_lickdata['weib_alpha'] if (burst_lickdata['weib_alpha'] is not None and num_bursts >= min_bursts_required) else np.nan,
        'weibull_beta': burst_lickdata['weib_beta'] if (burst_lickdata['weib_beta'] is not None and num_bursts >= min_bursts_required) else np.nan,
        'weibull_rsq': burst_lickdata['weib_rsq'] if (burst_lickdata['weib_rsq'] is not None and num_bursts >= min_bursts_required) else np.nan,
        'n_long_licks': np.nan,
        'max_lick_duration': np.nan
    }
    
    # Calculate long lick statistics if offset data available
    if segment_offsets:
        # Validate onset/offset pairs for this segment
        validation = validate_onset_offset_pairs(segment_licks, segment_offsets)
        
        if validation['valid']:
            try:
                # Use validated arrays
                validated_onsets = validation['corrected_onset']
                validated_offsets = validation['corrected_offset']
                
                lickdata_with_offset = lickcalc(validated_onsets, offset=validated_offsets, longlickThreshold=longlick_th)
                licklength = lickdata_with_offset["licklength"]
                stats['n_long_licks'] = len(lickdata_with_offset["longlicks"])
                stats['max_lick_duration'] = np.max(licklength) if len(licklength) > 0 else np.nan
                
                # Log validation warnings for segments
                if "Warning" in validation['message']:
                    logging.debug(f"Segment validation warning: {validation['message']}")
                    
            except (ValueError, TypeError, KeyError) as e:
                logging.warning(f"Could not calculate lick durations for burst range: {e}")
        else:
            logging.warning(f"Segment onset/offset validation failed: {validation['message']}")
            # Leave as NaN to indicate validation failure
    
    return stats


def get_licks_for_burst_range(lick_times, start_burst, end_burst, ibi, minlicks, remove_long=False):
    """
    Get lick times that belong to a specific range of bursts.
    
    Parameters:
        lick_times (list): All lick onset times
        start_burst (int): Starting burst index (inclusive)
        end_burst (int): Ending burst index (exclusive)
        ibi (float): Inter-burst interval threshold in seconds
        minlicks (int): Minimum number of licks per burst
        remove_long (bool): Whether to remove long licks
        
    Returns:
        list: Lick times that fall within the specified burst range
    """
    if not lick_times or start_burst >= end_burst:
        return []
    
    # Calculate bursts for the whole session first
    burst_lickdata = lickcalc(lick_times, burstThreshold=ibi, minburstlength=minlicks, remove_longlicks=remove_long)
    total_bursts = burst_lickdata.get('bNum', 0)
    
    if total_bursts == 0:
        # No bursts detected, fall back to time-based division
        session_duration = lick_times[-1] - lick_times[0] if len(lick_times) > 1 else 0
        if session_duration == 0:
            return lick_times if start_burst == 0 else []
            
        # Simple time-based fallback
        start_proportion = start_burst / max(end_burst, 1)
        end_proportion = end_burst / max(end_burst, 1)
        start_time = lick_times[0] + start_proportion * session_duration
        end_time = lick_times[0] + end_proportion * session_duration
        
        return [t for t in lick_times if start_time <= t < end_time]
    
    # We have bursts - extract them properly
    # The key insight: re-run lickcalc on the full data to get clean burst boundaries
    # Then extract the licks that belong to our target burst range
    
    # Ensure valid burst range
    start_burst = max(0, min(start_burst, total_bursts))
    end_burst = max(start_burst, min(end_burst, total_bursts))
    
    if start_burst == end_burst:
        return []
    
    # Get burst start times from the burst analysis
    burst_start_times = burst_lickdata.get('bStart', [])
    burst_end_times = burst_lickdata.get('bEnd', [])
    
    if not burst_start_times or not burst_end_times:
        # Fallback to proportional time-based approach
        start_proportion = start_burst / total_bursts
        end_proportion = end_burst / total_bursts
        session_duration = lick_times[-1] - lick_times[0]
        start_time = lick_times[0] + start_proportion * session_duration
        end_time = lick_times[0] + end_proportion * session_duration
        return [t for t in lick_times if start_time <= t <= end_time]
    
    # Extract the time boundaries for our burst range
    if start_burst < len(burst_start_times):
        range_start_time = float(burst_start_times[start_burst])
    else:
        range_start_time = lick_times[0]
    
    if end_burst - 1 < len(burst_end_times):
        range_end_time = float(burst_end_times[end_burst - 1])
    else:
        range_end_time = lick_times[-1]
    
    # Return licks within this time range
    return [t for t in lick_times if range_start_time <= t <= range_end_time]


def get_offsets_for_licks(original_licks, original_offsets, segment_licks):
    """
    Get corresponding offset times for a segment of licks.
    
    Parameters:
        original_licks (list): Complete list of lick onset times
        original_offsets (list): Complete list of lick offset times
        segment_licks (list): Subset of lick onset times
        
    Returns:
        list or None: Corresponding offset times for the segment licks, or None if not available
    """
    if not original_offsets or not segment_licks:
        return None
    
    # Find indices of segment licks in original lick list
    segment_indices = []
    for seg_lick in segment_licks:
        try:
            idx = original_licks.index(seg_lick)
            segment_indices.append(idx)
        except ValueError:
            continue
    
    # Return corresponding offsets
    if segment_indices and len(original_offsets) > max(segment_indices):
        return [original_offsets[i] for i in segment_indices if i < len(original_offsets)]
    
    return None
