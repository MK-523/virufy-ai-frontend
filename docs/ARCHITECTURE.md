# Architecture

```text
Browser
  -> same-origin POST /api/classify (raw WAV)
  -> length and MIME checks
  -> unique private temporary file
  -> PCM WAV structural validation
  -> deterministic acoustic features
  -> synthetic nearest-centroid comparison
  -> neutral JSON response
  -> unconditional temporary-file cleanup
```

The static frontend is packaged inside `acoustic_sandbox/static` and served by
the same WSGI application as the API. This removes cross-service configuration
from the default deployment and makes same-origin CORS the normal path.

The model is rebuilt deterministically in memory from procedural waveforms when
a worker starts. There is no serialized binary model, hidden download, network
dependency, training job, or mutable model state.

## API

### `GET /api/health`

Returns service liveness and explicitly reports `diagnostic_use: false`.

### `GET /api/config`

Returns client-visible upload types and limits.

### `POST /api/classify`

Accepts a raw PCM WAV body with `Content-Type: audio/wav` and a valid
`Content-Length`. The response contains neutral class IDs, relative scores,
basic WAV metadata, inspectable acoustic features, model provenance, and a
non-diagnostic notice.

Multipart forms are intentionally unnecessary; the browser sends the selected
file as the request body. The optional `X-Filename` header is allowed for CORS
preflight compatibility but is ignored by the server.
