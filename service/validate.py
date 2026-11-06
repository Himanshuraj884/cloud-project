"""Validate a model output against data/schema.json (copied into the image as service/schema.json)."""
import json
import os

_PATH = os.environ.get("SCHEMA_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.json"))
with open(_PATH, encoding="utf-8") as _f:
    SCHEMA = json.load(_f)
KEYS = SCHEMA["keys"]
INTENTS = set(SCHEMA["intents"])


def parse_output(raw):
    """Return the parsed dict if `raw` is a valid output, else None."""
    try:
        obj = json.loads(raw.strip())
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None
    if not isinstance(obj, dict) or set(obj.keys()) != set(KEYS):
        return None
    if obj["intent"] not in INTENTS:
        return None
    for k in ("date", "time", "place"):
        if obj[k] is not None and not isinstance(obj[k], str):
            return None
    return {k: obj[k] for k in KEYS}
