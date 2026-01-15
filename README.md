# Office Time Tracker

A simple command-line tool to track your office presence and calculate the percentage of time spent working from the office vs. remotely.

## Overview

This tool helps you maintain monthly records of your work location (office, remote, or holiday) and calculates statistics about your office presence. It uses plain text files for easy tracking and version control.

## Features

- 📅 **Monthly tracking**: Create and manage month-by-month records
- ✅ **Validation**: Ensures data integrity with comprehensive error checking
- 📊 **Statistics**: Calculate office percentage based on office vs. remote days
- 🎯 **Simple format**: Uses plain text files with ISO date format
- 🔒 **Data validation**: Prevents duplicates, missing days, and invalid statuses

## Installation

No installation required! Just ensure you have Python 3.7+ installed:

```bash
python3 --version
```

Make the script executable (optional):

```bash
chmod +x main.py
```

## Quick Start with Example Data

The repository includes example data files in the `office_days_records/` directory that you can use to understand how the tool works without creating your own data first.

**Try these commands with the example data:**

```bash
# View a single month
python3 main.py --dir office_days_records process-month --year 2026 --month 1

# View multiple months (same year)
python3 main.py --dir office_days_records process-month --year 2026 --month 1,2

# View cross-year quarter
python3 main.py --dir office_days_records process-months --months 2025-11,2025-12,2026-01

# View Q4 aggregate
python3 main.py --dir office_days_records process-months --months 2025-11,2025-12,2026-01
```

The example files demonstrate:
- Automatic weekend marking as holidays
- Random office/remote distribution for weekdays
- How aggregate calculations work across multiple months
- Cross-year quarter processing

## Usage

### 1. Initialize a Month File

Create a new month file with all days pre-populated:

```bash
python3 main.py init-month --year 2026 --month 1
```

This creates a file `office_months/2026-01.txt` with entries like:

```
2026-01-01
2026-01-02
2026-01-03
2026-01-04 holiday
2026-01-05 holiday
2026-01-06
...
2026-01-31
```

**Note:** Weekends (Saturdays and Sundays) are automatically marked as `holiday` to save you time. You only need to fill in weekdays.

### 2. Fill in Your Status

Edit the generated file and add your status for weekdays (weekends are already marked as `holiday`):

```
2026-01-01 office
2026-01-02 office
2026-01-03 remote
2026-01-04 holiday
2026-01-05 holiday
2026-01-06 office
2026-01-07 remote
```

**Valid statuses:**
- `office` - Working from the office
- `remote` - Working remotely
- `holiday` - Day off/holiday/vacation

### 3. Process and Calculate Statistics

Calculate your office percentage for a single month (up to today):

```bash
python3 main.py process-month --year 2026 --month 1
```

**Example output:**

```
2026-01 (until today)
  office=10 remote=8 holiday=2
  office_pct = 10/18 = 55.6%
```

#### Process Multiple Months (Quarterly Average)

**For months within the same year:**

```bash
# Q1 2026 (February, March, April)
python3 main.py process-month --year 2026 --month 2,3,4
```

**For months spanning different years (e.g., Q4):**

```bash
# Q4 (December 2025, January 2026, February 2026)
python3 main.py process-months --months 2025-12,2026-01,2026-02
```

**Example output:**

```
2025-12
  office=12 remote=8 holiday=11
  office_pct = 12/20 = 60.0%

2026-01
  office=15 remote=10 holiday=6
  office_pct = 15/25 = 60.0%

2026-02
  office=11 remote=9 holiday=8
  office_pct = 11/20 = 55.0%

AGGREGATE (2025-12 to 2026-02)
  office=38 remote=27 holiday=25
  office_pct = 38/65 = 58.5%
```

## Command Reference

### `init-month`

Creates a new month file with all days pre-populated.

**Options:**
- `--year YEAR` (required): Year (e.g., 2026)
- `--month MONTH` (required): Month (1-12)
- `--dir DIR` (optional): Directory for month files (default: `office_months`)

**Example:**
```bash
python3 main.py init-month --year 2026 --month 3 --dir my_tracking
```

### `process-month`

Validates the month file(s) and calculates statistics up to today. Supports processing multiple months for aggregate calculations.

**Options:**
- `--year YEAR` (required): Year (e.g., 2026)
- `--month MONTH` (required): Month (1-12) or comma-separated months (e.g., 2,3,4)
- `--dir DIR` (optional): Directory for month files (default: `office_months`)

**Examples:**

Single month:
```bash
python3 main.py process-month --year 2026 --month 1
```

Multiple months (same year):
```bash
# Q1: February, March, April
python3 main.py process-month --year 2026 --month 2,3,4

# Q2: May, June, July
python3 main.py process-month --year 2026 --month 5,6,7
```

### `process-months`

Process multiple year-month pairs across different years. Perfect for quarters that span year boundaries.

**Options:**
- `--months MONTHS` (required): Comma-separated year-month pairs in YYYY-MM format
- `--dir DIR` (optional): Directory for month files (default: `office_months`)

**Examples:**

Cross-year quarter:
```bash
# Q4: December 2025, January 2026, February 2026
python3 main.py process-months --months 2025-12,2026-01,2026-02
```

Any custom range:
```bash
# Last 6 months of a project
python3 main.py process-months --months 2025-08,2025-09,2025-10,2025-11,2025-12,2026-01
```

## File Format

Month files use a simple text format:

```
YYYY-MM-DD [status]
```

- Each line represents one day
- Date must be in ISO format (YYYY-MM-DD)
- Status is optional for future dates but **required** for past dates
- Blank lines are ignored
- All days of the month must be present

**Example file (`2026-01.txt`):**

```
2026-01-01 holiday
2026-01-02 office
2026-01-03 office
2026-01-04 remote
2026-01-05 remote
2026-01-06
2026-01-07
...
```

## Validation Rules

The tool enforces several validation rules:

1. ✅ All dates must be valid ISO format
2. ✅ Status must be one of: `office`, `remote`, `holiday`
3. ✅ No duplicate date entries allowed
4. ✅ All days of the month must be present
5. ✅ No dates from other months allowed
6. ✅ Past dates (including today) must have a status filled in
7. ✅ Future dates can be left blank

## Calculation Logic

The office percentage is calculated as:

```
office_pct = (office_days / (office_days + remote_days)) × 100
```

**Notes:**
- Only counts days up to and including today
- Holiday days are excluded from the percentage calculation
- Future days (not yet filled) are ignored

## Examples

### Track a full month

```bash
# Initialize January 2026
python3 main.py init-month --year 2026 --month 1

# Edit the file: office_months/2026-01.txt
# Fill in your daily status

# Check your stats
python3 main.py process-month --year 2026 --month 1
```

### Custom directory

```bash
# Use a custom directory
python3 main.py init-month --year 2026 --month 2 --dir ~/work-tracking
python3 main.py process-month --year 2026 --month 2 --dir ~/work-tracking
```

### Calculate quarterly averages

**Same-year quarter (Q1 2026: Feb, Mar, Apr):**

```bash
# Initialize all months
python3 main.py init-month --year 2026 --month 2
python3 main.py init-month --year 2026 --month 3
python3 main.py init-month --year 2026 --month 4

# Fill in the data for each month...

# Calculate Q1 aggregate
python3 main.py process-month --year 2026 --month 2,3,4
```

**Cross-year quarter (Q4: Dec 2025, Jan 2026, Feb 2026):**

```bash
# Initialize all months
python3 main.py init-month --year 2025 --month 12
python3 main.py init-month --year 2026 --month 1
python3 main.py init-month --year 2026 --month 2

# Fill in the data for each month...

# Calculate Q4 aggregate
python3 main.py process-months --months 2025-12,2026-01,2026-02
```

**Common quarters:**
- Q1 (same year): `process-month --year 2026 --month 2,3,4` (Feb, Mar, Apr)
- Q2 (same year): `process-month --year 2026 --month 5,6,7` (May, Jun, Jul)
- Q3 (same year): `process-month --year 2026 --month 8,9,10` (Aug, Sep, Oct)
- Q4 (cross-year): `process-months --months 2025-11,2025-12,2026-01` (Nov, Dec, Jan)

## Error Messages

The tool provides clear error messages for common issues:

- **"File already exists"**: Month file was already initialized
- **"Month file not found"**: Run `init-month` first
- **"Invalid status"**: Use only `office`, `remote`, or `holiday`
- **"Unfilled status for past day"**: All past dates must have a status
- **"Duplicate date entry"**: Each date should appear only once
- **"Missing day lines"**: All days of the month must be present

## Tips

- 📝 Keep your month files in version control (Git) to track changes over time
- 🔄 Update your status daily or weekly to avoid forgetting
- 📊 Run `process-month` regularly to monitor your office percentage
- 🗂️ Use the default `office_months` directory for easy organization
- 🎯 Weekends are automatically marked as `holiday` when you initialize a month - you only need to fill in weekdays!
- 📈 Use comma-separated months (e.g., `--month 2,3,4`) to calculate quarterly averages

## Requirements

- Python 3.7 or higher
- No external dependencies (uses only standard library)

## License

This is a simple utility script. Feel free to modify and use as needed.
