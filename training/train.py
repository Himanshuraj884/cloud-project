"""Sequence-level distillation: fine-tune Pythia-70M on teacher replies (CPU only).

  python training/train.py --config training/config.yaml [--subset 50]

Each example is   "Command: <command>\nJSON: <teacher_raw>" + EOS.
The loss is computed on the reply tokens only (the command part is masked with -100).
"""
import argparse
import csv
import json
import os
import platform
import random
import sys

import yaml


def build_example(tok, text, reply, max_len):
    prompt_ids = tok(f"Command: {text}\nJSON:")["input_ids"]
    reply_ids = tok(" " + reply.strip())["input_ids"] + [tok.eos_token_id]
    ids = (prompt_ids + reply_ids)[:max_len]
    labels = ([-100] * len(prompt_ids) + reply_ids)[:max_len]
    return ids, labels


def collate(batch, pad_id):
    import torch

    n = max(len(i) for i, _ in batch)
    ids = torch.full((len(batch), n), pad_id, dtype=torch.long)
    lab = torch.full((len(batch), n), -100, dtype=torch.long)
    att = torch.zeros((len(batch), n), dtype=torch.long)
    for r, (inp, tgt) in enumerate(batch):
        ids[r, : len(inp)] = torch.tensor(inp)
        lab[r, : len(tgt)] = torch.tensor(tgt)
        att[r, : len(inp)] = 1
    return ids, att, lab


def check_versions(cfg):
    import numpy
    import torch
    import transformers

    want = cfg["library_versions"]
    have = {"torch": torch.__version__.split("+")[0], "transformers": transformers.__version__,
            "numpy": numpy.__version__, "pyyaml": yaml.__version__}
    for k, v in have.items():
        if str(want.get(k)) != v:
            sys.exit(f"library mismatch for {k}: config.yaml says {want.get(k)}, installed {v}")
    print("python", platform.python_version(), "| libraries:", have)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--subset", type=int, default=0, help="train on the first N records only")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(args.config, encoding="utf-8"))

    import numpy as np
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, get_linear_schedule_with_warmup

    check_versions(cfg)
    seed = int(cfg["seed"])
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)

    rows = [json.loads(ln) for ln in open(cfg["train_file"], encoding="utf-8") if ln.strip()]
    rows = rows[: int(cfg["max_records"])]          # never more than the first 1,500 records
    if args.subset:
        rows = rows[: args.subset]
    print(f"training on {len(rows)} records")

    tok = AutoTokenizer.from_pretrained(cfg["base_model"])
    tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(cfg["base_model"], torch_dtype=torch.float32)
    data = [build_example(tok, r["text"], r["teacher_raw"], cfg["max_seq_length"]) for r in rows]

    bs, epochs = int(cfg["batch_size"]), int(cfg["epochs"])
    steps = epochs * ((len(data) + bs - 1) // bs)
    opt = torch.optim.AdamW(model.parameters(), lr=float(cfg["learning_rate"]),
                            weight_decay=float(cfg["weight_decay"]))
    sched = get_linear_schedule_with_warmup(opt, int(steps * float(cfg["warmup_ratio"])), steps)
    gen = torch.Generator().manual_seed(seed)

    out_dir = cfg["output_dir"]
    loss_csv = cfg["loss_csv"]
    if args.subset:
        out_dir, loss_csv = f"artifacts/subset{args.subset}", f"artifacts/subset{args.subset}_loss.csv"
    os.makedirs(os.path.dirname(loss_csv) or ".", exist_ok=True)

    model.train()
    history = []
    for ep in range(1, epochs + 1):
        order = torch.randperm(len(data), generator=gen).tolist()
        total, count = 0.0, 0
        for s in range(0, len(order), bs):
            ids, att, lab = collate([data[i] for i in order[s: s + bs]], tok.pad_token_id)
            loss = model(input_ids=ids, attention_mask=att, labels=lab).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            total += loss.item() * ids.shape[0]
            count += ids.shape[0]
        history.append((ep, total / count))
        print(f"epoch {ep}/{epochs}  loss {total / count:.4f}", flush=True)

    with open(loss_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["epoch", "train_loss"])
        w.writerows(history)

    os.makedirs(out_dir, exist_ok=True)
    model.save_pretrained(out_dir)
    tok.save_pretrained(out_dir)
    info = {k: cfg[k] for k in ("model_version", "base_model", "seed", "learning_rate", "batch_size",
                                "epochs", "max_seq_length")}
    info.update(records_used=len(rows), library_versions=cfg["library_versions"],
                final_train_loss=history[-1][1])
    json.dump(info, open(os.path.join(out_dir, "version_info.json"), "w"), indent=2)
    print("saved to", out_dir)


if __name__ == "__main__":
    main()
