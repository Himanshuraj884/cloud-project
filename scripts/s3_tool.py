"""Tiny S3 CLI for the SeaweedFS endpoint (S3_ENDPOINT + AWS_* env).
  s3_tool.py mkbuckets
  s3_tool.py put-file BUCKET KEY PATH
  s3_tool.py put-dir  BUCKET PREFIX DIR      (uploads regular files in DIR, non-recursive)
  s3_tool.py get-file BUCKET KEY PATH
  s3_tool.py has-prefix BUCKET PREFIX         (exit 0 if any object exists)
  s3_tool.py ls BUCKET [PREFIX]
  s3_tool.py delete-prefix BUCKET PREFIX      (deletes every object under PREFIX)"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "worker"))
import s3util  # noqa: E402

s3 = s3util.client()
cmd, args = sys.argv[1], sys.argv[2:]
if cmd == "mkbuckets":
    have = {b["Name"] for b in s3.list_buckets()["Buckets"]}
    for b in ("datasets", "models"):
        if b not in have:
            s3.create_bucket(Bucket=b)
        print("bucket ok:", b)
elif cmd == "put-file":
    s3.upload_file(args[2], args[0], args[1])
    print("uploaded", args[0] + "/" + args[1])
elif cmd == "put-dir":
    bucket, prefix, d = args
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if os.path.isfile(p):
            s3.upload_file(p, bucket, f"{prefix.rstrip('/')}/{name}")
            print("uploaded", f"{bucket}/{prefix.rstrip('/')}/{name}")
elif cmd == "get-file":
    s3.download_file(args[0], args[1], args[2])
elif cmd == "has-prefix":
    r = s3.list_objects_v2(Bucket=args[0], Prefix=args[1], MaxKeys=1)
    sys.exit(0 if r.get("KeyCount") else 1)
elif cmd == "ls":
    prefix = args[1] if len(args) > 1 else ""
    for o in s3.list_objects_v2(Bucket=args[0], Prefix=prefix).get("Contents", []):
        print(o["Size"], o["Key"])
elif cmd == "delete-prefix":
    bucket, prefix = args
    for o in s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", []):
        s3.delete_object(Bucket=bucket, Key=o["Key"])
        print("deleted", f"{bucket}/{o['Key']}")
