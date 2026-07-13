from __future__ import annotations

import json
import mimetypes
import tempfile
import uuid
from collections.abc import Callable, Iterable
from importlib.resources import files
from pathlib import Path
from typing import Any

from .audio import analyze_wav
from .config import Settings
from .errors import AudioValidationError
from .model import AcousticSandboxModel

StartResponse = Callable[[str, list[tuple[str, str]]], Any]
STATUS_TEXT = {
    200: "OK",
    204: "No Content",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    411: "Length Required",
    413: "Content Too Large",
    415: "Unsupported Media Type",
    500: "Internal Server Error",
}
STATIC_FILES = {
    "/": "index.html",
    "/app.js": "app.js",
    "/styles.css": "styles.css",
}
SECURITY_HEADERS = [
    (
        "Content-Security-Policy",
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "media-src 'self' blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; "
        "frame-ancestors 'none'; form-action 'self'",
    ),
    ("Permissions-Policy", "camera=(), geolocation=(), microphone=()"),
    ("Referrer-Policy", "no-referrer"),
    ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Cross-Origin-Resource-Policy", "same-origin"),
]


def _same_origin(origin: str, environ: dict[str, Any]) -> bool:
    scheme = environ.get("wsgi.url_scheme", "http")
    host = environ.get("HTTP_HOST")
    return bool(host) and origin.rstrip("/") == f"{scheme}://{host}".rstrip("/")


class AcousticSandboxApp:
    def __init__(self, settings: Settings | None = None, model: AcousticSandboxModel | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.model = model or AcousticSandboxModel()

    def _origin_allowed(self, origin: str, environ: dict[str, Any]) -> bool:
        normalized = origin.rstrip("/")
        return _same_origin(normalized, environ) or normalized in self.settings.allowed_origins

    def _headers(
        self,
        content_type: str,
        body_length: int,
        *,
        origin: str | None = None,
        environ: dict[str, Any] | None = None,
    ) -> list[tuple[str, str]]:
        headers = [
            ("Content-Type", content_type),
            ("Content-Length", str(body_length)),
            ("Cache-Control", "no-store"),
            *SECURITY_HEADERS,
        ]
        if origin and environ and self._origin_allowed(origin, environ):
            headers.extend([("Access-Control-Allow-Origin", origin.rstrip("/")), ("Vary", "Origin")])
        return headers

    def _respond(
        self,
        start_response: StartResponse,
        status: int,
        body: bytes,
        content_type: str,
        *,
        origin: str | None = None,
        environ: dict[str, Any] | None = None,
        extra_headers: Iterable[tuple[str, str]] = (),
    ) -> list[bytes]:
        headers = self._headers(content_type, len(body), origin=origin, environ=environ)
        headers.extend(extra_headers)
        start_response(f"{status} {STATUS_TEXT[status]}", headers)
        return [body]

    def _json(
        self,
        start_response: StartResponse,
        status: int,
        payload: dict[str, Any],
        *,
        origin: str | None,
        environ: dict[str, Any],
        extra_headers: Iterable[tuple[str, str]] = (),
    ) -> list[bytes]:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return self._respond(
            start_response,
            status,
            body,
            "application/json; charset=utf-8",
            origin=origin,
            environ=environ,
            extra_headers=extra_headers,
        )

    def _error(
        self,
        start_response: StartResponse,
        status: int,
        code: str,
        message: str,
        *,
        origin: str | None,
        environ: dict[str, Any],
        request_id: str,
    ) -> list[bytes]:
        return self._json(
            start_response,
            status,
            {"error": {"code": code, "message": message}, "request_id": request_id},
            origin=origin,
            environ=environ,
        )

    def _classify(
        self,
        environ: dict[str, Any],
        start_response: StartResponse,
        *,
        origin: str | None,
        request_id: str,
    ) -> list[bytes]:
        content_type = str(environ.get("CONTENT_TYPE", "")).split(";", 1)[0].strip().casefold()
        if content_type not in {"audio/wav", "audio/x-wav", "audio/wave"}:
            return self._error(
                start_response,
                415,
                "unsupported_media_type",
                "Upload an uncompressed PCM WAV using an audio/wav content type.",
                origin=origin,
                environ=environ,
                request_id=request_id,
            )
        raw_length = environ.get("CONTENT_LENGTH")
        if raw_length in (None, ""):
            return self._error(
                start_response,
                411,
                "length_required",
                "Content-Length is required.",
                origin=origin,
                environ=environ,
                request_id=request_id,
            )
        try:
            content_length = int(raw_length)
        except (TypeError, ValueError):
            content_length = -1
        if content_length <= 0:
            return self._error(
                start_response,
                400,
                "invalid_length",
                "Content-Length must be a positive integer.",
                origin=origin,
                environ=environ,
                request_id=request_id,
            )
        if content_length > self.settings.max_upload_bytes:
            return self._error(
                start_response,
                413,
                "upload_too_large",
                f"WAV upload exceeds the {self.settings.max_upload_bytes}-byte limit.",
                origin=origin,
                environ=environ,
                request_id=request_id,
            )

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix="acoustic-sandbox-",
                suffix=".wav",
                dir=self.settings.temp_dir,
                delete=False,
            ) as temporary:
                temp_path = Path(temporary.name)
                remaining = content_length
                while remaining:
                    chunk = environ["wsgi.input"].read(min(remaining, 64 * 1024))
                    if not chunk:
                        raise AudioValidationError("request body ended before Content-Length bytes were received")
                    temporary.write(chunk)
                    remaining -= len(chunk)

            analyzed = analyze_wav(temp_path, max_duration_seconds=self.settings.max_duration_seconds)
            classification = self.model.classify(analyzed.features)
            return self._json(
                start_response,
                200,
                {
                    "schema_version": 1,
                    "request_id": request_id,
                    "notice": "NON-DIAGNOSTIC ACOUSTIC ML SANDBOX — synthetic sound-shape classes only.",
                    "classification": {
                        "class_id": classification.class_id,
                        "display_name": classification.display_name,
                    },
                    "relative_scores": {
                        label: round(float(score), 10)
                        for label, score in classification.relative_scores.items()
                    },
                    "audio": analyzed.metadata.to_dict(),
                    "features": {
                        name: round(float(value), 10)
                        for name, value in analyzed.features.to_dict().items()
                    },
                    "model": {
                        "id": classification.model_id,
                        "training_data": "deterministic synthetic waveforms only",
                    },
                },
                origin=origin,
                environ=environ,
            )
        except AudioValidationError as exc:
            return self._error(
                start_response,
                400,
                "invalid_wav",
                str(exc),
                origin=origin,
                environ=environ,
                request_id=request_id,
            )
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def _dispatch(self, environ: dict[str, Any], start_response: StartResponse) -> list[bytes]:
        request_id = uuid.uuid4().hex
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = str(environ.get("PATH_INFO", "/"))
        origin = environ.get("HTTP_ORIGIN")

        if path.startswith("/api/") and origin and not self._origin_allowed(str(origin), environ):
            return self._error(
                start_response,
                403,
                "origin_not_allowed",
                "Request origin is not allowed.",
                origin=None,
                environ=environ,
                request_id=request_id,
            )

        if method == "OPTIONS" and path == "/api/classify":
            return self._respond(
                start_response,
                204,
                b"",
                "text/plain; charset=utf-8",
                origin=str(origin) if origin else None,
                environ=environ,
                extra_headers=(
                    ("Access-Control-Allow-Methods", "POST, OPTIONS"),
                    ("Access-Control-Allow-Headers", "Content-Type, X-Filename"),
                    ("Access-Control-Max-Age", "600"),
                ),
            )

        if path == "/api/health":
            if method != "GET":
                return self._error(
                    start_response,
                    405,
                    "method_not_allowed",
                    "Use GET for this endpoint.",
                    origin=str(origin) if origin else None,
                    environ=environ,
                    request_id=request_id,
                )
            return self._json(
                start_response,
                200,
                {"status": "ok", "service": "acoustic-sandbox", "diagnostic_use": False},
                origin=str(origin) if origin else None,
                environ=environ,
            )

        if path == "/api/config":
            if method != "GET":
                return self._error(
                    start_response,
                    405,
                    "method_not_allowed",
                    "Use GET for this endpoint.",
                    origin=str(origin) if origin else None,
                    environ=environ,
                    request_id=request_id,
                )
            return self._json(
                start_response,
                200,
                {
                    "accepted_content_types": ["audio/wav", "audio/x-wav", "audio/wave"],
                    "max_upload_bytes": self.settings.max_upload_bytes,
                    "max_duration_seconds": self.settings.max_duration_seconds,
                },
                origin=str(origin) if origin else None,
                environ=environ,
            )

        if path == "/api/classify":
            if method != "POST":
                return self._error(
                    start_response,
                    405,
                    "method_not_allowed",
                    "Use POST with a raw PCM WAV body.",
                    origin=str(origin) if origin else None,
                    environ=environ,
                    request_id=request_id,
                )
            return self._classify(
                environ,
                start_response,
                origin=str(origin) if origin else None,
                request_id=request_id,
            )

        if method in {"GET", "HEAD"} and path in STATIC_FILES:
            resource = files("acoustic_sandbox").joinpath("static", STATIC_FILES[path])
            body = resource.read_bytes()
            if method == "HEAD":
                body = b""
            content_type = mimetypes.guess_type(STATIC_FILES[path])[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type == "application/javascript":
                content_type += "; charset=utf-8"
            return self._respond(start_response, 200, body, content_type)

        return self._error(
            start_response,
            404,
            "not_found",
            "Resource not found.",
            origin=str(origin) if origin else None,
            environ=environ,
            request_id=request_id,
        )

    def __call__(self, environ: dict[str, Any], start_response: StartResponse) -> list[bytes]:
        try:
            return self._dispatch(environ, start_response)
        except Exception:
            request_id = uuid.uuid4().hex
            return self._error(
                start_response,
                500,
                "internal_error",
                "The request could not be completed.",
                origin=None,
                environ=environ,
                request_id=request_id,
            )


application = AcousticSandboxApp()
