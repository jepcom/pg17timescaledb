# ---- build PostGIS against the Postgres in this image ----
FROM timescale/timescaledb:latest-pg17 AS builder

# build deps
RUN apk add --no-cache --virtual .build-deps \
      build-base wget tar cmake \
      geos-dev proj-dev gdal-dev libxml2-dev json-c-dev protobuf-c-dev protobuf-dev

ENV POSTGIS_VER=3.5.0
WORKDIR /tmp
RUN wget -q https://download.osgeo.org/postgis/source/postgis-${POSTGIS_VER}.tar.gz \
 && tar xzf postgis-${POSTGIS_VER}.tar.gz \
 && cd postgis-${POSTGIS_VER} \
 && ./configure --with-pgconfig=/usr/local/bin/pg_config \
 && make -j"$(nproc)" \
 && make install

# ---- final image: timescale + (runtime libs) + postgis bits copied in ----
FROM timescale/timescaledb:latest-pg17

# runtime libs only (no compilers)
RUN apk add --no-cache geos proj gdal libxml2 json-c protobuf-c

# copy the PostGIS artifacts compiled against our PG
COPY --from=builder /usr/local/lib/postgresql/ /usr/local/lib/postgresql/
COPY --from=builder /usr/local/share/postgresql/extension/ /usr/local/share/postgresql/extension/

HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
  CMD pg_isready -U "$POSTGRES_USER" || exit 1
