# Lickcalc Webapp - Code Refactoring Guide

## ✅ What's Been Done

I've started refactoring your large `app.py` file into smaller, more manageable modules:

### Created Directories
```
lickcalc_webapp/
├── utils/              ✅ Created
│   ├── __init__.py     ✅ Created  
│   ├── validation.py   ✅ Created (2 functions)
│   └── calculations.py ✅ Created (3 functions)
└── callbacks/          ✅ Created
    └── __init__.py     (Pending)
```

### Extracted Functions

#### `utils/validation.py` (140 lines)
- `validate_onset_times(onset_times)` - Validates monotonic increasing onset times
- `validate_onset_offset_pairs(onset_times, offset_times)` - Validates onset/offset pairing

#### `utils/calculations.py` (215 lines)
- `calculate_segment_stats(...)` - Calculates stats for lick segments  
- `get_licks_for_burst_range(...)` - Extracts licks for burst range
- `get_offsets_for_licks(...)` - Gets corresponding offsets for lick subset

---

## 🎯 Next Steps (When You're Ready)

### Phase 1: Update app.py to use utility functions

Replace the function definitions in `app.py` with imports:

```python
# At the top of app.py, add:
from utils import (
    calculate_segment_stats,
    get_licks_for_burst_range,
    get_offsets_for_licks,
    validate_onset_times,
    validate_onset_offset_pairs
)
```

Then **delete** the original function definitions from `app.py`:
- Lines ~1528-1642: `validate_onset_times` and `validate_onset_offset_pairs`
- Lines ~2287-2427: `calculate_segment_stats`, `get_licks_for_burst_range`, `get_offsets_for_licks`

**Test** that the app still works after this change.

---

### Phase 2: Extract Callbacks (Optional - for future)

Once the utilities are working, you can extract callbacks into separate modules:

#### Suggested callback groups:

1. **`callbacks/config_callbacks.py`** - Configuration and slider updates
   - `load_config`
   - `update_session_length_seconds`
   - `convert_display_value_on_unit_change`
   - `update_bin_slider_range`
   - `convert_bin_slider_to_seconds`

2. **`callbacks/data_callbacks.py`** - Data loading and validation
   - `load_and_clean_data`
   - `clear_dependent_stores_on_new_file`
   - `update_validation_status`
   - `get_lick_data`
   - `toggle_dropdown_visibility`
   - `toggle_longlick_controls_visibility`

3. **`callbacks/graph_callbacks.py`** - Graph generation
   - `make_session_graph`
   - `update_session_length_suggestion`
   - `make_intraburstfreq_graph`
   - `make_longlicks_graph`
   - `make_bursthist_graph`
   - `make_burstprob_graph`
   - `collect_figure_data`
   - `update_display_values`

4. **`callbacks/export_callbacks.py`** - Data export
   - `export_to_excel`
   - `add_to_results_table`
   - `update_results_table`
   - `delete_selected_row`
   - `clear_all_results`
   - `export_table_data`

---

## 📋 Benefits of This Refactoring

### Before (Current):
- ❌ 3220 lines in one file
- ❌ Hard to find specific functions
- ❌ Difficult to test individual components
- ❌ Merge conflicts when collaborating

### After (Proposed):
- ✅ ~50 line main `app.py` file
- ✅ Logical grouping by functionality
- ✅ Easier to write unit tests
- ✅ Multiple people can work on different modules
- ✅ Easier to maintain and debug

---

## 🧪 Testing Checklist

After Phase 1 (using utility modules):
- [ ] App starts without errors
- [ ] File upload works
- [ ] Validation messages appear correctly
- [ ] All graphs generate properly
- [ ] Excel export works
- [ ] Results table functions correctly

---

## 📝 Notes

- **No functionality changes** - This is pure refactoring
- **Backwards compatible** - Same inputs/outputs for all functions
- **Gradual migration** - Can be done in phases
- **Easy rollback** - Original `app.py` is preserved until you're satisfied

---

## 🚀 Quick Start (Phase 1)

1. **Add import** at top of `app.py`:
   ```python
   from utils import (
       calculate_segment_stats,
       get_licks_for_burst_range,
       get_offsets_for_licks,
       validate_onset_times,
       validate_onset_offset_pairs
   )
   ```

2. **Delete** the 5 function definitions from `app.py`

3. **Test** your app - everything should work exactly the same!

---

## 📚 Resources

- See `REFACTORING_PLAN.md` for full detailed plan
- See `utils/__init__.py` for exported functions
- Original `app.py` is unchanged until you decide to proceed

---

**Questions?** The refactoring is optional and can be done at your own pace. The utility modules are ready to use whenever you want!
