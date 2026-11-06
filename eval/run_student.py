"""Generate predictions for validation.jsonl with a local model directory (or a HF model id).
  python eval/run_student.py MODEL_DIR data/validation.jsonl results/xxx_predictions.jsonl"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from service import inference  # noqa: E402


def main(model_dir, gold_path, out_path, max_new=64):
    model, tok = inference.load(model_dir)
    tok.pad_token = tok.eos_token
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(gold_path, encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as out:
        for ln in f:
            if not ln.strip():
                continue
            g = json.loads(ln)
            pred = inference.generate(model, tok, g["text"], max_new)
            out.write(json.dumps({"id": g["id"], "prediction": pred}, ensure_ascii=False) + "\n")
    print("wrote", out_path)


if __name__ == "__main__":
    main(*sys.argv[1:4])
