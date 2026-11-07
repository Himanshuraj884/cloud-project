"""Quick check of the teacher prompt/settings on the first N validation commands (needs Ollama).
  python3 scripts/teacher_smoke.py 20"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "worker"))
from teacher import ask_teacher, load_prompt  # noqa: E402

n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
prompt = load_prompt()
ok = 0
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "validation.jsonl")) as f:
    rows = [json.loads(ln) for ln in f if ln.strip()][:n]
for g in rows:
    raw = ask_teacher(g["text"], prompt)
    try:
        json.loads(raw)
        ok += 1
        flag = "ok "
    except ValueError:
        flag = "BAD"
    print(flag, repr(g["text"]), "->", repr(raw))
print(f"valid JSON: {ok}/{len(rows)}")
