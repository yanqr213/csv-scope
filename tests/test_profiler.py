from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from csv_scope.cli import main
from csv_scope.profiler import evaluate_expectations, profile_rows
from csv_scope.renderers import render_json, render_markdown


def test_profile_rows_infers_types_and_quality_metrics() -> None:
    rows = [
        {"name": "Alice", "age": "30", "joined": "2025-01-01", "score": "10"},
        {"name": "Bob", "age": "", "joined": "2025-01-02", "score": "11"},
        {"name": "Cara", "age": "40", "joined": "2025-01-03", "score": "100"},
    ]

    report = profile_rows(rows, fieldnames=["name", "age", "joined", "score"])
    columns = {column["name"]: column for column in report["columns"]}

    assert report["row_count"] == 3
    assert columns["name"]["type"] == "text"
    assert columns["age"]["type"] == "number"
    assert columns["age"]["missing_count"] == 1
    assert columns["age"]["missing_rate"] == 0.3333
    assert columns["joined"]["type"] == "date"
    assert columns["joined"]["date"] == {"min": "2025-01-01", "max": "2025-01-03"}
    assert columns["score"]["numeric"]["outlier_count"] == 0
    assert columns["name"]["top_values"][0] == {"value": "Alice", "count": 1}


def test_renderers_emit_expected_formats() -> None:
    report = profile_rows(
        [{"amount": "1"}, {"amount": "2"}],
        fieldnames=["amount"],
        source="sample.csv",
    )

    as_json = json.loads(render_json(report))
    as_markdown = render_markdown(report)

    assert as_json["source"] == "sample.csv"
    assert "# CSV 数据质量报告" in as_markdown
    assert "| amount | number |" in as_markdown


def test_expectations_report_errors_and_warnings() -> None:
    report = profile_rows(
        [
            {"id": "1", "amount": "10"},
            {"id": "", "amount": "999"},
        ],
        fieldnames=["id", "amount"],
    )
    issues = evaluate_expectations(
        report,
        {
            "required_columns": ["id", "amount", "created_at"],
            "columns": {
                "id": {"type": "number", "max_missing_rate": 0.0},
                "amount": {"type": "number", "max_outlier_count": 0},
            },
        },
    )

    assert {issue["code"] for issue in issues} == {"missing_column", "missing_rate_exceeded"}
    assert all(issue["severity"] == "error" for issue in issues)


def test_cli_returns_non_zero_for_failed_expectations(tmp_path: Path) -> None:
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text("id,name\n1,Alice\n,Bob\n", encoding="utf-8")
    expectations = tmp_path / "expectations.json"
    expectations.write_text(
        json.dumps({"columns": {"id": {"type": "number", "max_missing_rate": 0.0}}}),
        encoding="utf-8",
    )

    assert main([str(csv_file), "--expectations", str(expectations), "--format", "json"]) == 1


if __name__ == "__main__":
    test_profile_rows_infers_types_and_quality_metrics()
    test_renderers_emit_expected_formats()
    test_expectations_report_errors_and_warnings()
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        test_cli_returns_non_zero_for_failed_expectations(Path(directory))
    print("smoke tests passed")
