"""
Calculation utilities for lickcalc webapp.
Functions for burst analysis, segment statistics, and lick data processing.
"""

import numpy as np
import logging

try:
    from trompy import lickcalc  # type: ignore[import]
except Exception:
    # Provide a clear error at runtime if trompy isn't installed, while avoiding import-time editor errors
    def lickcalc(*args, **kwargs):  # type: ignore
        raise ImportError("The 'trompy' package is required for lick calculations. Please install it (see requirements.txt).")
from config_manager import config
from .validation import validate_onset_offset_pairs


def calculate_mean_interburst_time(burst_starts, burst_ends):
    """
    Calculate mean interburst interval from burst start and end times.
    
    Interburst interval is defined as the time from the end of one burst 
    to the start of the next burst.
    
    Parameters:
        burst_starts (list or np.array): Start times of each burst
        burst_ends (list or np.array): End times of each burst
        
    Returns:
        float or None: Mean interburst interval in seconds, or None if < 2 bursts
    """
    if burst_starts is None or burst_ends is None:
        return None
    if len(burst_starts) < 2 or len(burst_ends) < 2:
        return None
    
    # Calculate interburst intervals
    ibis = []
    for i in range(len(burst_ends) - 1):
        ibi = burst_starts[i + 1] - burst_ends[i]
        ibis.append(ibi)
    
    return np.mean(ibis) if len(ibis) > 0 else None


def detect_trials(lick_times, min_iti):
    """
    Detect trials based on inter-lick intervals.
    
    Trials are detected by identifying gaps between licks that are >= min_iti.
    Each trial consists of licks from after one large gap to before the next large gap.
    
    Parameters:
        lick_times (list or np.array): Lick onset times in seconds
        min_iti (float): Minimum inter-trial interval in seconds
        
    Returns:
        dict: Dictionary containing:
            - 'n_trials': Number of trials detected
            - 'trial_boundaries': List of tuples (start_idx, end_idx) for each trial
            - 'trial_start_times': List of start times for each trial
            - 'trial_end_times': List of end times for each trial
    """
    if lick_times is None or len(lick_times) == 0:
        return {
            'n_trials': 0,
            'trial_boundaries': [],
            'trial_start_times': [],
            'trial_end_times': []
        }
    
    lick_times = np.array(lick_times)
    
    # Calculate inter-lick intervals
    ilis = np.diff(lick_times)
    
    # Find gaps >= min_iti (these are trial boundaries)
    trial_boundaries_idx = np.where(ilis >= min_iti)[0]
    
    # Build trial segments
    trial_boundaries = []
    trial_start_times = []
    trial_end_times = []
    
    if len(trial_boundaries_idx) == 0:
        # No large gaps found - entire session is one trial
        trial_boundaries.append((0, len(lick_times)))
        trial_start_times.append(float(lick_times[0]))
        trial_end_times.append(float(lick_times[-1]))
    else:
        # First trial: from start to first boundary
        start_idx = 0
        for boundary_idx in trial_boundaries_idx:
            end_idx = boundary_idx + 1  # Include the lick before the gap
            trial_boundaries.append((start_idx, end_idx))
            trial_start_times.append(float(lick_times[start_idx]))
            trial_end_times.append(float(lick_times[end_idx - 1]))
            start_idx = end_idx  # Start of next trial is after the gap
        
        # Last trial: from last boundary to end
        if start_idx < len(lick_times):
            trial_boundaries.append((start_idx, len(lick_times)))
            trial_start_times.append(float(lick_times[start_idx]))
            trial_end_times.append(float(lick_times[-1]))
    
    return {
        'n_trials': len(trial_boundaries),
        'trial_boundaries': trial_boundaries,
        'trial_start_times': trial_start_times,
        'trial_end_times': trial_end_times
    }


def analyze_trial(lick_times, lick_offsets, trial_idx, start_idx, end_idx, 
                  ibi, minlicks, longlick_th, remove_long=False, crop_last_burst=False):
    """
    Analyze a single trial.
    
    Parameters:
        lick_times (list): All lick onset times
        lick_offsets (list): All lick offset times (can be None)
        trial_idx (int): Trial number (for identification)
        start_idx (int): Starting index in lick_times for this trial
        end_idx (int): Ending index in lick_times for this trial
        ibi (float): Inter-burst interval threshold
        minlicks (int): Minimum licks per burst
        longlick_th (float): Long lick threshold
        remove_long (bool): Whether to remove long licks
        crop_last_burst (bool): Whether to exclude the last burst from analysis
        
    Returns:
        dict: Trial statistics
    """
    # Extract trial licks
    trial_licks = lick_times[start_idx:end_idx]
    trial_offsets = (
        lick_offsets[start_idx:end_idx]
        if (lick_offsets is not None and len(lick_offsets) > 0)
        else None
    )
    
    if trial_licks is None or len(trial_licks) == 0:
        return {
            'trial_number': trial_idx + 1,
            'start_time': np.nan,
            'end_time': np.nan,
            'duration': 0,
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
    
    # If crop_last_burst is enabled, identify and remove the last burst
    if crop_last_burst:
        # First, calculate bursts to identify them
        burst_data = lickcalc(trial_licks, burstThreshold=ibi, minburstlength=minlicks, remove_longlicks=remove_long)
        
        if burst_data['bNum'] > 1:  # Only crop if there's more than 1 burst
            burst_ends = burst_data.get('bEnd', [])
            if burst_ends is not None and len(burst_ends) > 0:
                # Find the end time of the second-to-last burst
                last_burst_start_time = float(burst_ends[-2]) if len(burst_ends) > 1 else float(burst_ends[0])
                
                # Keep only licks up to and including the second-to-last burst
                trial_licks = [t for t in trial_licks if t <= last_burst_start_time]
                if trial_offsets is not None:
                    trial_offsets = trial_offsets[:len(trial_licks)]
    
    # Calculate statistics for the trial
    stats = calculate_segment_stats(trial_licks, trial_offsets, ibi, minlicks, longlick_th, remove_long)
    
    # Add trial-specific information
    stats['trial_number'] = trial_idx + 1
    stats['start_time'] = float(trial_licks[0]) if len(trial_licks) > 0 else np.nan
    stats['end_time'] = float(trial_licks[-1]) if len(trial_licks) > 0 else np.nan
    stats['duration'] = float(trial_licks[-1] - trial_licks[0]) if len(trial_licks) > 1 else 0
    
    return stats


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
    if segment_licks is None or len(segment_licks) == 0:
        return {
            'total_licks': 0,
            'intraburst_freq': np.nan,
            'n_bursts': 0,
            'mean_licks_per_burst': np.nan,
            'mean_interburst_time': np.nan,
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
    
    # Get mean interburst time from lickcalc IBIs output
    ibis = burst_lickdata.get('IBIs', [])
    mean_ibi = np.mean(ibis) if ibis is not None and len(ibis) > 0 else np.nan
    
    stats = {
        'total_licks': burst_lickdata['total'],
        'intraburst_freq': burst_lickdata['freq'],
        'n_bursts': burst_lickdata['bNum'],
        'mean_licks_per_burst': burst_lickdata['bMean'],
        'mean_interburst_time': mean_ibi,
        'weibull_alpha': burst_lickdata['weib_alpha'] if (burst_lickdata['weib_alpha'] is not None and num_bursts >= min_bursts_required) else np.nan,
        'weibull_beta': burst_lickdata['weib_beta'] if (burst_lickdata['weib_beta'] is not None and num_bursts >= min_bursts_required) else np.nan,
        'weibull_rsq': burst_lickdata['weib_rsq'] if (burst_lickdata['weib_rsq'] is not None and num_bursts >= min_bursts_required) else np.nan,
        'n_long_licks': np.nan,
        'max_lick_duration': np.nan
    }
    
    # Calculate long lick statistics if offset data available
    if segment_offsets is not None and len(segment_offsets) > 0:
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
    if lick_times is None or len(lick_times) == 0 or start_burst >= end_burst:
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
    
    if (burst_start_times is None or len(burst_start_times) == 0) or (burst_end_times is None or len(burst_end_times) == 0):
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
    if original_offsets is None or len(original_offsets) == 0 or segment_licks is None or len(segment_licks) == 0:
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
