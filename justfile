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

# ── Quarters (Q1=Feb–Apr, Q2=May–Jul, Q3=Aug–Oct, Q4=Nov–Jan) ──────────────

# Q1 (Feb–Apr): just q1 2026
q1 year:
    {{python}} --dir {{dir}} process-month --year {{year}} --month 2,3,4

# Q2 (May–Jul): just q2 2026
q2 year:
    {{python}} --dir {{dir}} process-month --year {{year}} --month 5,6,7

# Q3 (Aug–Oct): just q3 2026
q3 year:
    {{python}} --dir {{dir}} process-month --year {{year}} --month 8,9,10

# Q4 (Nov–Dec of year, Jan of year+1): just q4 2026
q4 year:
    #!/usr/bin/env bash
    next=$(( {{year}} + 1 ))
    {{python}} --dir {{dir}} process-months --months {{year}}-11,{{year}}-12,${next}-01

# ── Target: how many remaining days must be office ───────────────────────────

# Show how many remaining days must be in the office to hit target%
# just target 2026 2,3,4 50
target year month_list pct="50":
    {{python}} --dir {{dir}} target --year {{year}} --month {{month_list}} --target {{pct}}

# Target for Q1 (Feb–Apr): just q1-target 2026 [pct]
q1-target year pct="50":
    {{python}} --dir {{dir}} target --year {{year}} --month 2,3,4 --target {{pct}}

# Target for Q2 (May–Jul): just q2-target 2026 [pct]
q2-target year pct="50":
    {{python}} --dir {{dir}} target --year {{year}} --month 5,6,7 --target {{pct}}

# Target for Q3 (Aug–Oct): just q3-target 2026 [pct]
q3-target year pct="50":
    {{python}} --dir {{dir}} target --year {{year}} --month 8,9,10 --target {{pct}}

# Target for Q4 (Nov–Dec of year, Jan of year+1): just q4-target 2026 [pct]
q4-target year pct="50":
    #!/usr/bin/env bash
    next=$(( {{year}} + 1 ))
    {{python}} --dir {{dir}} target-range --months {{year}}-11,{{year}}-12,${next}-01 --target {{pct}}
