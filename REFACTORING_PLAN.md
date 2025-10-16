# App Refactoring Plan

## Current Structure
- `app.py` (3220 lines) - Everything in one file
- `config_manager.py` - Configuration management ✅
- `helperfx.py` - Helper functions ✅
- `layout.py` - Layout definitions ✅

## Proposed Structure

### 1. Core Application Files
```
app.py (NEW - minimal, ~50 lines)
├── Import app instance
├── Import all callbacks
└── Run server
```

### 2. Utilities (`utils/`)
```
utils/
├── __init__.py
├── calculations.py
│   ├── calculate_segment_stats()
│   ├── get_licks_for_burst_range()
│   └── get_offsets_for_licks()
└── validation.py
    ├── validate_onset_times()
    └── validate_onset_offset_pairs()
```

### 3. Callbacks (`callbacks/`)
```
callbacks/
├── __init__.py
├── config_callbacks.py
│   ├── load_config()
│   ├── update_session_length_seconds()
│   ├── convert_display_value_on_unit_change()
│   ├── update_bin_slider_range()
│   └── convert_bin_slider_to_seconds()
├── data_callbacks.py
│   ├── load_and_clean_data()
│   ├── clear_dependent_stores_on_new_file()
│   ├── update_validation_status()
│   ├── get_lick_data()
│   ├── toggle_dropdown_visibility()
│   └── toggle_longlick_controls_visibility()
├── graph_callbacks.py
│   ├── make_session_graph()
│   ├── update_session_length_suggestion()
│   ├── make_intraburstfreq_graph()
│   ├── make_longlicks_graph()
│   ├── make_bursthist_graph()
│   ├── make_burstprob_graph()
│   ├── collect_figure_data()
│   └── update_display_values()
└── export_callbacks.py
    ├── export_to_excel()
    ├── add_to_results_table()
    ├── update_results_table()
    ├── delete_selected_row()
    ├── clear_all_results()
    └── export_table_data()
```

### 4. App Instance (`app_instance.py`)
```
app_instance.py
├── Create Dash app
├── Configure server
└── Import layout from layout.py
```

## Implementation Steps

### Step 1: Create utility modules (Non-breaking)
- [x] Create `utils/` directory
- [ ] Create `utils/calculations.py` with calculation functions
- [ ] Create `utils/validation.py` with validation functions
- [ ] Update `utils/__init__.py`

### Step 2: Create callback modules (Non-breaking)
- [x] Create `callbacks/` directory
- [ ] Create `callbacks/config_callbacks.py`
- [ ] Create `callbacks/data_callbacks.py`
- [ ] Create `callbacks/graph_callbacks.py`
- [ ] Create `callbacks/export_callbacks.py`
- [ ] Create `callbacks/__init__.py` to register all callbacks

### Step 3: Create app instance module
- [ ] Create `app_instance.py` with app creation
- [ ] Move app initialization from `app.py`

### Step 4: Refactor main app.py
- [ ] Keep only imports and server run
- [ ] Import callbacks to register them
- [ ] Test that everything still works

### Step 5: Testing
- [ ] Test file upload
- [ ] Test all graphs
- [ ] Test exports
- [ ] Test config loading

## Benefits
1. ✅ **Easier navigation** - Find code by functionality
2. ✅ **Better maintainability** - Smaller files are easier to understand
3. ✅ **Reusability** - Utility functions can be tested independently
4. ✅ **Collaboration** - Multiple people can work on different callback files
5. ✅ **Testing** - Easier to write unit tests for individual modules

## Notes
- Each callback module will import the app instance from `app_instance.py`
- Callbacks are registered when modules are imported
- The main `app.py` just needs to import all callback modules
- No changes to existing functionality - just reorganization
