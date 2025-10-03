# lickcalc Configuration System

The lickcalc webapp now supports customizable default values through a `config.yaml` file. This allows you to set default slider values, UI preferences, and analysis parameters without modifying the source code.

## Quick Start

1. **Use Default Configuration**: The app works out-of-the-box with sensible defaults
2. **Customize Settings**: Copy `config.yaml` and modify values as needed
3. **Advanced Customization**: See `config_custom_example.yaml` for all available options

## Configuration File Structure

### Session Analysis Settings
```yaml
session:
  bin_size: 30        # Default histogram bin size (seconds)
  fig_type: 'hist'    # Default plot type: 'hist' or 'cumul'
```

### Microstructural Analysis Settings
```yaml
microstructure:
  interburst_interval: 0.5     # Inter-burst interval threshold (seconds)
  min_licks_per_burst: 1       # Minimum licks per burst
  long_lick_threshold: 0.3     # Long lick duration threshold (seconds)
```

### File Processing Settings
```yaml
files:
  default_file_type: 'med'     # Default file type: 'med', 'csv', or 'dd'
```

### UI Configuration
```yaml
ui:
  title: 'lickcalc'           # Application window title
  debug: true                 # Enable debug mode
  hot_reload: true            # Enable hot reload for development
```

### Advanced Analysis Parameters
```yaml
analysis:
  # Session bin slider settings
  max_session_bins: 300
  min_session_bins: 5
  session_bin_step: 5
  
  # Inter-burst interval slider settings
  max_interburst_interval: 3.0
  min_interburst_interval: 0.0
  interburst_step: 0.25
  
  # Long lick threshold slider settings
  max_long_lick_threshold: 1.0
  min_long_lick_threshold: 0.1
  long_lick_step: 0.1
```

## Usage Examples

### Example 1: Different Species Settings
For analyzing data from a different species with longer inter-burst intervals:

```yaml
microstructure:
  interburst_interval: 1.0     # Increase threshold for species with longer pauses
  min_licks_per_burst: 2       # Require more licks per burst
```

### Example 2: Long Session Analysis
For 24-hour recordings requiring larger time bins:

```yaml
session:
  bin_size: 300               # 5-minute bins instead of 30-second bins

analysis:
  max_session_bins: 1440      # Allow up to 1440 bins (24 hours in minutes)
  session_bin_step: 60        # 1-minute step increments
```

### Example 3: Production Deployment
For deployed applications in a research lab:

```yaml
ui:
  title: 'Lab Name - lickcalc Analysis'
  debug: false                # Disable debug mode
  hot_reload: false          # Disable hot reload

files:
  default_file_type: 'csv'    # If your lab primarily uses CSV files
```

## File Location and Loading

1. **Default Config**: Place `config.yaml` in the same directory as `app.py`
2. **Custom Config**: The app automatically loads `config.yaml` if it exists
3. **Fallback**: If no config file is found, sensible defaults are used
4. **Error Handling**: Malformed YAML files will trigger fallback to defaults

## Testing Configuration

Run the test script to verify your configuration:

```bash
python test_config.py
```

This will show you the loaded configuration values and verify everything is working correctly.

## Common Customizations

### For Different Research Labs
- Change `ui.title` to include your lab name
- Adjust `microstructure` defaults based on your typical experimental parameters
- Set `files.default_file_type` to match your primary data format

### For Different Species
- Modify `interburst_interval` based on species-specific licking patterns
- Adjust `long_lick_threshold` for different tongue contact durations
- Change slider ranges in `analysis` section for species with different temporal patterns

### For Different Experimental Paradigms
- Increase `session.bin_size` for long-duration recordings
- Modify `min_licks_per_burst` based on your burst definition criteria
- Adjust slider step sizes for more precise parameter tuning

## Troubleshooting

### Configuration Not Loading
- Ensure `config.yaml` is in the same directory as `app.py`
- Check YAML syntax (indentation must be consistent)
- Run `python test_config.py` to diagnose issues

### Invalid Values
- All numeric values must be within reasonable ranges
- String values for `fig_type` must be 'hist' or 'cumul'
- String values for `default_file_type` must be 'med', 'csv', or 'dd'

### PyYAML Not Found
If you get import errors, install PyYAML:
```bash
pip install PyYAML
```

## Advanced Features

The configuration system supports:
- **Automatic fallbacks**: Missing values use sensible defaults
- **Validation**: Invalid values are replaced with defaults
- **Hot reloading**: Restart the app to load configuration changes
- **Environment-specific configs**: Use different config files for development vs. production