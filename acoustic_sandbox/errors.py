class AcousticSandboxError(Exception):
    """Base error for expected sandbox failures."""


class AudioValidationError(AcousticSandboxError):
    """Raised when an uploaded WAV violates the documented input contract."""
