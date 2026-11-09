# syntax=docker/dockerfile:1

############################################################
# STAGE 1 — BUILDER
# Tugas stage ini hanya satu: meng-install dependencies Python
# ke dalam prefix /install, agar hasilnya bisa disalin ke stage
# runtime tanpa membawa pip, cache, dan build tool yang berat.
############################################################
FROM python:3.12.7-slim-bookworm AS builder

# Redam output pip yang tidak perlu agar layer tetap ramping & reproducible
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Salin manifest dependencies DULU sebelum source code.
# Layer ini hanya invalid ketika requirements.txt berubah,
# sehingga build ulang karena edit kode tetap memakai cache pip.
COPY backend/requirements.txt ./requirements.txt

# Install ke prefix /install (bukan ke system Python) supaya
# mudah dipindahkan ke stage runtime lewat COPY --from
RUN pip install --prefix=/install -r requirements.txt

############################################################
# STAGE 2 — RUNTIME
# Image final: hanya berisi Python + dependencies hasil build,
# source code, dan frontend statis. Tidak ada pip/cache/build tool.
############################################################
FROM python:3.12.7-slim-bookworm AS runtime

# Praktik baik untuk container Python:
# - tanpa .pyc  - log tidak di-buffer agar muncul di `docker logs`
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Jalankan sebagai non-root user, bukan root di dalam container
RUN groupadd --system appgroup && useradd --system --gid appgroup --create-home appuser

WORKDIR /app

# Ambil hasil install dependencies dari stage builder
COPY --from=builder /install /usr/local

# Salin source code backend dan frontend statis
# (urutan: dependency dulu di atas, source code belakangan)
COPY backend/main.py ./main.py
COPY frontend ./static

USER appuser

EXPOSE 8000

# Healthcheck internal container: pastikan API benar-benar merespons,
# bukan sekadar proses uvicorn hidup
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]

# CMD format exec (JSON array) agar proses uvicorn menjadi PID 1
# dan menerima sinyal SIGTERM dengan benar saat container dihentikan
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
