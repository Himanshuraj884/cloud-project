#!/usr/bin/env bash
# Run a command with a port-forward to SeaweedFS and credentials read from the cluster Secret.
#   scripts/with_s3.sh python3 scripts/s3_tool.py ls datasets
set -euo pipefail
PORT="${S3_LOCAL_PORT:-8333}"
export AWS_ACCESS_KEY_ID="$(kubectl -n app get secret s3-credentials -o jsonpath='{.data.AWS_ACCESS_KEY_ID}' | base64 -d)"
export AWS_SECRET_ACCESS_KEY="$(kubectl -n app get secret s3-credentials -o jsonpath='{.data.AWS_SECRET_ACCESS_KEY}' | base64 -d)"
export S3_ENDPOINT="http://localhost:${PORT}"
kubectl -n data port-forward svc/seaweedfs "${PORT}:8333" >/dev/null 2>&1 &
PF=$!
trap 'kill $PF 2>/dev/null || true' EXIT
for _ in $(seq 1 30); do
  (exec 3<>"/dev/tcp/127.0.0.1/${PORT}") 2>/dev/null && break
  sleep 1
done
"$@"
