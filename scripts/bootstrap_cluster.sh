#!/usr/bin/env bash
# Create the cluster (if missing), namespaces, and credentials Secrets. No credential is stored in Git:
# random keys are generated here and live only in the cluster.
set -euo pipefail
cd "$(dirname "$0")/.."
k3d cluster list cloudproj >/dev/null 2>&1 || k3d cluster create --config cluster/k3d.yaml
# a fresh cluster needs a little time before its API, metrics-server and Traefik answer
for i in $(seq 1 90); do
  kubectl get --raw=/readyz >/dev/null 2>&1 && kubectl -n kube-system get deploy traefik metrics-server >/dev/null 2>&1 && break
  sleep 2
done
kubectl wait --for=condition=Ready node --all --timeout=180s
kubectl -n kube-system rollout status deploy/metrics-server --timeout=180s
kubectl -n kube-system rollout status deploy/traefik --timeout=180s
kubectl apply -f k8s/namespaces.yaml
if ! kubectl -n app get secret s3-credentials >/dev/null 2>&1; then
  AK="seaweed$(openssl rand -hex 6)"
  SK="$(openssl rand -hex 20)"
  for ns in app pipeline; do
    kubectl -n "$ns" create secret generic s3-credentials \
      --from-literal=AWS_ACCESS_KEY_ID="$AK" --from-literal=AWS_SECRET_ACCESS_KEY="$SK"
  done
  cat > /tmp/s3.json <<J
{"identities":[{"name":"admin","credentials":[{"accessKey":"$AK","secretKey":"$SK"}],"actions":["Admin","Read","Write","List","Tagging"]}]}
J
  kubectl -n data create secret generic seaweedfs-s3-config --from-file=s3.json=/tmp/s3.json
  rm -f /tmp/s3.json
fi
kubectl apply -f k8s/data/seaweedfs.yaml
kubectl -n data rollout status deploy/seaweedfs --timeout=180s
scripts/with_s3.sh python3 scripts/s3_tool.py mkbuckets
scripts/with_s3.sh python3 scripts/s3_tool.py put-file datasets commands_pool.jsonl data/commands_pool.jsonl
