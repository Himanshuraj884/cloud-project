"""Check every command id in the pool appears in exactly one shard output (no gaps, no repeats).
Usage: python scripts/verify_shards.py data/commands_pool.jsonl DIR_WITH_shard-N.jsonl"""
import glob
import json
import os
import sys
from collections import Counter

pool = [json.loads(ln)["id"] for ln in open(sys.argv[1], encoding="utf-8") if ln.strip()]
seen = Counter()
for p in sorted(glob.glob(os.path.join(sys.argv[2], "shard-*.jsonl"))):
    ids = [json.loads(ln)["id"] for ln in open(p, encoding="utf-8") if ln.strip()]
    print(f"{os.path.basename(p)}: {len(ids)} records")
    seen.update(ids)
missing = [i for i in pool if i not in seen]
repeated = [i for i, c in seen.items() if c > 1]
extra = [i for i in seen if i not in set(pool)]
print(f"pool={len(pool)} covered={len(seen)} missing={len(missing)} "
      f"repeated={len(repeated)} extra={len(extra)}")
sys.exit(0 if not (missing or repeated or extra) and len(pool) == sum(seen.values()) else 1)
