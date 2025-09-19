FROM timescale/timescaledb:latest-pg17

RUN apk update && apk add --no-cache \
    postgis \
    postgis-utils \
    postgresql17-contrib

HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
  CMD pg_isready -U "$POSTGRES_USER" || exit 1
