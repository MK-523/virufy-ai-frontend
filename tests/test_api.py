import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from acoustic_sandbox.api import AcousticSandboxApp
from acoustic_sandbox.config import Settings
from acoustic_sandbox.synthetic import generate_fixture_bytes


def request(app, path, *, method="GET", body=b"", content_type="", origin=None):
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "CONTENT_LENGTH": str(len(body)) if body else "",
        "CONTENT_TYPE": content_type,
        "HTTP_HOST": "sandbox.test",
        "wsgi.url_scheme": "https",
        "wsgi.input": io.BytesIO(body),
    }
    if origin:
        environ["HTTP_ORIGIN"] = origin
    payload = b"".join(app(environ, start_response))
    return captured["status"], captured["headers"], payload


class ApiTest(unittest.TestCase):
    def test_static_frontend_has_security_headers_and_safety_label(self):
        status, headers, body = request(AcousticSandboxApp(), "/")
        self.assertTrue(status.startswith("200"))
        self.assertIn("default-src 'self'", headers["Content-Security-Policy"])
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertIn(b"NON-DIAGNOSTIC", body.upper())

    def test_successful_classification_uses_neutral_classes_and_deletes_temp_file(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            app = AcousticSandboxApp(Settings(temp_dir=Path(raw_tmp)))
            status, headers, body = request(
                app,
                "/api/classify",
                method="POST",
                body=generate_fixture_bytes("pulsed_tone"),
                content_type="audio/wav",
            )
            self.assertEqual(list(Path(raw_tmp).iterdir()), [])
        result = json.loads(body)
        self.assertTrue(status.startswith("200"))
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(result["classification"]["class_id"], "pulsed_tone")
        self.assertIn("NON-DIAGNOSTIC", result["notice"])
        serialized = json.dumps(result).casefold()
        for forbidden in ("covid", "bronchitis", "healthy", "disease"):
            self.assertNotIn(forbidden, serialized)

    def test_temp_names_are_unique_across_requests(self):
        original = tempfile.NamedTemporaryFile
        names = []

        def recording_tempfile(*args, **kwargs):
            handle = original(*args, **kwargs)
            names.append(handle.name)
            return handle

        with tempfile.TemporaryDirectory() as raw_tmp:
            app = AcousticSandboxApp(Settings(temp_dir=Path(raw_tmp)))
            with patch("acoustic_sandbox.api.tempfile.NamedTemporaryFile", side_effect=recording_tempfile):
                for _ in range(2):
                    status, _, _ = request(
                        app,
                        "/api/classify",
                        method="POST",
                        body=generate_fixture_bytes("steady_tone"),
                        content_type="audio/wav",
                    )
                    self.assertTrue(status.startswith("200"))
        self.assertEqual(len(names), 2)
        self.assertNotEqual(names[0], names[1])

    def test_size_and_type_limits_fail_before_processing(self):
        app = AcousticSandboxApp(Settings(max_upload_bytes=1_024))
        status, _, body = request(
            app,
            "/api/classify",
            method="POST",
            body=b"x" * 1_025,
            content_type="audio/wav",
        )
        self.assertTrue(status.startswith("413"))
        self.assertEqual(json.loads(body)["error"]["code"], "upload_too_large")
        status, _, _ = request(app, "/api/classify", method="POST", body=b"text", content_type="text/plain")
        self.assertTrue(status.startswith("415"))

    def test_cors_is_exact_and_never_wildcard(self):
        app = AcousticSandboxApp(Settings(allowed_origins=("https://allowed.test",)))
        status, headers, _ = request(app, "/api/config", origin="https://allowed.test")
        self.assertTrue(status.startswith("200"))
        self.assertEqual(headers["Access-Control-Allow-Origin"], "https://allowed.test")
        self.assertNotEqual(headers["Access-Control-Allow-Origin"], "*")
        status, headers, _ = request(app, "/api/config", origin="https://other.test")
        self.assertTrue(status.startswith("403"))
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_same_origin_request_is_allowed_without_configuration(self):
        status, headers, _ = request(AcousticSandboxApp(), "/api/config", origin="https://sandbox.test")
        self.assertTrue(status.startswith("200"))
        self.assertEqual(headers["Access-Control-Allow-Origin"], "https://sandbox.test")


if __name__ == "__main__":
    unittest.main()
