import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from acoustic_sandbox.cli import main


class CliTest(unittest.TestCase):
    def test_fixture_and_classification_flow(self):
        with tempfile.TemporaryDirectory() as raw_tmp:
            destination = Path(raw_tmp)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["fixtures", "--output-dir", str(destination)]), 0)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(["classify", str(destination / "steady_tone.wav")]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["classification"]["class_id"], "steady_tone")
        self.assertIn("NON-DIAGNOSTIC", result["notice"])


if __name__ == "__main__":
    unittest.main()
