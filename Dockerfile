FROM timescale/timescaledb:latest-pg17

RUN apk update && apk add --no-cache \
  --repository=https://dl-cdn.alpinelinux.org/alpine/v3.21/community \
  --repository=https://dl-cdn.alpinelinux.org/alpine/v3.21/main \
  postgis \
  postgresql17-contrib

HEALTHCHECK --interval=30s --timeout=3s --retries=5 \
  CMD pg_isready -U "$POSTGRES_USER" || exit 1

