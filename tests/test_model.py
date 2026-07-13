import hashlib
import unittest

from acoustic_sandbox.audio import extract_features
from acoustic_sandbox.model import AcousticSandboxModel
from acoustic_sandbox.synthetic import SYNTHETIC_CLASSES, generate_fixture_bytes, generate_samples


class SyntheticModelTest(unittest.TestCase):
    def test_each_unseen_variant_maps_to_its_neutral_synthetic_class(self):
        model = AcousticSandboxModel()
        for class_id in SYNTHETIC_CLASSES:
            with self.subTest(class_id=class_id):
                result = model.classify(extract_features(generate_samples(class_id, variant=8)))
                self.assertEqual(result.class_id, class_id)

    def test_fixture_bytes_are_reproducible(self):
        first = generate_fixture_bytes("broadband_texture", variant=3)
        second = generate_fixture_bytes("broadband_texture", variant=3)
        self.assertEqual(hashlib.sha256(first).digest(), hashlib.sha256(second).digest())

    def test_model_training_is_deterministic(self):
        first = AcousticSandboxModel()
        second = AcousticSandboxModel()
        self.assertEqual(first.centroids, second.centroids)
        self.assertEqual(first.scales, second.scales)


if __name__ == "__main__":
    unittest.main()
