# Non-Diagnostic Acoustic ML Sandbox

> **Synthetic sound-shape demonstration only. This project cannot diagnose,
> screen, treat, triage, or evaluate anyone's health.**

A safe, offline-trained browser-to-Python acoustic ML sandbox. It compares a
short PCM WAV with three neutral procedural waveform families—steady tone,
pulsed tone, and broadband texture—then returns inspectable features and
relative synthetic-class similarities.

No recorded training audio, disease labels, clinical data, pretrained model,
or model download is used.

## What is complete

- one responsive, accessible frontend packaged with the API;
- a zero-dependency PCM WAV feature pipeline;
- a deterministic synthetic nearest-centroid model;
- neutral JSON outputs with explicit non-diagnostic provenance;
- strict type, size, duration, channel, sample-width, and sample-rate limits;
- unique private temporary files with unconditional cleanup;
- same-origin CORS by default and an exact-origin allowlist;
- CSP and additional browser security headers;
- a non-root Gunicorn production container with no debug server;
- synthetic fixtures, model/data/privacy documentation, tests, packaging, and
  continuous integration.

## Run the offline CLI

Python 3.10 or newer is required. Core feature extraction and classification
use only the standard library.

```bash
python -m pip install -e .
acoustic-sandbox fixtures --output-dir generated-fixtures
acoustic-sandbox classify generated-fixtures/steady_tone.wav
```

The output uses `relative_scores`, not medical risk or calibrated confidence.

## Run the web sandbox

Install the production-server extra and start Gunicorn:

```bash
python -m pip install -e '.[server]'
gunicorn --bind 127.0.0.1:8080 --workers 2 --threads 4 acoustic_sandbox.api:application
```

Then visit `http://127.0.0.1:8080`.

Or use Docker:

```bash
docker build -t acoustic-sandbox .
docker run --rm -p 8080:8080 --read-only \
  --tmpfs /tmp/acoustic-sandbox:rw,noexec,nosuid,size=16m \
  acoustic-sandbox
```

## API example

The API intentionally accepts a raw WAV body instead of a multipart form:

```bash
curl --fail-with-body \
  -H 'Content-Type: audio/wav' \
  --data-binary @generated-fixtures/pulsed_tone.wav \
  http://127.0.0.1:8080/api/classify
```

Successful responses include:

- `classification`: a neutral synthetic family;
- `relative_scores`: normalized inverse-distance weights;
- `audio`: duration, sample rate, channels, and sample width;
- `features`: six deterministic acoustic measurements;
- `model`: model ID and synthetic-only training provenance; and
- `notice`: a prominent non-diagnostic warning.

## Input limits

| Constraint | Default |
|---|---:|
| File type | Uncompressed PCM WAV |
| Upload size | 2 MiB |
| Duration | 0.2–10 seconds |
| Sample rate | 8–48 kHz |
| Channels | Mono or stereo |
| Sample width | 8-bit or 16-bit |

See [`docs/PRIVACY_AND_SECURITY.md`](docs/PRIVACY_AND_SECURITY.md) for deployment
controls and remaining risks.

## Development

```bash
python -m pip install -e '.[dev]'
ruff check acoustic_sandbox tests
python -m unittest discover -s tests -v
python -m build
```

CI tests Python 3.10–3.12, exercises the CLI, builds distributions, and builds
the production image.

## Documentation

- [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md): model construction, scope, and limitations
- [`docs/DATA_RIGHTS.md`](docs/DATA_RIGHTS.md): fixture provenance and upload rights
- [`docs/PRIVACY_AND_SECURITY.md`](docs/PRIVACY_AND_SECURITY.md): retention and deployment controls
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): request lifecycle and API contract

## Historical prototype

Every pre-existing executable and source file remains byte-for-byte unchanged
at its original path. Exact snapshots—including the original README—and commit
provenance are kept under `legacy/original`. Those files are historical
artifacts, are excluded from the package and container, and must not be used as
the maintained application.

## Rights and responsible use

No new software license is assigned by this upgrade. Users remain responsible
for checking the repository's applicable terms and for the rights and
sensitivity of files they choose to process.
