from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from .audio import AcousticFeatures, extract_features, feature_vector
from .synthetic import SYNTHETIC_CLASSES, generate_samples

FEATURE_ORDER = (
    "rms_energy",
    "peak_amplitude",
    "crest_factor",
    "zero_crossing_rate",
    "mean_absolute_delta",
    "active_ratio",
)
DISPLAY_NAMES = {
    "steady_tone": "Steady tone",
    "pulsed_tone": "Pulsed tone",
    "broadband_texture": "Broadband texture",
}


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    class_id: str
    display_name: str
    relative_scores: Mapping[str, float]
    model_id: str


def _mean(vectors: list[tuple[float, ...]]) -> tuple[float, ...]:
    return tuple(sum(vector[index] for vector in vectors) / len(vectors) for index in range(len(vectors[0])))


class AcousticSandboxModel:
    """Nearest-centroid demo trained only on deterministic synthetic waveforms."""

    model_id = "synthetic-acoustic-centroids-v1"

    def __init__(self) -> None:
        training: dict[str, list[tuple[float, ...]]] = {}
        all_vectors: list[tuple[float, ...]] = []
        for class_id in SYNTHETIC_CLASSES:
            vectors = [
                feature_vector(extract_features(generate_samples(class_id, variant=variant)), FEATURE_ORDER)
                for variant in range(6)
            ]
            training[class_id] = vectors
            all_vectors.extend(vectors)
        self.centroids = {class_id: _mean(vectors) for class_id, vectors in training.items()}
        global_mean = _mean(all_vectors)
        self.scales = tuple(
            max(
                math.sqrt(
                    sum((vector[index] - global_mean[index]) ** 2 for vector in all_vectors)
                    / len(all_vectors)
                ),
                1e-4,
            )
            for index in range(len(FEATURE_ORDER))
        )

    def classify(self, features: AcousticFeatures) -> ClassificationResult:
        vector = feature_vector(features, FEATURE_ORDER)
        distances: dict[str, float] = {}
        for class_id, centroid in self.centroids.items():
            distances[class_id] = math.sqrt(
                sum(
                    ((value - center) / scale) ** 2
                    for value, center, scale in zip(vector, centroid, self.scales, strict=True)
                )
                / len(FEATURE_ORDER)
            )
        weights = {class_id: math.exp(-distance) for class_id, distance in distances.items()}
        total = sum(weights.values())
        scores = {class_id: weights[class_id] / total for class_id in sorted(weights)}
        selected = min(distances, key=lambda class_id: (distances[class_id], class_id))
        return ClassificationResult(
            class_id=selected,
            display_name=DISPLAY_NAMES[selected],
            relative_scores=scores,
            model_id=self.model_id,
        )
