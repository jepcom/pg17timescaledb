FROM timescale/timescaledb:latest-pg17

# Install Alpine's PostGIS and contrib
RUN apk update && apk add --no-cache \
    postgis \
    postgresql17-contrib

# Align Alpine's install paths (/usr/...) with this image's PG paths (/usr/local/...)
RUN set -eux; \
  src_share=/usr/share/postgresql/extension; dst_share=/usr/local/share/postgresql/extension; \
  src_lib=/usr/lib/postgresql;            dst_lib=/usr/local/lib/postgresql; \
  mkdir -p "$dst_share" "$dst_lib"; \
  # extension control & SQL files
  for f in postgis* topology* address_standardizer* tiger*; do \
    if [ -e "$src_share/$f.control" ] || ls "$src_share/$f--"* >/dev/null 2>&1; then \
      cp -av "$src_share"/$f* "$dst_share"/; \
    fi; \
  done; \
  # shared libraries
  for f in postgis rtpostgis address_standardizer sfcgal raster; do \
    if ls "$src_lib"/$f* >/dev/null 2>&1; then \
      cp -av "$src_lib"/$f* "$dst_lib"/; \
    fi; \
  done; \
  # liblwgeom is needed by PostGIS
  if ls /usr/lib/liblwgeom* >/dev/null 2>&1; then \
    cp -av /usr/lib/liblwgeom* /usr/local/lib/; \
  fi; \
  # sanity prints
  ls -l "$dst_share" | head -n 20; \
  ls -l "$dst_lib"   | head -n 20

HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
  CMD pg_isready -U "$POSTGRES_USER" || exit 1
