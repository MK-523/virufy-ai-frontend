# Contributing

Thank you for improving the acoustic sandbox. Keep every change aligned with
its synthetic-only, non-diagnostic scope.

## Development checks

```bash
python -m pip install -e '.[dev]'
ruff check acoustic_sandbox tests examples
python -m unittest discover -s tests -v
python -m build
```

Add tests for changes to WAV validation, temporary-file handling, API behavior,
features, generators, or class selection. Fixtures must be deterministic and
procedurally generated; do not add recorded audio, personal data, health labels,
or downloaded model artifacts.

Do not modify historical prototype files at their original paths or under
`legacy/original`. New maintained work belongs in `acoustic_sandbox`.
