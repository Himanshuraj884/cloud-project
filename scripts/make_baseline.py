"""Save the UNTRAINED Pythia-70M as a release asset for the CI quality-gate demonstration.
  python scripts/make_baseline.py   -> dist/model-baseline.tar.gz
Upload as a release with tag 'baseline-untrained', then run the workflow manually with
release_tag=baseline-untrained and asset_name=model-baseline.tar.gz (the gate must FAIL)."""
import os
import subprocess
import sys

from transformers import AutoModelForCausalLM, AutoTokenizer

AutoModelForCausalLM.from_pretrained("EleutherAI/pythia-70m").save_pretrained("artifacts/baseline")
AutoTokenizer.from_pretrained("EleutherAI/pythia-70m").save_pretrained("artifacts/baseline")
subprocess.run([sys.executable, "scripts/package_model.py", "artifacts/baseline", "baseline"], check=True)
os.replace("models/baseline/model.sha256", "dist/model-baseline.sha256")
