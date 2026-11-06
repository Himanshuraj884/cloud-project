#!/usr/bin/env bash
# Task 1: run the sharded teacher workers in the "pipeline" namespace (Ollama runs on the host:
#   OLLAMA_HOST=0.0.0.0 ollama serve   and   ollama pull phi3.5).
set -euo pipefail
cd "$(dirname "$0")/.."
docker build -f worker/Dockerfile -t parser-worker:local .
k3d image import parser-worker:local -c cloudproj
kubectl -n pipeline delete job teacher-labelling --ignore-not-found
kubectl apply -f k8s/pipeline/worker-job.yaml
echo "follow: kubectl -n pipeline logs -f -l job-name=teacher-labelling --prefix"
echo "wait:   kubectl -n pipeline wait --for=condition=complete job/teacher-labelling --timeout=24h"
