"""
Validation utilities for lickcalc webapp.
Functions to validate onset times, offset times, and their relationships.
"""

def validate_onset_times(onset_times):
    """
    Validate that onset times are monotonically increasing.
    
    Parameters:
        onset_times (list): List of onset timestamps
        
    Returns:
        dict: Contains 'valid', 'message', 'first_violation_index'
    """
    if not onset_times or len(onset_times) <= 1:
        return {
            'valid': True,
            'message': "No or single onset time - no validation needed",
            'first_violation_index': None
        }
    
    for i in range(1, len(onset_times)):
        if onset_times[i] <= onset_times[i-1]:
            return {
                'valid': False,
                'message': f"Onset times are not monotonically increasing. At position {i+1}: {onset_times[i]:.3f}s is not greater than previous time {onset_times[i-1]:.3f}s. This suggests the file format doesn't match the selected file type.",
                'first_violation_index': i
            }
    
    return {
        'valid': True,
        'message': f"Onset times are properly ordered ({len(onset_times)} timestamps)",
        'first_violation_index': None
    }


def validate_onset_offset_pairs(onset_times, offset_times):
    """
    Validate that onset and offset times form proper lick pairs.
    
    Parameters:
        onset_times (list): List of lick onset timestamps
        offset_times (list): List of lick offset timestamps
        
    Returns:
        dict: Contains 'valid', 'message', 'corrected_onset', 'corrected_offset'
    """
    if not onset_times or not offset_times:
        return {
            'valid': False,
            'message': "Empty onset or offset data",
            'corrected_onset': onset_times,
            'corrected_offset': offset_times
        }
    
    original_onset_len = len(onset_times)
    original_offset_len = len(offset_times)
    
    # Make copies for potential correction
    corrected_onset = onset_times.copy()
    corrected_offset = offset_times.copy()
    
    # Handle length mismatches first
    if abs(len(corrected_onset) - len(corrected_offset)) > 1:
        return {
            'valid': False,
            'message': f"Severe length mismatch: {original_onset_len} onsets vs {original_offset_len} offsets. Arrays differ by more than 1.",
            'corrected_onset': corrected_onset,
            'corrected_offset': corrected_offset
        }
    
    # Handle length difference of 1
    if len(corrected_onset) - len(corrected_offset) == 1:
        # One more onset than offset - remove last onset
        corrected_onset = corrected_onset[:-1]
    elif len(corrected_offset) - len(corrected_onset) == 1:
        # One more offset than onset - remove last offset
        corrected_offset = corrected_offset[:-1]
    
    # Now check temporal order
    warnings = []
    errors = []
    
    for i in range(len(corrected_onset)):
        onset_time = corrected_onset[i]
        offset_time = corrected_offset[i]
        
        # Check if offset comes after onset
        if offset_time <= onset_time:
            errors.append(f"Pair {i+1}: Offset ({offset_time:.3f}s) is not after onset ({onset_time:.3f}s)")
        
        # Check if this offset comes before next onset (no overlap)
        if i < len(corrected_onset) - 1:
            next_onset = corrected_onset[i + 1]
            if offset_time >= next_onset:
                warnings.append(f"Pair {i+1}: Offset ({offset_time:.3f}s) occurs after or at next onset ({next_onset:.3f}s)")
    
    # Determine overall validity
    if errors:
        return {
            'valid': False,
            'message': f"Temporal order errors found: {'; '.join(errors[:3])}{'...' if len(errors) > 3 else ''}",
            'corrected_onset': corrected_onset,
            'corrected_offset': corrected_offset
        }
    elif warnings:
        return {
            'valid': True,
            'message': f"Warning - overlapping licks detected: {'; '.join(warnings[:2])}{'...' if len(warnings) > 2 else ''}",
            'corrected_onset': corrected_onset,
            'corrected_offset': corrected_offset
        }
    else:
        length_msg = ""
        if original_onset_len != len(corrected_onset):
            length_msg = f" (adjusted from {original_onset_len} to {len(corrected_onset)} onsets)"
        elif original_offset_len != len(corrected_offset):
            length_msg = f" (adjusted from {original_offset_len} to {len(corrected_offset)} offsets)"
            
        return {
            'valid': True,
            'message': f"Valid onset/offset pairs{length_msg}",
            'corrected_onset': corrected_onset,
            'corrected_offset': corrected_offset
        }
