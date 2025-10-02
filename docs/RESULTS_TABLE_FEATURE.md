# Results Summary Table Feature

## Overview
A new **Results Summary Table** has been added at the bottom of the LickCalc webapp, after the Data Output section. This table allows you to collect, manage, and analyze results from multiple datasets.

## Features

### 📊 Results Collection
- **Add Current Results to Table** button: Captures all primary analysis parameters from the current analysis
- Automatically includes: ID, Total Licks, Intraburst Frequency, N Bursts, Mean Licks/Burst, Weibull parameters, Long Lick statistics
- Uses the Animal ID from the input field above

### ✏️ Data Management
- **Editable ID column**: Click on any ID cell to edit the animal identifier
- **Row selection**: Click on any row to select it for operations
- **Delete Selected Row**: Remove individual entries from the table
- **Visual highlighting**: Different background colors for data vs. statistics rows

### 📈 Automatic Statistics
The table automatically calculates and displays:
- **Mean**: Average of all values (NaN values ignored)
- **SD (Standard Deviation)**: Population standard deviation
- **N**: Count of non-NaN values for each column
- **SE (Standard Error)**: Standard deviation divided by square root of N

### 📋 Export Options
- **Export Selected Row**: Export a single selected row to Excel
- **Export Full Table**: Export the entire table including statistics to Excel
- Automatic timestamp-based filename generation
- Excel format with proper formatting

## Column Descriptions

| Column | Description | Format |
|--------|-------------|---------|
| ID | Animal/Subject identifier | Text (editable) |
| Total Licks | Total number of licks detected | Integer |
| Intraburst Freq (Hz) | Licking frequency within bursts | 3 decimal places |
| N Bursts | Number of burst events | Integer |
| Mean Licks/Burst | Average licks per burst | 2 decimal places |
| Weibull Alpha | Weibull distribution alpha parameter | 3 decimal places |
| Weibull Beta | Weibull distribution beta parameter | 3 decimal places |
| Weibull R² | Weibull fit R-squared value | 3 decimal places |
| N Long Licks | Number of long licks (requires offset data) | Integer |
| Max Lick Duration (s) | Maximum lick duration (requires offset data) | 4 decimal places |

## Usage Workflow

1. **Load and analyze data** using the standard LickCalc interface
2. **Set the Animal ID** in the Data Output section
3. **Click "Add Current Results to Table"** to capture the current analysis
4. **Repeat for additional datasets** - each will be added as a new row
5. **Edit IDs if needed** by clicking in the ID column
6. **Review statistics** automatically calculated at the bottom
7. **Export data** either by row or full table

## Visual Formatting

- **Standard data rows**: Alternating light gray background
- **Mean row**: Light blue background, bold text
- **SD row**: Light red background, bold text
- **SE row**: Light green background, bold text
- **N row**: Light orange background, bold text

## Error Handling

- **NaN values**: Automatically handled in statistical calculations
- **Missing data**: Shows as NaN in table, ignored in statistics
- **No offset data**: Long lick columns show NaN
- **Invalid selections**: Prevents deletion of statistics rows
- **Export errors**: Clear error messages with troubleshooting info

## Technical Implementation

- **Data storage**: Uses Dash Store component for persistence during session
- **Real-time updates**: Table automatically updates when data is added/removed
- **Statistics calculation**: Uses pandas for robust NaN-aware calculations
- **Excel export**: Uses openpyxl engine for reliable file generation
- **Responsive design**: Table scrolls horizontally on smaller screens

## Benefits

1. **Multi-subject analysis**: Easily compare results across multiple animals
2. **Statistical power**: Automatic calculation of group statistics
3. **Data persistence**: Results remain in table throughout session
4. **Export flexibility**: Choose individual subjects or full dataset
5. **Quality control**: Edit IDs and remove outliers as needed
6. **Professional output**: Clean Excel files ready for publication

This feature transforms LickCalc from a single-analysis tool into a comprehensive platform for group-level microstructure analysis!