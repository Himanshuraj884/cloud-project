"""Teacher labelling worker.

Env: SHARD_INDEX (from 0), SHARD_COUNT, S3_ENDPOINT, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
     OLLAMA_URL, TEACHER_MODEL. Optional: POOL_KEY, OUT_PREFIX, UPLOAD_EVERY.

Takes the commands whose 0-based line number % SHARD_COUNT == SHARD_INDEX, asks the teacher,
and writes {"id", "text", "teacher_raw"} lines to datasets/teacher/shard-<SHARD_INDEX>.jsonl.
Progress is uploaded regularly and a restarted worker resumes where it stopped.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s3util  # noqa: E402
from shard import select_shard  # noqa: E402
from teacher import ask_teacher, load_prompt  # noqa: E402


def main():
    idx = int(os.environ["SHARD_INDEX"])
    count = int(os.environ["SHARD_COUNT"])
    pool_key = os.environ.get("POOL_KEY", "commands_pool.jsonl")
    out_key = f"{os.environ.get('OUT_PREFIX', 'teacher')}/shard-{idx}.jsonl"
    every = int(os.environ.get("UPLOAD_EVERY", "25"))

    s3 = s3util.client()
    prompt = load_prompt()
    lines = [ln for ln in s3util.get_text(s3, "datasets", pool_key).splitlines() if ln.strip()]
    mine = [(n, json.loads(ln)) for n, ln in select_shard(lines, idx, count)]

    done = {}
    previous = s3util.get_text_or_none(s3, "datasets", out_key)
    if previous:
        for ln in previous.splitlines():
            if ln.strip():
                rec = json.loads(ln)
                done[rec["id"]] = rec
    print(f"shard {idx}/{count}: {len(mine)} commands, {len(done)} already done", flush=True)

    start = time.time()
    for k, (_, cmd) in enumerate(mine, 1):
        if cmd["id"] in done:
            continue
        raw = ask_teacher(cmd["text"], prompt)
        done[cmd["id"]] = {"id": cmd["id"], "text": cmd["text"], "teacher_raw": raw}
        if k % every == 0:
            upload(s3, out_key, mine, done)
            print(f"shard {idx}: {k}/{len(mine)} ({time.time() - start:.0f}s)", flush=True)
    upload(s3, out_key, mine, done)
    print(f"shard {idx}: finished {len(done)} records", flush=True)


def upload(s3, key, mine, done):
    body = "".join(
        json.dumps(done[c["id"]], ensure_ascii=False) + "\n" for _, c in mine if c["id"] in done
    )
    s3util.put_text(s3, "datasets", key, body)


if __name__ == "__main__":
    main()
