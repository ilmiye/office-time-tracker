#!/usr/bin/env python3
from __future__ import annotations

import argparse
import calendar
import math
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Tuple, Optional

VALID = {"holiday", "remote", "office"}


@dataclass(frozen=True)
class Row:
    day: date
    status: Optional[str]  # None means blank/unfilled


def month_file_path(base_dir: Path, y: int, m: int) -> Path:
    return base_dir / f"{y:04d}" / f"{y:04d}-{m:02d}.txt"


def generate_month_file(base_dir: Path, y: int, m: int) -> Path:
    p = month_file_path(base_dir, y, m)
    if p.exists():
        raise SystemExit(f"File already exists: {p}")

    p.parent.mkdir(parents=True, exist_ok=True)

    _, last_day = calendar.monthrange(y, m)
    lines = []
    for d in range(1, last_day + 1):
        day_date = date(y, m, d)
        # weekday() returns 5 for Saturday, 6 for Sunday
        if day_date.weekday() in (5, 6):
            lines.append(f"{y:04d}-{m:02d}-{d:02d} holiday\n")
        else:
            lines.append(f"{y:04d}-{m:02d}-{d:02d}\n")

    p.write_text("".join(lines), encoding="utf-8")
    return p


def parse_month_file(path: Path) -> Tuple[List[Row], List[str]]:
    errors: List[str] = []
    rows: List[Row] = []
    errored_dates: set = set()

    if not path.exists():
        raise SystemExit(f"Month file not found: {path}")

    text = path.read_text(encoding="utf-8").splitlines()

    for i, raw in enumerate(text, start=1):
        line = raw.strip()

        if not line:
            continue  # ignore blank lines entirely

        parts = line.split()

        # Expect: YYYY-MM-DD [status]
        if len(parts) > 2:
            errors.append(f"Line {i}: too many tokens: {raw!r}")
            continue

        ds = parts[0]
        try:
            d = date.fromisoformat(ds)
        except ValueError:
            errors.append(f"Line {i}: invalid date: {ds!r}")
            continue

        status = None
        if len(parts) == 2:
            status = parts[1].strip()
            if status not in VALID:
                errors.append(
                    f"Line {i}: invalid status {status!r}. Allowed: {sorted(VALID)}"
                )
                errored_dates.add(d)
                continue

        rows.append(Row(day=d, status=status))

    # Extra structural checks: duplicates, missing days
    seen = {}
    for r in rows:
        if r.day in seen:
            errors.append(f"Duplicate date entry: {r.day.isoformat()}")
        seen[r.day] = True

    # Ensure month coverage (every day appears)
    if rows:
        y = rows[0].day.year
        m = rows[0].day.month
        _, last_day = calendar.monthrange(y, m)
        expected = {date(y, m, d) for d in range(1, last_day + 1)}
        actual = {r.day for r in rows}
        missing = sorted(expected - actual - errored_dates)
        extra = sorted(actual - expected)
        if missing:
            errors.append(
                "Missing day lines: " + ", ".join(d.isoformat() for d in missing[:10]) +
                (" ..." if len(missing) > 10 else "")
            )
        if extra:
            errors.append(
                "Date(s) not in that month: " + ", ".join(d.isoformat() for d in extra)
            )

    return rows, errors


def compute_until_today(rows: List[Row]) -> Tuple[float, int, int, int]:
    """
    Returns: (pct, office_count, remote_count, holiday_count)
    pct = office / (office + remote) * 100
    """
    today = date.today()

    office = 0
    remote = 0
    holiday = 0

    for r in rows:
        if r.day > today:
            continue

        if r.status is None:
            # Past (or today) must be filled
            raise ValueError(f"Unfilled status for past day: {r.day.isoformat()}")

        if r.status == "office":
            office += 1
        elif r.status == "remote":
            remote += 1
        elif r.status == "holiday":
            holiday += 1

    denom = office + remote
    pct = (office / denom * 100.0) if denom else 0.0
    return pct, office, remote, holiday


def compute_needed(rows: List[Row], target_pct: float) -> Tuple[float, int, int, int, int, int, int, int]:
    """
    Returns: (pct_current, office, remote, holiday, remaining, needed, denom_current, denom_total)

    Counts strictly past days (before today) as settled.
    Today + future blank days are counted as `remaining` workdays.
    Holidays (pre-filled) are excluded from remaining.
    `needed` = office days required from remaining to hit target_pct overall.
    """
    today = date.today()
    office = remote = holiday = 0
    remaining = 0

    for r in rows:
        if r.day < today:
            if r.status is None:
                raise ValueError(f"Unfilled status for past day: {r.day.isoformat()}")
            if r.status == "office":
                office += 1
            elif r.status == "remote":
                remote += 1
            elif r.status == "holiday":
                holiday += 1
        else:  # today or future
            if r.status is None:
                remaining += 1
            elif r.status == "holiday":
                holiday += 1
            elif r.status == "office":
                office += 1
            elif r.status == "remote":
                remote += 1

    denom_current = office + remote
    pct_current = (office / denom_current * 100.0) if denom_current else 0.0
    denom_total = denom_current + remaining
    needed = math.ceil(target_pct / 100.0 * denom_total - office) if denom_total else 0
    needed = max(0, needed)

    return pct_current, office, remote, holiday, remaining, needed, denom_current, denom_total


def cmd_init(args: argparse.Namespace) -> None:
    p = generate_month_file(Path(args.dir), args.year, args.month)
    print(str(p))


def cmd_process(args: argparse.Namespace) -> None:
    base_dir = Path(args.dir)
    
    # Parse comma-separated months
    months = [int(m.strip()) for m in args.month.split(',')]
    
    # Process each month
    all_results = []
    for month in months:
        path = month_file_path(base_dir, args.year, month)

        rows, errors = parse_month_file(path)
        if errors:
            raise SystemExit(f"Invalid month file for {args.year:04d}-{month:02d}:\n- " + "\n- ".join(errors))

        try:
            pct, office, remote, holiday = compute_until_today(rows)
        except ValueError as e:
            raise SystemExit(f"Error in {args.year:04d}-{month:02d}: {e}")

        # Determine if today is in this month
        today = date.today()
        month_contains_today = any(r.day.year == today.year and r.day.month == today.month for r in rows)
        
        all_results.append({
            'month': month,
            'office': office,
            'remote': remote,
            'holiday': holiday,
            'pct': pct,
            'contains_today': month_contains_today
        })
    
    # Display individual month results
    for result in all_results:
        denom = result['office'] + result['remote']
        month_label = f"{args.year:04d}-{result['month']:02d}"
        if result['contains_today']:
            month_label += " (until today)"
        
        print(f"{month_label}")
        print(f"  office={result['office']} remote={result['remote']} holiday={result['holiday']}")
        print(f"  office_pct = {result['office']}/{denom} = {result['pct']:.1f}%")
        print()
    
    # If multiple months, show aggregate
    if len(all_results) > 1:
        total_office = sum(r['office'] for r in all_results)
        total_remote = sum(r['remote'] for r in all_results)
        total_holiday = sum(r['holiday'] for r in all_results)
        total_denom = total_office + total_remote
        total_pct = (total_office / total_denom * 100.0) if total_denom else 0.0
        
        month_range = f"{args.year:04d}-{months[0]:02d} to {args.year:04d}-{months[-1]:02d}"
        print(f"AGGREGATE ({month_range})")
        print(f"  office={total_office} remote={total_remote} holiday={total_holiday}")
        print(f"  office_pct = {total_office}/{total_denom} = {total_pct:.1f}%")


def cmd_process_multi(args: argparse.Namespace) -> None:
    """Process multiple year-month pairs (e.g., 2025-12,2026-01,2026-02)"""
    base_dir = Path(args.dir)
    
    # Parse year-month pairs
    year_month_pairs = []
    for ym in args.months.split(','):
        ym = ym.strip()
        try:
            year_str, month_str = ym.split('-')
            year = int(year_str)
            month = int(month_str)
            if not (1 <= month <= 12):
                raise ValueError(f"Month must be 1-12, got {month}")
            year_month_pairs.append((year, month))
        except ValueError as e:
            raise SystemExit(f"Invalid year-month format '{ym}'. Expected YYYY-MM (e.g., 2026-01). Error: {e}")
    
    # Process each month
    all_results = []
    for year, month in year_month_pairs:
        path = month_file_path(base_dir, year, month)

        rows, errors = parse_month_file(path)
        if errors:
            raise SystemExit(f"Invalid month file for {year:04d}-{month:02d}:\n- " + "\n- ".join(errors))

        try:
            pct, office, remote, holiday = compute_until_today(rows)
        except ValueError as e:
            raise SystemExit(f"Error in {year:04d}-{month:02d}: {e}")

        # Determine if today is in this month
        today = date.today()
        month_contains_today = any(r.day.year == today.year and r.day.month == today.month for r in rows)
        
        all_results.append({
            'year': year,
            'month': month,
            'office': office,
            'remote': remote,
            'holiday': holiday,
            'pct': pct,
            'contains_today': month_contains_today
        })
    
    # Display individual month results
    for result in all_results:
        denom = result['office'] + result['remote']
        month_label = f"{result['year']:04d}-{result['month']:02d}"
        if result['contains_today']:
            month_label += " (until today)"
        
        print(f"{month_label}")
        print(f"  office={result['office']} remote={result['remote']} holiday={result['holiday']}")
        print(f"  office_pct = {result['office']}/{denom} = {result['pct']:.1f}%")
        print()
    
    # If multiple months, show aggregate
    if len(all_results) > 1:
        total_office = sum(r['office'] for r in all_results)
        total_remote = sum(r['remote'] for r in all_results)
        total_holiday = sum(r['holiday'] for r in all_results)
        total_denom = total_office + total_remote
        total_pct = (total_office / total_denom * 100.0) if total_denom else 0.0
        
        first = all_results[0]
        last = all_results[-1]
        month_range = f"{first['year']:04d}-{first['month']:02d} to {last['year']:04d}-{last['month']:02d}"
        print(f"AGGREGATE ({month_range})")
        print(f"  office={total_office} remote={total_remote} holiday={total_holiday}")
        print(f"  office_pct = {total_office}/{total_denom} = {total_pct:.1f}%")


def _print_target_result(month_range: str, office: int, remote: int, holiday: int,
                         pct_current: float, remaining: int, denom_current: int,
                         denom_total: int, needed: int, target_pct: float) -> None:
    today = date.today()
    print(f"Period : {month_range}  (as of {today.isoformat()})")
    print(f"Settled: office={office}  remote={remote}  holiday={holiday}")
    print(f"Current: {office}/{denom_current} = {pct_current:.1f}%")
    print(f"Remaining unfilled workdays: {remaining}")
    print()
    print(f"Target: {target_pct:.1f}%")
    print()
    if remaining == 0:
        print(f"No remaining days — final office % is {pct_current:.1f}%")
    elif needed <= 0:
        print(f"Already at target! You can take all {remaining} remaining days remote.")
    elif needed > remaining:
        max_pct = (office + remaining) / denom_total * 100.0
        print(f"Not achievable — max possible is {max_pct:.1f}%")
        print(f"(would need {needed} office days but only {remaining} remain)")
    else:
        can_remote = remaining - needed
        print(f"You need {needed} office days out of {remaining} remaining days")
        print(f"You can take {can_remote} more remote days")


def cmd_target(args: argparse.Namespace) -> None:
    base_dir = Path(args.dir)
    target_pct = args.target
    months = [int(m.strip()) for m in args.month.split(',')]

    all_rows: List[Row] = []
    for month in months:
        path = month_file_path(base_dir, args.year, month)
        rows, errors = parse_month_file(path)
        if errors:
            raise SystemExit(f"Invalid month file for {args.year:04d}-{month:02d}:\n- " + "\n- ".join(errors))
        all_rows.extend(rows)

    try:
        pct_current, office, remote, holiday, remaining, needed, denom_current, denom_total = compute_needed(all_rows, target_pct)
    except ValueError as e:
        raise SystemExit(f"Error: {e}")

    month_range = f"{args.year:04d}-{months[0]:02d} to {args.year:04d}-{months[-1]:02d}"
    _print_target_result(month_range, office, remote, holiday, pct_current,
                         remaining, denom_current, denom_total, needed, target_pct)


def cmd_target_range(args: argparse.Namespace) -> None:
    """Cross-year target calculation (e.g., Q4 spanning Nov-Dec + Jan next year)."""
    base_dir = Path(args.dir)
    target_pct = args.target

    year_month_pairs = []
    for ym in args.months.split(','):
        ym = ym.strip()
        try:
            year_str, month_str = ym.split('-')
            year_month_pairs.append((int(year_str), int(month_str)))
        except ValueError:
            raise SystemExit(f"Invalid year-month format '{ym}'. Expected YYYY-MM.")

    all_rows: List[Row] = []
    for year, month in year_month_pairs:
        path = month_file_path(base_dir, year, month)
        rows, errors = parse_month_file(path)
        if errors:
            raise SystemExit(f"Invalid month file for {year:04d}-{month:02d}:\n- " + "\n- ".join(errors))
        all_rows.extend(rows)

    try:
        pct_current, office, remote, holiday, remaining, needed, denom_current, denom_total = compute_needed(all_rows, target_pct)
    except ValueError as e:
        raise SystemExit(f"Error: {e}")

    first_y, first_m = year_month_pairs[0]
    last_y, last_m = year_month_pairs[-1]
    month_range = f"{first_y:04d}-{first_m:02d} to {last_y:04d}-{last_m:02d}"
    _print_target_result(month_range, office, remote, holiday, pct_current,
                         remaining, denom_current, denom_total, needed, target_pct)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Track office%% using a per-month TXT file. Quarters not needed for this command flow."
    )
    p.add_argument("--dir", default=os.environ.get("OFFICE_TRACKER_DIR", "office_days_records"), help="Directory to store month files")

    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init-month", help="Create a blank month file: YYYY-MM.txt")
    pi.add_argument("--year", type=int, required=True)
    pi.add_argument("--month", type=int, required=True)
    pi.set_defaults(func=cmd_init)

    pp = sub.add_parser("process-month", help="Validate + compute office%% until today for a month file (or multiple months)")
    pp.add_argument("--year", type=int, required=True)
    pp.add_argument("--month", type=str, required=True, help="Month number (1-12) or comma-separated months (e.g., 2,3,4)")
    pp.set_defaults(func=cmd_process)

    pm = sub.add_parser("process-months", help="Process multiple year-month pairs (supports cross-year ranges)")
    pm.add_argument("--months", type=str, required=True, help="Comma-separated year-month pairs (e.g., 2025-12,2026-01,2026-02)")
    pm.set_defaults(func=cmd_process_multi)

    pt = sub.add_parser("target", help="Show how many remaining days must be office to hit a target %%")
    pt.add_argument("--year", type=int, required=True)
    pt.add_argument("--month", type=str, required=True, help="Comma-separated months (e.g., 2,3,4)")
    pt.add_argument("--target", type=float, default=50.0, help="Target office %% (default: 50.0)")
    pt.set_defaults(func=cmd_target)

    ptr = sub.add_parser("target-range", help="Cross-year target calculation (e.g., Q4)")
    ptr.add_argument("--months", type=str, required=True, help="Comma-separated YYYY-MM pairs (e.g., 2026-11,2026-12,2027-01)")
    ptr.add_argument("--target", type=float, default=50.0, help="Target office %% (default: 50.0)")
    ptr.set_defaults(func=cmd_target_range)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
