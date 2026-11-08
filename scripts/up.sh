#!/usr/bin/env bash
# Build and deploy the whole system (cluster, object storage, model, service).
set -euo pipefail
cd "$(dirname "$0")/.."
scripts/bootstrap_cluster.sh
scripts/fetch_models.sh
docker build -f service/Dockerfile -t parser-service:local .
k3d image import parser-service:local -c cloudproj
kubectl apply -f k8s/app/deployment.yaml
kubectl -n app rollout status deploy/parser --timeout=600s
# wait until the Ingress routes to a ready Pod (Traefik needs a few seconds after the rollout)
for i in $(seq 1 60); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' localhost:8080/readyz)" = 200 ] && break
  sleep 2
done
echo "ready: curl -s -X POST localhost:8080/parse -H 'Content-Type: application/json' -d '{\"text\":\"what is the weather in london\"}'"
