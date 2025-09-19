FROM timescale/timescaledb:latest-pg17
RUN apk add --no-cache postgresql17-postgis postgresql17-postgis-utils
# Optional: enable page checksums on first init (only affects brand-new volumes)
# ENV POSTGRES_INITDB_ARGS="--data-checksums"
# Optional: lightweight healthcheck
HEALTHCHECK --interval=30s --timeout=3s --retries=5 CMD pg_isready -U "$POSTGRES_USER" || exit 1

