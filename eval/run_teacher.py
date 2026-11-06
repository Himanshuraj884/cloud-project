"""Run the teacher (same prompt and settings as Task 1) on validation.jsonl.
  python eval/run_teacher.py data/validation.jsonl results/teacher_predictions.jsonl"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "worker"))
from teacher import ask_teacher, load_prompt  # noqa: E402

gold, out_path = sys.argv[1], sys.argv[2]
prompt = load_prompt()
os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
with open(gold, encoding="utf-8") as f, open(out_path, "w", encoding="utf-8") as out:
    for ln in f:
        if ln.strip():
            g = json.loads(ln)
            out.write(json.dumps({"id": g["id"], "prediction": ask_teacher(g["text"], prompt)},
                                 ensure_ascii=False) + "\n")
print("wrote", out_path)
