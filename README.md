# CSV Commander — CSV Cleaner, Validator & Transformer

**Stop fighting with messy CSV files. One tool, six commands, zero dependencies.**

## What It Does

CSV Commander is the Swiss Army knife for CSV data. Clean messy imports, validate data quality, transform columns, merge files, and generate statistics — all from one command-line tool.

## Commands

```bash
# See what's in your file
csvcommander info data.csv

# Clean messy data (trim whitespace, remove empties)
csvcommander clean data.csv -o clean.csv --required name,email

# Validate data quality (missing columns, duplicates, nulls)
csvcommander validate data.csv --columns name,age,email --check-duplicates

# Transform structure (rename, select, filter, sort)
csvcommander transform data.csv --rename "old_name:new_name" --select name,email

# Merge multiple files
csvcommander merge jan.csv feb.csv mar.csv -o quarterly.csv

# Generate statistics for numeric columns
csvcommander stats sales.csv
```

## Why Data People Need This

Every data analyst has spent hours cleaning CSV files in Excel. CSV Commander does it in seconds from the terminal — scriptable, repeatable, and reliable. No more manual cleanup. No more "why are there 50,000 empty rows?"

## Features

- **info** — column list, row count, non-empty counts, sample rows
- **clean** — trim whitespace, remove empty rows, filter by required columns
- **validate** — schema checks, duplicate detection, null analysis, row count limits
- **transform** — rename, select, drop, filter, sort columns
- **merge** — combine multiple CSVs with auto-alignment
- **stats** — mean, median, min, max, range for every numeric column
- Zero dependencies — pure Python stdlib
- CI/CD ready — validate exits with error code for automation

## Pricing

**$7** — one-time. All six commands. Lifetime updates.

## What You Get

- `csvcommander.py` (MIT license)
- All six subcommands with full argument support
- Works on any CSV file, any size

---

Created by HamdenTwins Digital
---

## Support

If CSV Commander saves you time, consider [sponsoring](https://github.com/sponsors/ellitedom03) or buying me a coffee at [ko-fi.com/hamdentwins](https://ko-fi.com/hamdentwins).

Created by [HamdenTwins Digital](https://payhip.com/HamdenTwinsDigital)
