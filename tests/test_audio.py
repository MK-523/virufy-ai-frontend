import tempfile
import unittest
from pathlib import Path

from acoustic_sandbox.audio import AudioValidationError, analyze_wav
from acoustic_sandbox.synthetic import generate_fixture_bytes, generate_samples, wav_bytes


class AudioPipelineTest(unittest.TestCase):
    def _write(self, payload):
        temporary = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temporary.write(payload)
        temporary.close()
        self.addCleanup(Path(temporary.name).unlink, missing_ok=True)
        return Path(temporary.name)

    def test_feature_extraction_is_deterministic(self):
        path = self._write(generate_fixture_bytes("steady_tone", variant=2))
        first = analyze_wav(path)
        second = analyze_wav(path)
        self.assertEqual(first, second)

    def test_non_wav_is_rejected(self):
        path = self._write(b"not a wave file")
        with self.assertRaises(AudioValidationError):
            analyze_wav(path)

    def test_short_wav_is_rejected(self):
        path = self._write(wav_bytes(generate_samples("steady_tone", duration_seconds=0.1)))
        with self.assertRaisesRegex(AudioValidationError, "at least"):
            analyze_wav(path)

    def test_valid_fixture_has_bounded_metadata_and_features(self):
        path = self._write(generate_fixture_bytes("broadband_texture"))
        result = analyze_wav(path)
        self.assertEqual(result.metadata.sample_rate_hz, 16_000)
        self.assertEqual(result.metadata.channels, 1)
        self.assertAlmostEqual(result.metadata.duration_seconds, 1.0)
        for value in result.features.to_dict().values():
            self.assertGreaterEqual(value, 0.0)


if __name__ == "__main__":
    unittest.main()
