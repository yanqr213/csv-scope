from __future__ import annotations

import argparse
from pathlib import Path

from .profiler import evaluate_expectations, load_expectations, profile_csv
from .renderers import render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m csv_scope",
        description="Profile CSV data quality and emit a compact report.",
    )
    parser.add_argument("csv_file", help="Path to the CSV file to profile.")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="Report format. Defaults to markdown.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="CSV file encoding. Defaults to utf-8-sig.",
    )
    parser.add_argument(
        "--delimiter",
        default=",",
        help="CSV delimiter. Defaults to ','.",
    )
    parser.add_argument(
        "--output",
        help="Write report to this path instead of stdout.",
    )
    parser.add_argument(
        "--expectations",
        help="Optional JSON quality contract to evaluate against the CSV.",
    )
    parser.add_argument(
        "--fail-on",
        choices=("never", "error", "warning"),
        default="error",
        help="Exit non-zero when expectation issues reach this severity. Defaults to error.",
    )
    parser.add_argument(
        "--top-values",
        type=int,
        default=5,
        help="Number of frequent values to include for each column. Defaults to 5.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    report = profile_csv(
        args.csv_file,
        encoding=args.encoding,
        delimiter=args.delimiter,
        top_values=args.top_values,
    )
    if args.expectations:
        expectations = load_expectations(args.expectations)
        report["expectations"] = {
            "source": args.expectations,
            "issues": evaluate_expectations(report, expectations),
        }
    rendered = render_json(report) if args.format == "json" else render_markdown(report)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    return _exit_code(report, fail_on=args.fail_on)


def _exit_code(report: dict, *, fail_on: str) -> int:
    if fail_on == "never":
        return 0

    issues = report.get("expectations", {}).get("issues", [])
    severities = {issue.get("severity") for issue in issues}
    if fail_on == "warning" and ("warning" in severities or "error" in severities):
        return 1
    if fail_on == "error" and "error" in severities:
        return 1
    return 0
