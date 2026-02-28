import os
from src.config import load_cfg
from src.bot import run, approve_and_post

if __name__ == "__main__":
    cfg = load_cfg()
    mode = os.getenv("MODE", "run").strip().lower()
    if mode == "approve":
        raise SystemExit(approve_and_post(cfg))
    raise SystemExit(run(cfg))
