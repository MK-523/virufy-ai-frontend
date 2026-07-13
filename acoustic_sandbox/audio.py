from __future__ import annotations

import math
import struct
import wave
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from .errors import AudioValidationError

MIN_DURATION_SECONDS = 0.2
MIN_SAMPLE_RATE = 8_000
MAX_SAMPLE_RATE = 48_000
SUPPORTED_SAMPLE_WIDTHS = (1, 2)
SUPPORTED_CHANNELS = (1, 2)


@dataclass(frozen=True, slots=True)
class AudioMetadata:
    sample_rate_hz: int
    channels: int
    sample_width_bytes: int
    frame_count: int
    duration_seconds: float

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AcousticFeatures:
    rms_energy: float
    peak_amplitude: float
    crest_factor: float
    zero_crossing_rate: float
    mean_absolute_delta: float
    active_ratio: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AnalyzedAudio:
    metadata: AudioMetadata
    features: AcousticFeatures


def _decode_pcm(raw: bytes, sample_width: int) -> list[float]:
    if sample_width == 1:
        return [(value - 128) / 128.0 for value in raw]
    if len(raw) % 2:
        raise AudioValidationError("WAV sample data is truncated")
    sample_count = len(raw) // 2
    return [value / 32768.0 for value in struct.unpack(f"<{sample_count}h", raw)]


def _mix_to_mono(samples: Sequence[float], channels: int) -> list[float]:
    if channels == 1:
        return list(samples)
    return [sum(samples[index : index + channels]) / channels for index in range(0, len(samples), channels)]


def extract_features(samples: Sequence[float]) -> AcousticFeatures:
    if len(samples) < 2:
        raise AudioValidationError("audio contains too few samples")
    count = len(samples)
    sum_squares = sum(value * value for value in samples)
    rms = math.sqrt(sum_squares / count)
    peak = max(abs(value) for value in samples)
    crossings = sum(
        1
        for left, right in zip(samples, samples[1:], strict=False)
        if (left < 0 <= right) or (left >= 0 > right)
    )
    mean_delta = sum(
        abs(right - left) for left, right in zip(samples, samples[1:], strict=False)
    ) / (count - 1)
    activity_threshold = max(0.015, rms * 0.45)
    active_ratio = sum(abs(value) >= activity_threshold for value in samples) / count
    return AcousticFeatures(
        rms_energy=rms,
        peak_amplitude=peak,
        crest_factor=peak / max(rms, 1e-12),
        zero_crossing_rate=crossings / (count - 1),
        mean_absolute_delta=mean_delta,
        active_ratio=active_ratio,
    )


def analyze_wav(path: str | Path, *, max_duration_seconds: float = 10.0) -> AnalyzedAudio:
    source = Path(path)
    try:
        with wave.open(str(source), "rb") as handle:
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
            sample_rate = handle.getframerate()
            frame_count = handle.getnframes()
            compression = handle.getcomptype()
            if compression != "NONE":
                raise AudioValidationError("only uncompressed PCM WAV files are supported")
            if channels not in SUPPORTED_CHANNELS:
                raise AudioValidationError("WAV must contain one or two channels")
            if sample_width not in SUPPORTED_SAMPLE_WIDTHS:
                raise AudioValidationError("WAV must use 8-bit or 16-bit PCM samples")
            if not MIN_SAMPLE_RATE <= sample_rate <= MAX_SAMPLE_RATE:
                raise AudioValidationError(
                    f"sample rate must be between {MIN_SAMPLE_RATE} and {MAX_SAMPLE_RATE} Hz"
                )
            duration = frame_count / sample_rate if sample_rate else 0.0
            if duration < MIN_DURATION_SECONDS:
                raise AudioValidationError(f"audio must be at least {MIN_DURATION_SECONDS:.1f} seconds")
            if duration > max_duration_seconds:
                raise AudioValidationError(f"audio must not exceed {max_duration_seconds:g} seconds")
            raw = handle.readframes(frame_count)
    except (EOFError, wave.Error, OSError) as exc:
        raise AudioValidationError("file is not a readable PCM WAV") from exc

    expected_bytes = frame_count * channels * sample_width
    if len(raw) != expected_bytes:
        raise AudioValidationError("WAV sample data is truncated")
    mono = _mix_to_mono(_decode_pcm(raw, sample_width), channels)
    return AnalyzedAudio(
        metadata=AudioMetadata(
            sample_rate_hz=sample_rate,
            channels=channels,
            sample_width_bytes=sample_width,
            frame_count=frame_count,
            duration_seconds=duration,
        ),
        features=extract_features(mono),
    )


def feature_vector(features: AcousticFeatures, order: Iterable[str]) -> tuple[float, ...]:
    values = features.to_dict()
    return tuple(float(values[name]) for name in order)
