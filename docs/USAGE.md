# Usage Guide

`csv-scope` has two jobs:

1. Produce a compact profile for a CSV file.
2. Optionally fail the command when the file violates a quality contract.

## Basic Profiling

```bash
python -m csv_scope examples/sample.csv
python -m csv_scope examples/sample.csv --format json
python -m csv_scope examples/sample.csv --format markdown --output report.md
```

The input file must include a header row. By default, files are read as `utf-8-sig` and parsed with comma delimiters.

```bash
python -m csv_scope exports/orders.tsv --delimiter "`t" --encoding utf-8
```

On PowerShell, pass a tab delimiter as:

```powershell
python -m csv_scope exports/orders.tsv --delimiter "`t"
```

## Expectations

Expectations are JSON files that describe the minimum contract your CSV must satisfy.

```json
{
  "required_columns": ["customer_id", "created_at", "amount", "status"],
  "columns": {
    "customer_id": {
      "type": "number",
      "max_missing_rate": 0
    },
    "amount": {
      "type": "number",
      "max_missing_rate": 0.05,
      "max_outlier_count": 2
    }
  }
}
```

Supported column rules:

- `type`: one of `number`, `date`, `boolean`, `text`, `empty`.
- `max_missing_rate`: a decimal between `0` and `1`.
- `max_outlier_count`: numeric columns only; checked with the IQR outlier count.

Run a gate:

```bash
csv-scope examples/sample.csv --expectations examples/expectations.json --fail-on error
```

The bundled `examples/expectations.json` matches `examples/sample.csv`. Use `examples/failing-expectations.json` when you want to see failure output locally.

`--fail-on warning` also fails for warning-level issues such as numeric outlier thresholds.

`--fail-on never` always exits `0` while still rendering issues in the report.

## Exit Codes

- `0`: success.
- `1`: expectations produced issues at or above the configured `--fail-on` severity.
- `2`: invalid CLI usage, returned by `argparse`.

## Pipeline Pattern

```bash
csv-scope incoming/orders.csv \
  --expectations contracts/orders.expectations.json \
  --format json \
  --output artifacts/orders-profile.json
```

This gives downstream jobs a stable JSON file while preserving a useful terminal failure code.
