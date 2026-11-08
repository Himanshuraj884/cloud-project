# Runbook for the Kubernetes experiments (save every output into results/)

Standard load test (use a longer --run-time when something is changed during the run):
    locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest

## Not-ready Service has no endpoints (Task 4.2)
    kubectl -n app rollout restart deploy/parser; kubectl -n app get endpoints parser -w   # empty while the model loads

## HPA scale up/down (Task 4.4)  - the HPA must be on; start from 1 replica
    while true; do echo "$(date +%T) cpu=$(kubectl -n app get hpa parser -o jsonpath='{.status.currentMetrics[0].resource.current.averageUtilization}')% current=$(kubectl -n app get hpa parser -o jsonpath='{.status.currentReplicas}') desired=$(kubectl -n app get hpa parser -o jsonpath='{.status.desiredReplicas}') ready_pods=$(kubectl -n app get deploy parser -o jsonpath='{.status.readyReplicas}')"; sleep 10; done | tee results/hpa_watch.txt
    # in one terminal; run the load test in another
Limitation to state: one node, one machine; metrics-server on a laptop reports noisy CPU; no real node-level scaling.

## Rolling update then rollback (Task 4.5), during a longer load test (--run-time 6m)
    kubectl -n app set env deploy/parser MODEL_VERSION=v2 MODEL_URI=s3://models/v2/
    kubectl -n app rollout status deploy/parser
    kubectl -n app rollout undo deploy/parser
    cat results/loadtest_headers.json          # shows v1 again after rollback; failures <= 0.5%

## Recovery (Task 4.6), during load
    kubectl -n app delete pod <one-pod>; kubectl -n app get pods -w

## Cold start (Task 4.7)
    python scripts/coldstart.py 3

## Load balancing (Task 4.8): exactly two Ready replicas, HPA must not scale down in the middle
    kubectl -n app delete hpa parser; kubectl -n app scale deploy/parser --replicas=2   # or keep HPA and rely on load
    kubectl -n app rollout status deploy/parser; make load-test; cat results/loadtest_headers.json

## Task 7
    kubectl top pods -n app            # run repeatedly during the load test; save to results/top_pods.txt
    python scripts/cost.py results/loadtest_stats.csv --replicas 2 --cpu-limit 1 --mem-limit-gib 1 --slo 99
