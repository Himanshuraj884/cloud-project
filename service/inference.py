"""Model loading and generation (CPU). Imported lazily so unit tests do not need torch."""
import os

PROMPT = "Command: {text}\nJSON:"


def load(model_dir):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "1")))
    tok = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir, torch_dtype=torch.float32)
    model.eval()
    return model, tok


def generate(model, tok, text, max_new_tokens=64):
    """Greedy decoding. Returns only the generated text, cut at the first newline."""
    import torch

    enc = tok(PROMPT.format(text=text.strip()), return_tensors="pt")
    with torch.no_grad():
        out = model.generate(
            **enc,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tok.eos_token_id,
            eos_token_id=tok.eos_token_id,
        )
    gen = tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
    return gen.split("\n")[0].strip()
