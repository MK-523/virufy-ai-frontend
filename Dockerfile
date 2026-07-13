FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ACOUSTIC_MAX_UPLOAD_BYTES=2097152 \
    ACOUSTIC_MAX_DURATION_SECONDS=10 \
    ACOUSTIC_TEMP_DIR=/tmp/acoustic-sandbox \
    TMPDIR=/tmp/acoustic-sandbox

WORKDIR /app

COPY pyproject.toml README.md MANIFEST.in ./
COPY acoustic_sandbox ./acoustic_sandbox

RUN python -m pip install --no-cache-dir '.[server]' \
    && addgroup --system sandbox \
    && adduser --system --ingroup sandbox --home /nonexistent sandbox \
    && mkdir -p /tmp/acoustic-sandbox \
    && chown sandbox:sandbox /tmp/acoustic-sandbox

USER sandbox
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=2).read()"

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--workers=2", "--threads=4", "--timeout=30", "--worker-tmp-dir=/tmp/acoustic-sandbox", "--max-requests=1000", "--max-requests-jitter=100", "--access-logfile=-", "--error-logfile=-", "acoustic_sandbox.api:application"]
