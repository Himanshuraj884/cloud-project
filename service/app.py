"""Command-parser service. Port 8000.

Env: MODEL_URI, MODEL_VERSION, S3_ENDPOINT, MAX_NEW_TOKENS (+ FAULT_INJECT for tests).
Credentials arrive as AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY from a Kubernetes Secret.
"""
import json
import logging
import os
import threading

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from service.validate import parse_output

log = logging.getLogger("service")
logging.basicConfig(level=logging.INFO)

# STATE["generate"] is a function text -> raw model output. It is set when the model has loaded.
STATE = {"ready": False, "generate": None, "error": None}
_LOCK = threading.Lock()  # one generation at a time: bounded memory and CPU on a 1-core limit


def _load_model():
    try:
        from service import inference, storage

        dest = os.environ.get("MODEL_DIR", "/tmp/model")
        n = storage.download_model(os.environ["MODEL_URI"], os.environ["S3_ENDPOINT"], dest)
        log.info("downloaded %d model files from %s", n, os.environ["MODEL_URI"])
        model, tok = inference.load(dest)
        max_new = int(os.environ.get("MAX_NEW_TOKENS", "64"))
        STATE["generate"] = lambda text: inference.generate(model, tok, text, max_new)
        STATE["ready"] = True
        log.info("model %s loaded, ready", os.environ.get("MODEL_VERSION"))
    except Exception as exc:  # keep the process alive so /healthz answers and the cause is visible
        STATE["error"] = repr(exc)
        log.exception("model load failed")


def lifespan_start():
    threading.Thread(target=_load_model, daemon=True).start()


app = FastAPI(on_startup=[lifespan_start])


@app.get("/healthz")
def healthz():
    return {"status": "alive"}


@app.get("/readyz")
def readyz():
    if STATE["ready"]:
        return {"status": "ready"}
    return JSONResponse({"status": "loading", "error": STATE["error"]}, status_code=503)


@app.post("/parse")
async def parse(request: Request):
    try:
        body = await request.json()
        text = body["text"]
        if not isinstance(text, str) or not text.strip():
            raise ValueError
    except Exception:
        return JSONResponse({"error": "bad_request"}, status_code=400)
    if not STATE["ready"]:
        return JSONResponse({"error": "model_not_ready"}, status_code=503)

    with _LOCK:
        raw = STATE["generate"](text)
    if os.environ.get("FAULT_INJECT") == "1":
        raw = "not json"
    obj = parse_output(raw)
    if obj is None:
        return JSONResponse({"error": "invalid_model_output"}, status_code=500)

    headers = {
        "X-Model-Version": os.environ.get("MODEL_VERSION", "unknown"),
        "X-Served-By": os.environ.get("HOSTNAME", "unknown"),  # the Pod name inside Kubernetes
    }
    return Response(json.dumps(obj), media_type="application/json", headers=headers)
