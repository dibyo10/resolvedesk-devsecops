#!/usr/bin/env bash
set -euo pipefail
request_url="${URL:-http://localhost:3000/api/tickets}"
request_count="${REQUESTS:-500}"
for ((request_index=0; request_index<request_count; request_index++)); do
  curl --fail --silent --show-error "$request_url" >/dev/null
done
printf 'Completed %s successful requests to %s\n' "$request_count" "$request_url"
