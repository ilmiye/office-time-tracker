#!/usr/bin/env python3
from __future__ import annotations

import argparse
import calendar
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Tuple, Optional

VALID = {"holiday", "remote", "office"}
ALLOWED_EMPTY = True  # empty status means "not filled" and is an error for past days


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

    if not path.exists():
        raise SystemExit(f"Month file not found: {path}")

    text = path.read_text(encoding="utf-8").splitlines()

    for i, raw in enumerate(text, start=1):
        line = raw.strip()

        if not line:
            continue  # ignore blank lines entirely

        parts = line.split()
        if len(parts) == 0:
            continue

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
        missing = sorted(expected - actual)
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


def cmd_init(args: argparse.Namespace) -> None:
    p = generate_month_file(Path(args.dir), args.year, args.month)
    print(str(p))


def cmd_process(args: argparse.Namespace) -> None:
    base_dir = Path(args.dir)
    path = month_file_path(base_dir, args.year, args.month)

    rows, errors = parse_month_file(path)
    if errors:
        raise SystemExit("Invalid month file:\n- " + "\n- ".join(errors))

    try:
        pct, office, remote, holiday = compute_until_today(rows)
    except ValueError as e:
        raise SystemExit(str(e))

    denom = office + remote
    print(f"{args.year:04d}-{args.month:02d} (until today)")
    print(f"office={office} remote={remote} holiday={holiday}")
    print(f"office_pct = {office}/{denom} = {pct:.1f}%")

    # Extra strictness: detect any past days beyond today that were filled incorrectly is already handled by parser
    # We also want to throw if there are any blank past days; already done above.


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Track office%% using a per-month TXT file. Quarters not needed for this command flow."
    )
    p.add_argument("--dir", default="office_days_records", help="Directory to store month files")

    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("init-month", help="Create a blank month file: YYYY-MM.txt")
    pi.add_argument("--year", type=int, required=True)
    pi.add_argument("--month", type=int, required=True)
    pi.set_defaults(func=cmd_init)

    pp = sub.add_parser("process-month", help="Validate + compute office%% until today for a month file")
    pp.add_argument("--year", type=int, required=True)
    pp.add_argument("--month", type=int, required=True)
    pp.set_defaults(func=cmd_process)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
