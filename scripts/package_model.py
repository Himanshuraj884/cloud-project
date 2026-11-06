"""Package a trained model directory for release and object storage.
  python scripts/package_model.py artifacts/v1 v1
Creates dist/model-v1.tar.gz (the GitHub Release asset) and models/v1/model.sha256, whose first
field is the SHA-256 of that very tar.gz. Also writes models/v1/version_info.json."""
import hashlib
import io
import os
import shutil
import sys
import tarfile

src, version = sys.argv[1], sys.argv[2]
os.makedirs("dist", exist_ok=True)
os.makedirs(f"models/{version}", exist_ok=True)
tar_path = f"dist/model-{version}.tar.gz"
files = sorted(f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f)))
raw = io.BytesIO()
with tarfile.open(fileobj=raw, mode="w") as tar:        # deterministic: sorted, fixed metadata
    for name in files:
        info = tar.gettarinfo(os.path.join(src, name), arcname=name)
        info.mtime, info.uid, info.gid, info.uname, info.gname = 0, 0, 0, "", ""
        with open(os.path.join(src, name), "rb") as f:
            tar.addfile(info, f)
import gzip  # noqa: E402
with open(tar_path, "wb") as out, gzip.GzipFile(fileobj=out, mode="wb", mtime=0) as gz:
    gz.write(raw.getvalue())
digest = hashlib.sha256(open(tar_path, "rb").read()).hexdigest()
open(f"models/{version}/model.sha256", "w").write(f"{digest}  model-{version}.tar.gz\n")
if os.path.exists(os.path.join(src, "version_info.json")):
    shutil.copy(os.path.join(src, "version_info.json"), f"models/{version}/version_info.json")
print(tar_path, digest)
