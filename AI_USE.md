# AI use

## Tools
- Claude (Anthropic chat assistant): used to draft the repository scaffold (worker, clean.py, training
  script, FastAPI service, Dockerfiles, Kubernetes manifests, CI workflow, helper scripts, report template)
  and to review the scaffold against the assignment handout.
- Ollama + Phi-3.5-mini-instruct: the fixed teacher model (produces labels only; not used to write code).

## What the AI was used for
- First drafts and review of the code and configuration listed above, and an explanation of subnetting
  and NACL rules.

## How I checked the output
> Keep only the lines that are true for you at submission time, and add what you actually did.
- [ ] Ran `python tools/nacl_sim.py network/nacl.json network/packets_sample.jsonl --check` and re-derived the subnets by hand.
- [ ] Ran `make lint` and `make test`.
- [ ] Ran `make train SUBSET=50` and read the loss values.
- [ ] Read every Kubernetes manifest and applied it to my own cluster.
- [ ] Compared every number in the report with the files in `results/`.
- Teacher replies are stored exactly as generated; no labels were created or edited by AI or by hand.
