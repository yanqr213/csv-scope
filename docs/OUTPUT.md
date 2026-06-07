# Output Reference

`csv-scope` can render the same report as JSON or Markdown.

## JSON Shape

```json
{
  "source": "examples/sample.csv",
  "row_count": 8,
  "column_count": 7,
  "columns": [
    {
      "name": "amount",
      "type": "number",
      "missing_count": 0,
      "missing_rate": 0.0,
      "unique_count": 8,
      "top_values": [{"value": "19.99", "count": 1}],
      "numeric": {
        "min": 9.99,
        "p25": 14.99,
        "median": 32.49,
        "p75": 74.99,
        "max": 199.99,
        "outlier_count": 1,
        "outlier_examples": [199.99],
        "outlier_rule": "IQR: value < Q1 - 1.5*IQR or value > Q3 + 1.5*IQR"
      }
    }
  ],
  "expectations": {
    "source": "examples/expectations.json",
    "issues": []
  }
}
```

## Inferred Types

- `number`: all or most present values parse as numbers.
- `date`: all or most present values parse as dates.
- `boolean`: all present values are common boolean tokens.
- `text`: mixed or categorical text values.
- `empty`: no non-missing values.

Missing tokens include empty strings, `na`, `n/a`, `null`, `none`, and `nan`.

## Markdown Report

Markdown is intended for pull request comments, handoff notes, and customer-facing summaries. It includes a summary table and an expectations table when issues exist.
