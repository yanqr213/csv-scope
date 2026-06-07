from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import Any

MISSING_VALUES = {"", "na", "n/a", "null", "none", "nan"}
TRUE_VALUES = {"true", "t", "yes", "y"}
FALSE_VALUES = {"false", "f", "no", "n"}
DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
)


def profile_csv(
    path: str | Path,
    *,
    encoding: str = "utf-8-sig",
    delimiter: str = ",",
    top_values: int = 5,
) -> dict[str, Any]:
    csv_path = Path(path)
    with csv_path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        rows = list(reader)

    return profile_rows(rows, fieldnames=reader.fieldnames or [], source=str(csv_path), top_values=top_values)


def profile_rows(
    rows: list[dict[str, str]],
    *,
    fieldnames: list[str],
    source: str = "<memory>",
    top_values: int = 5,
) -> dict[str, Any]:
    columns = [
        _profile_column(name, [row.get(name, "") for row in rows], top_values=top_values)
        for name in fieldnames
    ]
    return {
        "source": source,
        "row_count": len(rows),
        "column_count": len(fieldnames),
        "columns": columns,
    }


def evaluate_expectations(report: dict[str, Any], expectations: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate a compact JSON quality contract against a generated report."""
    columns = {column["name"]: column for column in report["columns"]}
    issues: list[dict[str, Any]] = []

    required_columns = expectations.get("required_columns", [])
    for column_name in required_columns:
        if column_name not in columns:
            issues.append(_issue("missing_column", "error", column_name, "required column is absent"))

    expected_columns = expectations.get("columns", {})
    for column_name, rules in expected_columns.items():
        column = columns.get(column_name)
        if column is None:
            issues.append(_issue("missing_column", "error", column_name, "configured column is absent"))
            continue

        expected_type = rules.get("type")
        if expected_type and column["type"] != expected_type:
            issues.append(
                _issue(
                    "type_mismatch",
                    "error",
                    column_name,
                    f"expected {expected_type}, got {column['type']}",
                    expected=expected_type,
                    actual=column["type"],
                )
            )

        max_missing_rate = rules.get("max_missing_rate")
        if max_missing_rate is not None and column["missing_rate"] > float(max_missing_rate):
            issues.append(
                _issue(
                    "missing_rate_exceeded",
                    "error",
                    column_name,
                    f"missing rate {column['missing_rate']:.2%} exceeds {float(max_missing_rate):.2%}",
                    expected=max_missing_rate,
                    actual=column["missing_rate"],
                )
            )

        max_outlier_count = rules.get("max_outlier_count")
        if max_outlier_count is not None and column["type"] == "number":
            outlier_count = column["numeric"]["outlier_count"]
            if outlier_count > int(max_outlier_count):
                issues.append(
                    _issue(
                        "outlier_count_exceeded",
                        "warning",
                        column_name,
                        f"outlier count {outlier_count} exceeds {max_outlier_count}",
                        expected=max_outlier_count,
                        actual=outlier_count,
                    )
                )

    return issues


def load_expectations(path: str | Path) -> dict[str, Any]:
    expectation_path = Path(path)
    with expectation_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("expectations file must contain a JSON object")
    return data


def _profile_column(name: str, values: list[str], *, top_values: int) -> dict[str, Any]:
    total = len(values)
    cleaned = [_clean(value) for value in values]
    present = [value for value in cleaned if not _is_missing(value)]
    missing_count = total - len(present)
    unique_count = len(set(present))

    numbers = [_parse_float(value) for value in present]
    numeric_values = [value for value in numbers if value is not None]
    dates = [_parse_date(value) for value in present]
    date_values = [value for value in dates if value is not None]
    bool_count = sum(1 for value in present if _parse_bool(value) is not None)

    inferred_type = _infer_type(
        present_count=len(present),
        numeric_count=len(numeric_values),
        date_count=len(date_values),
        bool_count=bool_count,
    )

    result: dict[str, Any] = {
        "name": name,
        "type": inferred_type,
        "missing_count": missing_count,
        "missing_rate": _safe_ratio(missing_count, total),
        "unique_count": unique_count,
        "top_values": _top_values(present, limit=top_values),
    }

    if inferred_type == "number":
        result["numeric"] = _numeric_summary(numeric_values)
    if inferred_type == "date":
        result["date"] = {
            "min": min(date_values).isoformat(),
            "max": max(date_values).isoformat(),
        }

    return result


def _top_values(values: list[str], *, limit: int) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{"value": value, "count": count} for value, count in ranked[:limit]]


def _issue(
    code: str,
    severity: str,
    column: str,
    message: str,
    *,
    expected: Any | None = None,
    actual: Any | None = None,
) -> dict[str, Any]:
    issue = {
        "code": code,
        "severity": severity,
        "column": column,
        "message": message,
    }
    if expected is not None:
        issue["expected"] = expected
    if actual is not None:
        issue["actual"] = actual
    return issue


def _infer_type(
    *,
    present_count: int,
    numeric_count: int,
    date_count: int,
    bool_count: int,
) -> str:
    if present_count == 0:
        return "empty"
    if bool_count == present_count:
        return "boolean"
    if numeric_count == present_count:
        return "number"
    if date_count == present_count:
        return "date"
    if numeric_count / present_count >= 0.85:
        return "number"
    if date_count / present_count >= 0.85:
        return "date"
    return "text"


def _numeric_summary(values: list[float]) -> dict[str, Any]:
    sorted_values = sorted(values)
    q1 = _percentile(sorted_values, 0.25)
    q3 = _percentile(sorted_values, 0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = [value for value in sorted_values if value < lower_bound or value > upper_bound]

    return {
        "min": sorted_values[0],
        "p25": q1,
        "median": median(sorted_values),
        "p75": q3,
        "max": sorted_values[-1],
        "outlier_count": len(outliers),
        "outlier_examples": outliers[:5],
        "outlier_rule": "IQR: value < Q1 - 1.5*IQR or value > Q3 + 1.5*IQR",
    }


def _percentile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        raise ValueError("percentile requires at least one value")
    if len(sorted_values) == 1:
        return sorted_values[0]

    position = (len(sorted_values) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    weight = position - lower_index
    return sorted_values[lower_index] * (1 - weight) + sorted_values[upper_index] * weight


def _clean(value: str | None) -> str:
    return "" if value is None else str(value).strip()


def _is_missing(value: str) -> bool:
    return value.lower() in MISSING_VALUES


def _parse_float(value: str) -> float | None:
    try:
        normalized = value.replace(",", "")
        return float(normalized)
    except ValueError:
        return None


def _parse_date(value: str) -> date | None:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def _parse_bool(value: str) -> bool | None:
    lowered = value.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    return None


def _safe_ratio(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else round(numerator / denominator, 4)
