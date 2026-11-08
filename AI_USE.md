# AI use

Name: Himanshu Raj, roll number 230101084

## Tools
- **Claude (Anthropic chat assistant, used from two accounts):**
  - wrote the first version of the repository scaffold: the labelling worker, `clean.py`, the training script,
    the FastAPI service, Dockerfiles, Kubernetes manifests, helper scripts, the CI workflow and `README.md`;
  - explained subnetting and NACL rules and proposed the subnet table and `network/nacl.json`;
  - helped read my terminal output and fix problems (listed below), each time as a new version of a few files;
  - drafted the report text (`report/report.pdf`) from the result files I gave it.
- **Ollama + Phi-3.5-mini-instruct (`phi3.5`):** the fixed teacher model. It produced the labels only; it was not used to write code.
- **ruff, pytest, gitleaks, Locust, `tools/score.py`, `tools/nacl_sim.py`:** checking tools supplied by the course or open source.

## What was NOT done by AI
- Teacher replies are stored exactly as generated. No label was created, edited or repaired by AI or by hand.
- The model was trained only on the first 1,500 records of the cleaned teacher data. `validation.jsonl` was used only for evaluation
  (one caveat: I chose seed 44 for model v2 after seed 43 gave one invalid reply on a validation command; this is noted in the report).
- All commands were run by me on my own machine and every number in the report comes from a file in `results/`.

## How I checked what the AI gave me
- Ran `make lint` and `make test` (ruff clean, 12 tests passed) and read the tests.
- Ran `make train SUBSET=50` and then `make train`, and read the per-epoch loss values in `training/loss.csv`.
- Ran every Kubernetes step myself and read the output: probes, not-ready endpoints, HPA scale up and down, rolling update with rollback,
  Pod deletion under load, cold starts, load balancing. I kept the failed attempts in `results/`.
- Ran `python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check` (6 of 6 correct) and re-derived the four subnets
  with Python's `ipaddress` module (`results/subnets_check.txt`).
- Checked `input = a + b + c + d + duplicates + kept` (3000 = 6 + 13 + 12 + 212 + 48 + 2709) and re-ran `clean.py` on the saved
  shard files to reproduce the checksum in `train.sha256`.
- Compared SHA-256 of the downloaded Release assets with `models/v1/model.sha256` and `models/v2/model.sha256`.
- Tested `make up` and `make down` from a fresh clone. This found two real bugs (Ingress not ready right after the rollout, and the API server not
  ready right after cluster creation), which were fixed.
- Ran CI on GitHub: a passing run, and a deliberate failure with the untrained Pythia-70M (links in `results/ci_runs.txt`).
- Compared the numbers in the report with the files in `results/` before submitting.

## Mistakes in the AI-generated work that were found and fixed during testing
- Teacher replies kept going after the JSON object (Phi-3.5 invented more "Command:" turns). Fixed with stop sequences and relabelling; the first run was discarded.
- The service ran generation on the async event loop, so health probes stalled under load and my first HPA run failed. Fixed with `run_in_threadpool`.
- The rolling update first failed 2.25% of requests (HTTP 502/500/connection errors). Fixed with a `preStop` sleep and a longer grace period, and by retraining v2.
- The first v2 model produced broken JSON for one validation command. I retrained with another seed and kept the first attempt in `results/v2_attempt1/`.
- `make up` was fragile on a fresh machine (see above). Fixed with explicit waits.
- A command suggested for the Pod-deletion test did not delete any Pod; the Pod names and ages in the output had not changed, so I kept that run as
  `results/attempt1_no_deletion/`, and repeated it.
- The Locust header file path is fixed, so later runs overwrote the rollout and recovery counts. I copied the printed numbers into two clearly labelled
  `*_transcribed.txt` files.
