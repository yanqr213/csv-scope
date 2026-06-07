from __future__ import annotations

import json
from typing import Any


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CSV 数据质量报告",
        "",
        f"- 文件：`{report['source']}`",
        f"- 行数：{report['row_count']}",
        f"- 列数：{report['column_count']}",
        "",
        "| 列名 | 类型 | 缺失率 | 缺失数 | 唯一值 | 摘要 |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]

    for column in report["columns"]:
        lines.append(
            "| {name} | {type} | {missing_rate:.2%} | {missing_count} | {unique_count} | {summary} |".format(
                name=_escape_cell(column["name"]),
                type=column["type"],
                missing_rate=column["missing_rate"],
                missing_count=column["missing_count"],
                unique_count=column["unique_count"],
                summary=_escape_cell(_column_summary(column)),
            )
        )

    issues = report.get("expectations", {}).get("issues", [])
    if issues:
        lines.extend(
            [
                "",
                "## Expectations",
                "",
                "| Severity | Code | Column | Message |",
                "| --- | --- | --- | --- |",
            ]
        )
        for issue in issues:
            lines.append(
                "| {severity} | {code} | {column} | {message} |".format(
                    severity=issue["severity"],
                    code=issue["code"],
                    column=_escape_cell(issue["column"]),
                    message=_escape_cell(issue["message"]),
                )
            )

    return "\n".join(lines)


def _column_summary(column: dict[str, Any]) -> str:
    if column["type"] == "number":
        numeric = column["numeric"]
        parts = [
            f"min={_fmt_number(numeric['min'])}",
            f"p25={_fmt_number(numeric['p25'])}",
            f"median={_fmt_number(numeric['median'])}",
            f"p75={_fmt_number(numeric['p75'])}",
            f"max={_fmt_number(numeric['max'])}",
        ]
        if numeric["outlier_count"]:
            examples = ", ".join(_fmt_number(item) for item in numeric["outlier_examples"])
            parts.append(f"异常值={numeric['outlier_count']}（例：{examples}）")
        else:
            parts.append("异常值=0")
        return "; ".join(parts)

    if column["type"] == "date":
        date_info = column["date"]
        return f"{date_info['min']} 至 {date_info['max']}"

    if column["type"] == "empty":
        return "无非空值"

    top_values = column.get("top_values") or []
    if top_values:
        rendered = ", ".join(f"{item['value']}({item['count']})" for item in top_values[:3])
        return f"top: {rendered}"

    return "-"


def _fmt_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:.4g}"


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
