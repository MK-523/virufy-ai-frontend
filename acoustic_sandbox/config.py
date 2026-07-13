from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_UPLOAD_BYTES = 2 * 1024 * 1024
DEFAULT_MAX_DURATION_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class Settings:
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
    max_duration_seconds: float = DEFAULT_MAX_DURATION_SECONDS
    allowed_origins: tuple[str, ...] = ()
    temp_dir: Path | None = None

    def __post_init__(self) -> None:
        if not 1_024 <= self.max_upload_bytes <= 20 * 1024 * 1024:
            raise ValueError("max_upload_bytes must be between 1 KiB and 20 MiB")
        if not 0.2 <= self.max_duration_seconds <= 60.0:
            raise ValueError("max_duration_seconds must be between 0.2 and 60 seconds")
        if "*" in self.allowed_origins:
            raise ValueError("wildcard CORS origins are not supported")
        if any(not origin.startswith(("http://", "https://")) for origin in self.allowed_origins):
            raise ValueError("allowed CORS origins must be absolute HTTP(S) origins")

    @classmethod
    def from_env(cls) -> Settings:
        raw_origins = os.getenv("ACOUSTIC_ALLOWED_ORIGINS", "")
        origins = tuple(origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip())
        raw_temp_dir = os.getenv("ACOUSTIC_TEMP_DIR")
        return cls(
            max_upload_bytes=int(os.getenv("ACOUSTIC_MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES)),
            max_duration_seconds=float(
                os.getenv("ACOUSTIC_MAX_DURATION_SECONDS", DEFAULT_MAX_DURATION_SECONDS)
            ),
            allowed_origins=origins,
            temp_dir=Path(raw_temp_dir) if raw_temp_dir else None,
        )
