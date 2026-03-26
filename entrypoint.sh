#!/bin/sh
# This script runs as part of the nginx:alpine default entrypoint.
# It substitutes environment variables into the Nginx configuration template
# and writes the final config before nginx starts.

set -e

# Path to the template and the final config
TEMPLATE="/etc/nginx/conf.d/default.conf.template"
TARGET="/etc/nginx/conf.d/default.conf"

# Perform variable substitution (only ${DATA_FILE_PATH} is expected, but all env vars are allowed)
envsubst < "$TEMPLATE" > "$TARGET"

# Continue with the original entrypoint command
exec "$@"