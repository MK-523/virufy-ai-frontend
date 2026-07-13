from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audio import analyze_wav
from .config import DEFAULT_MAX_DURATION_SECONDS, DEFAULT_MAX_UPLOAD_BYTES
from .errors import AcousticSandboxError
from .model import AcousticSandboxModel
from .synthetic import write_fixture_set


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="acoustic-sandbox",
        description="NON-DIAGNOSTIC acoustic feature and synthetic-class sandbox.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    fixtures = commands.add_parser("fixtures", help="generate deterministic synthetic WAV fixtures")
    fixtures.add_argument("--output-dir", type=Path, default=Path("generated-fixtures"))
    classify = commands.add_parser("classify", help="classify a PCM WAV into neutral synthetic families")
    classify.add_argument("wav", type=Path)
    return parser


def _classify(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise AcousticSandboxError(f"file not found: {path}")
    if path.stat().st_size > DEFAULT_MAX_UPLOAD_BYTES:
        raise AcousticSandboxError(f"WAV exceeds the {DEFAULT_MAX_UPLOAD_BYTES}-byte limit")
    analyzed = analyze_wav(path, max_duration_seconds=DEFAULT_MAX_DURATION_SECONDS)
    classification = AcousticSandboxModel().classify(analyzed.features)
    return {
        "notice": "NON-DIAGNOSTIC ACOUSTIC ML SANDBOX",
        "model_id": classification.model_id,
        "classification": {
            "class_id": classification.class_id,
            "display_name": classification.display_name,
        },
        "relative_scores": dict(classification.relative_scores),
        "audio": analyzed.metadata.to_dict(),
        "features": analyzed.features.to_dict(),
    }


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "fixtures":
            for path in write_fixture_set(arguments.output_dir):
                print(path)
        else:
            print(json.dumps(_classify(arguments.wav), indent=2, sort_keys=True))
    except AcousticSandboxError as exc:
        raise SystemExit(f"error: {exc}") from exc
    return 0
