# Office Time Tracker
# Usage: just <recipe> [args...]

set dotenv-load  # export .env file before running any recipe

python := "python3 main.py"
dir    := env_var_or_default("OFFICE_TRACKER_DIR", "office_days_records")

# Show available recipes
default:
    @just --list

# Initialize a new month file: just init 2026 3
init year month:
    {{python}} --dir {{dir}} init-month --year {{year}} --month {{month}}

# Process a single month: just month 2026 3
month year month:
    {{python}} --dir {{dir}} process-month --year {{year}} --month {{month}}

# Process multiple months in same year: just months 2026 1,2,3
months year month_list:
    {{python}} --dir {{dir}} process-month --year {{year}} --month {{month_list}}

# Process cross-year month range: just range 2025-12,2026-01,2026-02
range month_pairs:
    {{python}} --dir {{dir}} process-months --months {{month_pairs}}

# Process current month
current:
    #!/usr/bin/env bash
    year=$(date +%Y)
    month=$(date +%-m)
    {{python}} --dir {{dir}} process-month --year $year --month $month

# Initialize current month file
init-current:
    #!/usr/bin/env bash
    year=$(date +%Y)
    month=$(date +%-m)
    {{python}} --dir {{dir}} init-month --year $year --month $month
