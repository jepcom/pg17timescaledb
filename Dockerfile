FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]

FROM timescale/timescaledb:latest-pg17

# 1) Install PostGIS (plus contrib for uuid-ossp, etc.)
RUN apk update && apk add --no-cache postgis postgresql17-contrib

# 2) Copy PostGIS control/SQL and .so files from Alpine's paths (/usr/...)
#    to the places this image's PostgreSQL actually reads (/usr/local/...)
RUN set -eux; \
  SHARED_DST="$(pg_config --sharedir)/extension"; \
  LIB_DST="$(pg_config --pkglibdir)"; \
  mkdir -p "$SHARED_DST" "$LIB_DST"; \
  # control + SQL files (handles versioned dirs e.g. /usr/share/postgresql17/extension)
  for d in /usr/share/postgresql*/extension /usr/share/postgresql/extension; do \
    if [ -d "$d" ]; then \
      find "$d" -maxdepth 1 -type f \( -name 'postgis*.control' -o -name 'postgis*--*.sql' -o -name 'topology*' -o -name 'address_standardizer*' -o -name 'tiger*' \) \
        -exec cp -av {} "$SHARED_DST"/ \; || true; \
    fi; \
  done; \
  # shared libraries (handles versioned libdirs e.g. /usr/lib/postgresql17)
  for d in /usr/lib/postgresql* /usr/lib; do \
    if [ -d "$d" ]; then \
      find "$d" -maxdepth 1 -type f \( -name 'postgis*.so*' -o -name 'rtpostgis*.so*' -o -name 'address_standardizer*.so*' -o -name 'sfcgal*.so*' \) \
        -exec cp -av {} "$LIB_DST"/ \; || true; \
    fi; \
  done; \
  # liblwgeom is required by PostGIS
  if ls /usr/lib/liblwgeom*.so* >/dev/null 2>&1; then cp -av /usr/lib/liblwgeom*.so* /usr/local/lib/; fi; \
  # sanity checks
  test -f "$SHARED_DST/postgis.control"; \
  ls -l "$SHARED_DST" | head -n 20; \
  ls -l "$LIB_DST"   | head -n 20

HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
  CMD pg_isready -U "$POSTGRES_USER" || exit 1
