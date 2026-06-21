#!/usr/bin/env python3
"""
CSV Commander — Clean, Validate & Transform CSV Files
======================================================
The Swiss Army knife for CSV data. Clean messy data, validate schemas,
transform columns, merge files, and generate reports — all from one tool.

Every data analyst and developer needs this. One command, zero setup.

Author: HamdenTwins Digital
License: MIT
Version: 1.0.0
"""

import csv
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import Counter

VERSION = "1.0.0"


def read_csv(filepath, delimiter=",", encoding="utf-8"):
    """Read CSV and return headers + rows."""
    with open(filepath, "r", encoding=encoding, errors="replace") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        headers = reader.fieldnames
        rows = list(reader)
    return headers, rows


def write_csv(filepath, headers, rows, delimiter=","):
    """Write CSV file."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


def cmd_info(args):
    """Show file info: rows, columns, size, sample."""
    headers, rows = read_csv(args.file, args.delimiter)
    path = Path(args.file)

    print(f"  CSV Commander v{VERSION} — File Info")
    print(f"  {'─' * 40}")
    print(f"  File:       {args.file}")
    print(f"  Size:        {path.stat().st_size:,} bytes")
    print(f"  Rows:        {len(rows):,}")
    print(f"  Columns:     {len(headers)}")
    print(f"  Delimiter:   '{args.delimiter}'")
    print(f"\n  Columns:")
    for i, h in enumerate(headers):
        non_empty = sum(1 for r in rows if r.get(h, "").strip())
        print(f"    {i+1}. {h}  ({non_empty}/{len(rows)} non-empty)")

    if rows:
        print(f"\n  Sample (first 3 rows):")
        for i, row in enumerate(rows[:3]):
            print(f"\n  Row {i+1}:")
            for h in headers:
                val = row.get(h, "")[:80]
                print(f"    {h}: {val}")

    print()


def cmd_clean(args):
    """Clean CSV: trim, remove empties, normalize."""
    headers, rows = read_csv(args.file, args.delimiter)

    cleaned = 0
    original = len(rows)
    cleaned_rows = []

    for row in rows:
        # Trim whitespace
        for h in headers:
            if h in row and row[h] is not None:
                row[h] = row[h].strip()

        # Remove empty rows
        if args.remove_empty_rows:
            if all(not row.get(h, "").strip() for h in headers):
                cleaned += 1
                continue

        # Remove rows with empty required columns
        if args.required:
            skip = False
            for req in args.required.split(","):
                req = req.strip()
                if req in headers and not row.get(req, "").strip():
                    skip = True
                    break
            if skip:
                cleaned += 1
                continue

        cleaned_rows.append(row)

    output = args.output or args.file
    write_csv(output, headers, cleaned_rows, args.delimiter)

    removed = original - len(cleaned_rows)
    print(f"  Cleaned: {removed} rows removed, {len(cleaned_rows)} rows kept")
    print(f"  Output:  {output}")
    if removed:
        print(f"  Issues fixed: whitespace trimming, empty row removal")


def cmd_validate(args):
    """Validate CSV against a schema or rules."""
    headers, rows = read_csv(args.file, args.delimiter)
    issues = []

    # Check required columns exist
    if args.columns:
        expected = [c.strip() for c in args.columns.split(",")]
        missing = [c for c in expected if c not in headers]
        if missing:
            issues.append(f"MISSING COLUMNS: {', '.join(missing)}")
        extra = [c for c in headers if c not in expected]
        if extra:
            issues.append(f"EXTRA COLUMNS: {', '.join(extra)}")

    # Check for duplicate rows
    if args.check_duplicates:
        seen = set()
        dupes = 0
        for i, row in enumerate(rows):
            key = tuple(row.get(h, "") for h in headers)
            if key in seen:
                dupes += 1
            seen.add(key)
        if dupes:
            issues.append(f"DUPLICATE ROWS: {dupes}")

    # Check for nulls in required columns
    for h in headers:
        nulls = sum(1 for r in rows if not r.get(h, "").strip())
        if nulls > 0:
            if nulls == len(rows):
                issues.append(f"ALL NULL: '{h}' ({nulls}/{len(rows)} rows)")
            elif nulls > len(rows) * 0.1:
                issues.append(f"HIGH NULLS: '{h}' ({nulls}/{len(rows)} rows)")

    # Row count
    if args.max_rows and len(rows) > args.max_rows:
        issues.append(f"TOO MANY ROWS: {len(rows)} (max {args.max_rows})")
    if args.min_rows and len(rows) < args.min_rows:
        issues.append(f"TOO FEW ROWS: {len(rows)} (min {args.min_rows})")

    print(f"  CSV Commander v{VERSION} — Validation Report")
    print(f"  {'─' * 40}")
    print(f"  File:    {args.file}")
    print(f"  Rows:    {len(rows):,}")
    print(f"  Columns: {len(headers)}")
    print()

    if issues:
        print(f"  ❌ {len(issues)} issue(s) found:\n")
        for issue in issues:
            print(f"     • {issue}")
        print(f"\n  Validation FAILED")
        sys.exit(1)
    else:
        print(f"  ✅ All checks passed. File looks clean!")
        sys.exit(0)


def cmd_transform(args):
    """Transform CSV: rename, reorder, select, add columns."""
    headers, rows = read_csv(args.file, args.delimiter)

    # Rename columns
    if args.rename:
        mapping = {}
        for pair in args.rename.split(","):
            old, new = pair.split(":")
            mapping[old.strip()] = new.strip()
        headers = [mapping.get(h, h) for h in headers]
        for row in rows:
            for old, new in mapping.items():
                if old in row:
                    row[new] = row.pop(old)

    # Select specific columns
    if args.select:
        selected = [c.strip() for c in args.select.split(",")]
        headers = [h for h in headers if h in selected]
        rows = [{h: r.get(h, "") for h in headers} for r in rows]

    # Drop columns
    if args.drop:
        to_drop = {c.strip() for c in args.drop.split(",")}
        headers = [h for h in headers if h not in to_drop]
        rows = [{h: r.get(h, "") for h in headers} for r in rows]

    # Filter rows
    if args.filter:
        field, op, value = args.filter.split(":", 2)
        field = field.strip()
        value = value.strip()
        filtered = []
        for row in rows:
            cell = row.get(field, "")
            if op == "eq" and cell == value:
                filtered.append(row)
            elif op == "ne" and cell != value:
                filtered.append(row)
            elif op == "contains" and value.lower() in cell.lower():
                filtered.append(row)
            elif op == "gt" and float(cell) > float(value):
                filtered.append(row)
            elif op == "lt" and float(cell) < float(value):
                filtered.append(row)
        rows = filtered

    # Sort
    if args.sort:
        field = args.sort.strip()
        reverse = args.sort_desc
        try:
            rows.sort(key=lambda r: float(r.get(field, 0)), reverse=reverse)
        except ValueError:
            rows.sort(key=lambda r: r.get(field, "").lower(), reverse=reverse)

    output = args.output or args.file
    write_csv(output, headers, rows, args.delimiter)
    print(f"  Transformed: {len(rows)} rows, {len(headers)} columns → {output}")


def cmd_merge(args):
    """Merge multiple CSV files."""
    all_rows = []
    all_headers = None

    for i, filepath in enumerate(args.files):
        headers, rows = read_csv(filepath, args.delimiter)
        if all_headers is None:
            all_headers = headers
        elif set(headers) != set(all_headers):
            print(f"  Warning: {filepath} has different columns — aligning...")
            # Align to master headers
            aligned = []
            for row in rows:
                aligned.append({h: row.get(h, "") for h in all_headers})
            rows = aligned

        all_rows.extend(rows)
        print(f"  + {filepath}: {len(rows)} rows")

    output = args.output or "merged.csv"
    write_csv(output, all_headers, all_rows, args.delimiter)
    print(f"  Merged: {len(all_rows)} total rows → {output}")


def cmd_stats(args):
    """Generate statistics for numeric columns."""
    headers, rows = read_csv(args.file, args.delimiter)

    print(f"  CSV Commander v{VERSION} — Column Statistics")
    print(f"  {'─' * 50}")

    for h in headers:
        values = []
        for r in rows:
            val = r.get(h, "").strip()
            if val:
                try:
                    values.append(float(val))
                except ValueError:
                    pass

        if not values:
            continue

        values.sort()
        n = len(values)
        total = sum(values)
        mean = total / n
        median = values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2

        print(f"\n  📊 {h}")
        print(f"     Count:   {n:,}")
        print(f"     Sum:     {total:,.2f}")
        print(f"     Mean:    {mean:,.2f}")
        print(f"     Median:  {median:,.2f}")
        print(f"     Min:     {values[0]:,.2f}")
        print(f"     Max:     {values[-1]:,.2f}")
        print(f"     Range:   {values[-1] - values[0]:,.2f}")

    # Show null counts for all columns
    print(f"\n  📋 Missing Values:")
    for h in headers:
        nulls = sum(1 for r in rows if not r.get(h, "").strip())
        pct = (nulls / len(rows) * 100) if rows else 0
        bar = "█" * int(pct / 5) if pct > 0 else ""
        print(f"     {h:20s}  {nulls:5d} ({pct:5.1f}%) {bar}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="CSV Commander — Clean, validate, transform, and analyze CSV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # info
    p = subparsers.add_parser("info", help="Show file info and sample")
    p.add_argument("file", help="CSV file")
    p.add_argument("-d", "--delimiter", default=",", help="Delimiter (default: comma)")
    p.set_defaults(func=cmd_info)

    # clean
    p = subparsers.add_parser("clean", help="Clean messy CSV data")
    p.add_argument("file", help="CSV file")
    p.add_argument("-o", "--output", help="Output file")
    p.add_argument("-d", "--delimiter", default=",", help="Delimiter")
    p.add_argument("--remove-empty-rows", action="store_true", default=True, help="Remove empty rows")
    p.add_argument("--required", help="Required columns (comma-separated)")
    p.set_defaults(func=cmd_clean)

    # validate
    p = subparsers.add_parser("validate", help="Validate CSV data quality")
    p.add_argument("file", help="CSV file")
    p.add_argument("-d", "--delimiter", default=",", help="Delimiter")
    p.add_argument("--columns", help="Expected columns (comma-separated)")
    p.add_argument("--check-duplicates", action="store_true", help="Check for duplicate rows")
    p.add_argument("--max-rows", type=int, help="Max allowed rows")
    p.add_argument("--min-rows", type=int, help="Min required rows")
    p.set_defaults(func=cmd_validate)

    # transform
    p = subparsers.add_parser("transform", help="Transform CSV structure")
    p.add_argument("file", help="CSV file")
    p.add_argument("-o", "--output", help="Output file")
    p.add_argument("-d", "--delimiter", default=",", help="Delimiter")
    p.add_argument("--rename", help="Rename columns (old:new,old:new)")
    p.add_argument("--select", help="Select columns (comma-separated)")
    p.add_argument("--drop", help="Drop columns (comma-separated)")
    p.add_argument("--filter", help="Filter rows (field:op:value). Ops: eq,ne,contains,gt,lt")
    p.add_argument("--sort", help="Sort by column")
    p.add_argument("--sort-desc", action="store_true", help="Sort descending")
    p.set_defaults(func=cmd_transform)

    # merge
    p = subparsers.add_parser("merge", help="Merge multiple CSV files")
    p.add_argument("files", nargs="+", help="CSV files to merge")
    p.add_argument("-o", "--output", default="merged.csv", help="Output file")
    p.add_argument("-d", "--delimiter", default=",", help="Delimiter")
    p.set_defaults(func=cmd_merge)

    # stats
    p = subparsers.add_parser("stats", help="Generate column statistics")
    p.add_argument("file", help="CSV file")
    p.add_argument("-d", "--delimiter", default=",", help="Delimiter")
    p.set_defaults(func=cmd_stats)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()