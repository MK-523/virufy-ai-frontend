# Privacy and security

## Implemented controls

- Only raw requests with WAV content types reach the classifier.
- `Content-Length` is required and checked before the request body is read.
- The default upload limit is 2 MiB.
- The decoded WAV duration is limited to 10 seconds.
- Only uncompressed 8-bit or 16-bit PCM, one or two channels, and sample rates
  from 8–48 kHz are accepted.
- Every request uses an operating-system-created, mode-`0600`, uniquely named
  temporary file.
- Cleanup runs in a `finally` block after success and expected failure.
- Filenames are not used as filesystem paths and are not returned by the API.
- API responses use `Cache-Control: no-store`.
- CORS is same-origin by default. Configured origins are matched exactly;
  wildcard origins are rejected.
- The frontend is protected by a restrictive Content Security Policy plus
  framing, MIME-sniffing, referrer, permissions, and resource-policy headers.
- The container runs Gunicorn as an unprivileged user. No debug server is
  enabled or documented.

## What the service does not provide

The sandbox does not implement authentication, authorization, consent capture,
rate limiting, malware scanning, encrypted durable storage, deletion receipts,
tenant isolation, or audit logging. It should not be exposed publicly without
TLS, proxy-level body/time limits, request throttling, monitoring, and an abuse
response plan.

Temporary deletion reduces retention but cannot guarantee secure erasure from
all operating systems, container layers, swap, crash dumps, infrastructure
logs, or host-level backups. Use non-sensitive synthetic fixtures whenever
possible.

## Configuration

| Environment variable | Default | Purpose |
|---|---:|---|
| `ACOUSTIC_MAX_UPLOAD_BYTES` | `2097152` | Maximum raw request body |
| `ACOUSTIC_MAX_DURATION_SECONDS` | `10` | Maximum decoded WAV duration |
| `ACOUSTIC_ALLOWED_ORIGINS` | empty | Comma-separated exact HTTP(S) origins |
| `ACOUSTIC_TEMP_DIR` | system temp | Ephemeral processing directory |
