"""Clean the teacher shard outputs into datasets/v1/train.jsonl (+ train.sha256).

Rejection reasons, applied in this order (a record is counted under the first one it hits):
  (a) reply is not valid JSON
  (b) reply is not an object with exactly the keys intent, date, time, place
  (c) intent is not one of the eight
  (d) a slot value is neither null nor a non-empty string that appears in the command
Then (e): among the remaining records, a repeated command text keeps only the smallest id.
Output is sorted by id and written deterministically, so the checksum is reproducible.

Usage:
  python worker/clean.py                       # read/write object storage (S3_ENDPOINT + AWS_* env)
  python worker/clean.py --local-dir DIR       # read DIR/shard-*.jsonl, write DIR/v1/train.jsonl
"""
import argparse
import glob
import hashlib
import json
import os
import sys

KEYS = ["intent", "date", "time", "place"]
INTENTS = {
    "alarm_set", "alarm_query", "calendar_set", "calendar_query",
    "calendar_remove", "weather_query", "datetime_query", "recommendation_events",
}


def check_record(rec):
    """Return None if the record is good, else the reason letter 'a'..'d'."""
    try:
        obj = json.loads(rec["teacher_raw"])
    except (json.JSONDecodeError, TypeError):
        return "a"
    if not isinstance(obj, dict) or set(obj.keys()) != set(KEYS):
        return "b"
    if obj["intent"] not in INTENTS:
        return "c"
    text = rec["text"].lower()
    for k in ("date", "time", "place"):
        v = obj[k]
        if v is None:
            continue
        if not isinstance(v, str) or not v.strip() or v.lower() not in text:
            return "d"
    return None


def clean(records):
    """records: iterable of dicts. Returns (kept_records, counts)."""
    records = sorted(records, key=lambda r: r["id"])
    counts = {"input": len(records), "a_invalid_json": 0, "b_bad_keys": 0,
              "c_bad_intent": 0, "d_bad_slot": 0, "duplicates": 0, "kept": 0}
    names = {"a": "a_invalid_json", "b": "b_bad_keys", "c": "c_bad_intent", "d": "d_bad_slot"}
    seen, kept = set(), []
    for rec in records:
        bad = check_record(rec)
        if bad:
            counts[names[bad]] += 1
        elif rec["text"] in seen:
            counts["duplicates"] += 1
        else:
            seen.add(rec["text"])
            kept.append(rec)
    counts["kept"] = len(kept)
    assert counts["input"] == sum(v for k, v in counts.items() if k != "input")
    return kept, counts


def serialise(kept):
    return "".join(
        json.dumps({"id": r["id"], "text": r["text"], "teacher_raw": r["teacher_raw"]},
                   ensure_ascii=False) + "\n"
        for r in kept
    )


def sha256_line(text, name="train.jsonl"):
    return f"{hashlib.sha256(text.encode('utf-8')).hexdigest()}  {name}\n"


def parse_lines(text):
    return [json.loads(ln) for ln in text.splitlines() if ln.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-dir")
    args = ap.parse_args()

    if args.local_dir:
        records = []
        for path in sorted(glob.glob(os.path.join(args.local_dir, "shard-*.jsonl"))):
            with open(path, encoding="utf-8") as f:
                records += parse_lines(f.read())
    else:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import s3util
        s3 = s3util.client()
        keys = [o["Key"] for o in s3.list_objects_v2(Bucket="datasets", Prefix="teacher/")
                .get("Contents", []) if o["Key"].endswith(".jsonl")]
        records = []
        for k in sorted(keys):
            records += parse_lines(s3util.get_text(s3, "datasets", k))

    kept, counts = clean(records)
    body = serialise(kept)
    checksum = sha256_line(body)
    counts_text = json.dumps(counts, indent=2) + "\n"

    if args.local_dir:
        out = os.path.join(args.local_dir, "v1")
        os.makedirs(out, exist_ok=True)
        for name, data in (("train.jsonl", body), ("train.sha256", checksum),
                           ("counts.json", counts_text)):
            with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(data)
    else:
        s3util.put_text(s3, "datasets", "v1/train.jsonl", body)
        s3util.put_text(s3, "datasets", "v1/train.sha256", checksum)
        s3util.put_text(s3, "datasets", "v1/counts.json", counts_text)
    print(counts_text, end="")
    print(checksum, end="")


if __name__ == "__main__":
    main()
