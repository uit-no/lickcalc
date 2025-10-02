# LickCalc Data Output System

## Overview

The LickCalc webapp now includes a comprehensive data output system that allows you to export analysis results and underlying figure data to Excel files. This system is located in a dedicated section at the bottom of the interface.

## Features

### 1. **Animal ID Input**
- Text input field for specifying the animal/subject identifier
- Default value configurable in `config.yaml` (default: "ID1")
- Used in the exported filename and summary sheet

### 2. **Selective Data Export**
Choose which figure data to include in your Excel export:

- **✅ Session Histogram Data** - Time bins and lick counts from the session overview
- **✅ Intraburst Frequency Data** - Inter-lick interval bins and frequencies  
- **☐ Lick Lengths Data** - Lick duration data (requires offset times)
- **☐ Burst Histogram Data** - Burst size distribution data
- **☐ Burst Probability Data** - Weibull probability plot data

### 3. **Excel Export**
- **Multi-sheet Excel files** with organized data
- **Summary sheet** with all key statistics
- **Individual sheets** for selected figure data
- **Automatic filename generation** with timestamp
- **File browser** opens automatically for save location

## Excel File Structure

### Summary Sheet
Contains all the key analysis results:
- Animal ID and export timestamp
- Total licks count
- Intraburst frequency (Hz)
- Number of bursts
- Mean licks per burst
- Weibull distribution parameters (α, β, R²)
- Long lick statistics (if offset data available)

### Data Sheets (when selected)
1. **Session_Histogram** - Time bin centers and lick counts
2. **Intraburst_Frequency** - ILI bin centers and frequencies
3. **Lick_Lengths** - Duration bin centers and frequencies
4. **Burst_Histogram** - Burst sizes and frequencies
5. **Burst_Probability** - Burst sizes and survival probabilities

## Usage Instructions

### Basic Export
1. Load your lick data file
2. Adjust analysis parameters as needed
3. Scroll to the **Data Output** section at the bottom
4. Enter your animal ID (e.g., "Mouse_001")
5. Click **"Export Data to Excel"**
6. Choose save location in the file browser
7. Success/error message will appear

### Custom Data Selection
1. Uncheck data types you don't need
2. For lick lengths data, ensure you have offset times loaded
3. Export will only include checked data types
4. Summary sheet is always included

### Filename Format
Files are automatically named as:
```
LickCalc_Export_{AnimalID}_{YYYYMMDD_HHMMSS}.xlsx
```
Example: `LickCalc_Export_Mouse_001_20241002_143022.xlsx`

## Configuration

Add to your `config.yaml`:

```yaml
# Output configuration
output:
  # Default animal ID
  default_animal_id: 'ID1'
```

## Troubleshooting

### Export Failed Errors
- **"No data available"** - Load a data file first
- **"Excel export failed"** - Check that openpyxl is installed
- **"Permission denied"** - Close Excel if the file is already open

### Missing Data Sheets
- **Lick Lengths missing** - Requires offset time data (load onset+offset file)
- **Empty sheets** - Analysis parameters may have excluded all data

### Dependencies
Ensure you have the required packages:
```bash
pip install pandas openpyxl
```

## Tips for Research Use

### For Multiple Animals
1. Change the Animal ID for each export
2. Use consistent naming conventions (e.g., "Group1_Mouse01")
3. Export data immediately after analysis to avoid losing settings

### For Publication Data
1. Export all data types for complete records
2. Use the raw data sheets for custom statistical analysis
3. Summary sheet provides publication-ready statistics

### For Batch Processing
1. Set your preferred default animal ID in config.yaml
2. Select your commonly used data types as defaults
3. Use consistent analysis parameters across animals

## Data Quality Notes

- **Bin sizes** are preserved in the exported data
- **Raw values** are included where applicable for custom analysis
- **Analysis parameters** (thresholds, bin sizes) are reflected in the data
- **Timestamps** ensure traceability of when analysis was performed

## Integration with Analysis Workflow

The export system automatically:
1. **Captures current analysis state** - Uses whatever parameters are currently set
2. **Includes all relevant metadata** - Thresholds, bin sizes, timestamps
3. **Preserves data integrity** - Exports the exact data underlying the figures
4. **Maintains traceability** - Animal ID and timestamp for lab records

This system replaces the simple CSV output with a comprehensive, research-grade data export solution suitable for publication and detailed statistical analysis.