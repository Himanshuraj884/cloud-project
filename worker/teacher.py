"""Teacher client: Phi-3.5-mini-instruct served by Ollama (temperature 0, seed 42)."""
import json
import os
import urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
TEACHER_MODEL = os.environ.get("TEACHER_MODEL", "phi3.5")
PROMPT_FILE = os.environ.get(
    "PROMPT_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "teacher_prompt.txt"),
)
# temperature 0 and seed 42 are fixed by the assignment. The stop sequences are a generation setting:
# without them Phi-3.5 answers correctly and then keeps inventing further "Command: ..." turns until the
# token limit, so the reply is not a single JSON object. Replies are stored exactly as generated.
OPTIONS = {"temperature": 0, "seed": 42, "num_predict": 96, "stop": ["\n\n", "\nCommand:", "Command:"]}


def load_prompt(path=PROMPT_FILE):
    with open(path, encoding="utf-8") as f:
        return f.read().strip()


def ask_teacher(command, system_prompt, url=OLLAMA_URL, model=TEACHER_MODEL, timeout=300):
    """Return the teacher's exact reply text (not stripped, not edited)."""
    body = {
        "model": model,
        "stream": False,
        "options": OPTIONS,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Command: " + command},
        ],
    }
    req = urllib.request.Request(
        url.rstrip("/") + "/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))["message"]["content"]
