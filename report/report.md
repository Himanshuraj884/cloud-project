# Cloud Computing Mini Project: Knowledge Distillation and Deployment of a Command Parser

Name: Himanshu Raj   Roll number: 230101084   Repository: <GITHUB LINK> (tag `final`)

> Fill every `<<MEASURED: ...>>` from your own runs and the files in `results/`. Keep measured results and
> assumptions separate. Convert this file to `report/report.pdf` (max 8 pages excluding references/appendices).

## 0. Architecture and decisions
Diagram: laptop -> k3d single-node cluster; namespaces `data` (SeaweedFS), `pipeline` (workers),
`app` (service, Ingress, HPA); Ollama teacher on the host; GitHub Actions for CI.
Decisions: sequence-level distillation; strict `clean.py` (no repair of teacher replies); loss on reply tokens only;
CPU-only torch image; model weights only in object storage and Release assets.

## 1. Task 1: Object storage and parallel teacher labelling
Setup: <<k3d config, SeaweedFS in `data`, buckets, prompt file, workers in `pipeline`>>.
Sharding (<= half a page): record i (0-based line number) goes to worker `i mod SHARD_COUNT`; each worker writes its
own object `datasets/teacher/shard-<k>.jsonl`; no overlap and no gap by construction; `scripts/verify_shards.py`
output: <<MEASURED>>. Workers resume from their object after a restart.

| Counts | Value |
|---|---|
| Input records | <<MEASURED>> |
| (a) invalid JSON | <<MEASURED>> |
| (b) wrong keys | <<MEASURED>> |
| (c) intent not in the eight | <<MEASURED>> |
| (d) slot not null / not in command | <<MEASURED>> |
| Duplicates (smallest id kept) | <<MEASURED>> |
| Kept | <<MEASURED>> |
Check: input = a + b + c + d + duplicates + kept. Checksum in `train.sha256`: <<MEASURED>>.
Rules as implemented: checks run in order a, b, c, d; each record is counted once; duplicates are judged among valid records.

## 2. Task 2: Training the student
Config (`training/config.yaml`): seed, learning rate, batch size, epochs, max length, library versions.
Loss per epoch (`training/loss.csv`): <<MEASURED>>. Checksums: v1 <<MEASURED>>, v2 <<MEASURED>>.

| Model | json_validity | intent | date | time | place | full_frame |
|---|---|---|---|---|---|---|
| Teacher (phi3.5) | <<M>> | <<M>> | <<M>> | <<M>> | <<M>> | <<M>> |
| Untrained Pythia-70M | <<M>> | <<M>> | <<M>> | <<M>> | <<M>> | <<M>> |
| Trained student v1 | <<M>> | <<M>> | <<M>> | <<M>> | <<M>> | <<M>> |
Discussion: <<what changed; where the student fails; compare with teacher>>.

Sequence-level vs logit-based distillation (<= 1 page): sequence-level trains the student with ordinary
cross-entropy on the teacher's generated text (hard targets, one sampled/greedy sequence). Logit-based trains the student to match
the teacher's per-token probability distribution (soft targets, e.g. KL divergence). It is not possible here because the
teacher (Phi-3.5, via Ollama) returns only text, and the two models use different tokenizers/vocabularies, so their
output distributions cannot be aligned token by token. Limitation (state one you measured): <<e.g. student copies teacher
mistakes; only 1,500 examples; slot copying errors seen in results/>>.

## 3. Task 3: Container
Endpoints and headers as specified; validation against `schema.json`; `FAULT_INJECT=1` test output: <<MEASURED>>.
Image size: <<MEASURED>> (limit 2 GB); no weights; pinned dependencies. 50 requests at 1 CPU / 1 GiB: <<MEASURED: no OOM>>,
peak memory <<MEASURED>> (evidence: `results/memory_test.txt`).

## 4. Task 4: Kubernetes
Table of results: Ingress check <<M>>; requests/limits; not-ready endpoints evidence <<M>>; HPA evidence 1->2->1 <<M>>;
rolling update failures <<M>> % (<= 0.5%) and X-Model-Version after rollback <<M>>; recovery failures <<M>> % (<= 2%);
cold starts <<M, M, M>> median <<M>> s (log evidence); load balancing per replica <<M>> (each >= 30%).
Limitation (state clearly): the cluster is one node on one laptop; this shows Pod-level recovery only, not fault tolerance
across machines; the HPA cannot add node capacity and its CPU readings are noisy here.

## 5. Task 5: Subnetting and NACL
Table copied from `network/subnets.md`; NACL rule table; `nacl_sim.py` result 6/6. Explanation from `network/subnets.md`.

## 6. Task 6: Reproducibility and CI/CD
`make up` / `make down`; workflow stages lint -> unit tests -> evaluation (Release asset) -> quality gate;
failed-gate run (untrained model): <<LINK>>; passing run: <<LINK>>; gitleaks result: <<MEASURED>>; `AI_USE.md`.

## 7. Task 7: Performance, cost, review
| p50 | p95 | req/s | error rate | cold start |
|---|---|---|---|---|
| <<M>> | <<M>> | <<M>> | <<M>> | <<M>> |
`kubectl top pods` per Pod: <<M>>. Cost per 1,000 requests: show the steps from `scripts/cost.py` <<M>>.
SLO: target <<e.g. 99% success>>, window one load-test run, error budget <<M>> requests, used <<M>>.

| Component | Evidence (measured) | Limitation | Improvement |
|---|---|---|---|
| Data and storage | | | |
| Model quality | | | |
| Latency and throughput | | | |
| Resource utilisation | | | |
| Reliability and recovery | | | |
| Security and cost | | | |

## Assumptions (not measured)
<<list them, e.g. hypothetical rate card, single-node cluster, Ollama on host>>
