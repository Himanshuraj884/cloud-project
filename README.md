# Distilling a command parser (Phi-3.5 -> Pythia-70M) on a local k3d cloud

GitHub repository: **https://github.com/Himanshuraj884/cloud-project**   (tag `final`)
Release with model assets: **https://github.com/Himanshuraj884/cloud-project/releases/tag/v1**
Name / roll number: **Himanshu Raj / 230101084**

## Prerequisites
Docker, k3d, kubectl, Python 3.11, Ollama (teacher), `pip install -r requirements-dev.txt`.

## Layout
`cluster/` k3d config | `k8s/` manifests | `worker/` labelling + `clean.py` | `training/` config + trainer |
`service/` FastAPI + Dockerfile | `eval/` evaluation | `network/` subnets + NACL | `tools/` provided scripts |
`scripts/` deploy/measurement helpers | `results/` evidence | `report/` report | `.github/workflows/ci.yml`

## Build and deploy from a fresh clone (three commands)
    git clone <repo> && cd <repo>
    make up          # cluster + SeaweedFS + buckets + model (from the Release) + image + Deployment/Service/Ingress/HPA
    curl -s -X POST localhost:8080/parse -H 'Content-Type: application/json' -d '{"text":"set an alarm for seven am tomorrow"}'

## Tear down
    make down

## Test
    make lint && make test
    make load-test                      # standard Locust command, writes results/loadtest_*

## How the data and models were produced (reproduce in this order)
    ollama pull phi3.5 && OLLAMA_HOST=0.0.0.0 ollama serve        # separate terminal
    scripts/bootstrap_cluster.sh                                    # cluster, secrets, SeaweedFS, buckets, commands_pool upload
    make label                                                      # 2 sharded workers in namespace "pipeline"
    python scripts/verify_shards.py data/commands_pool.jsonl <dir with shard files>   # coverage check
    make clean-data && make fetch-train                             # datasets/v1/train.jsonl(+.sha256) -> data/
    make train SUBSET=50                                            # smoke test
    make train && make package V=v1                                 # v1
    make train-v2 && make package V=v2                              # v2
    # upload dist/model-v1.tar.gz and dist/model-v2.tar.gz as Release assets (tag v1), then `make up`
    make eval-teacher && make eval                                  # three score reports in results/

Measurement helpers: `scripts/mem_test.sh` (Task 3), `scripts/coldstart.py` (Task 4),
`scripts/cost.py` (Task 7), `docs/RUNBOOK.md` (Task 4 / 7 command sequences).

No credentials are in the repository: S3 keys are generated inside the cluster by `scripts/bootstrap_cluster.sh`.
Model weights are never committed; they are Release assets and live in the `models` bucket.
