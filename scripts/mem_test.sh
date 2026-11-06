#!/usr/bin/env bash
# Task 3: 50 sequential requests against the container with 1 CPU / 1 GiB; report peak memory.
# Needs the cluster's SeaweedFS reachable: this script opens the port-forward itself.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p results
export AWS_ACCESS_KEY_ID="$(kubectl -n app get secret s3-credentials -o jsonpath='{.data.AWS_ACCESS_KEY_ID}' | base64 -d)"
export AWS_SECRET_ACCESS_KEY="$(kubectl -n app get secret s3-credentials -o jsonpath='{.data.AWS_SECRET_ACCESS_KEY}' | base64 -d)"
kubectl -n data port-forward --address 0.0.0.0 svc/seaweedfs 8333:8333 >/dev/null 2>&1 & PF=$!
docker rm -f parser-mem >/dev/null 2>&1 || true
trap 'kill $PF 2>/dev/null || true; docker rm -f parser-mem >/dev/null 2>&1 || true' EXIT
sleep 3
docker run -d --name parser-mem --cpus=1 --memory=1g --memory-swap=1g -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -e MODEL_URI=s3://models/v1/ -e MODEL_VERSION=v1 -e MAX_NEW_TOKENS=64 \
  -e S3_ENDPOINT=http://host.docker.internal:8333 \
  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY parser-service:local >/dev/null
until [ "$(curl -s -o /dev/null -w '%{http_code}' localhost:8000/readyz)" = "200" ]; do sleep 2; done
PEAK=0
{
  for i in $(seq 1 50); do
    TEXT="$(sed -n "${i}p" data/validation.jsonl | python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["text"])')"
    curl -s -o /dev/null -w "request $i: %{http_code}\n" -X POST localhost:8000/parse \
      -H 'Content-Type: application/json' -d "{\"text\": \"$TEXT\"}"
    MEM="$(docker stats --no-stream --format '{{.MemUsage}}' parser-mem | cut -d/ -f1 | tr -d ' ')"
    echo "memory after request $i: $MEM"
  done
  echo "OOMKilled: $(docker inspect -f '{{.State.OOMKilled}}' parser-mem)"
  echo "cgroup peak memory (bytes): $(docker exec parser-mem cat /sys/fs/cgroup/memory.peak 2>/dev/null || echo n/a)"
} | tee results/memory_test.txt
