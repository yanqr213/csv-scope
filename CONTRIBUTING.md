# Contributing

Thanks for improving `csv-scope`.

## Local Setup

```bash
python -m pip install -e .
python -m compileall -q csv_scope tests
python tests/test_profiler.py
```

If you have `pytest`:

```bash
python -m pytest
```

## Project Principles

- Keep runtime dependencies at zero unless a feature clearly justifies one.
- Prefer deterministic, explainable profiling rules over opaque magic.
- Keep JSON output backward-compatible whenever possible.
- Add tests for every new rule, output field, or exit-code behavior.

## Pull Request Checklist

- README or docs updated when behavior changes.
- Tests added or updated.
- `python -m compileall -q csv_scope tests` passes.
- `python tests/test_profiler.py` passes.
