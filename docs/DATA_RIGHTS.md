# Data and audio rights

## Repository fixtures

The maintained package contains source code that deterministically generates
three waveform families. It includes no recorded audio and no third-party
dataset. Generated fixtures may be recreated locally. This upgrade does not
assign a new software or data license; check the repository's applicable terms.

## User uploads

Users must have permission to process every uploaded file. A recording may
contain copyrighted material, voices, personal information, background
conversations, location cues, or other sensitive content even when the primary
sound seems harmless.

Do not commit uploads or derived user features to this repository. Do not use
the sandbox to collect a dataset. A separate data-governance review is required
before any deployment that accepts recordings from other people.

## Historical files

The original prototype is preserved byte-for-byte at its existing paths and in
`legacy/original` for provenance. Those files are excluded from the maintained
package and container. Their labels, dependencies, and behavior do not describe
the current sandbox.
