"""Shared helpers for the per-dataset download scripts."""
import hashlib
import json
import os
from datetime import date
from pathlib import Path

import pandas as pd


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "manifest.json"
PROJECT_ROOT = HERE.parents[2]                                        

DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_ROOT / "data"))    
EXTRA_DATA_DIR = Path.home() / "hw1_data"                             
DATA_DIRS = [DATA_DIR, EXTRA_DATA_DIR]                               

for d in DATA_DIRS:
    d.mkdir(parents=True, exist_ok=True)

def sha256(path: Path) -> str:
    """Return the SHA-256 checksum of a file (read in 1 MB chunks)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_sample(df: pd.DataFrame, name: str, n: int = 20, seed: int = 42) -> Path:
    """Save a reproducible n-row preview (CSV + Parquet) into the submission folder."""
    out_dir = HERE / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"sample_{n}.csv"

    sample = df.sample(min(n, len(df)), random_state=seed)        # sample once
    sample.to_csv(out, index=False, encoding="utf-8")             # sample_20.csv
    sample.to_parquet(out.with_suffix(".parquet"), index=False)   # sample_20.parquet
    
    data_sample_dir = DATA_DIR / name
    data_sample_dir.mkdir(parents=True, exist_ok=True)
    sample.to_csv(data_sample_dir / f"sample_{n}.csv", index=False, encoding="utf-8")
    sample.to_parquet(data_sample_dir / f"sample_{n}.parquet", index=False)

    print(f"Saved sample → {out_dir} and {data_sample_dir}")
    return out

def update_manifest(name: str, entry: dict) -> None:
    """Add or replace one dataset's entry in manifest.json, keeping the others."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {"datasets": {}}
    entry["retrieved"] = date.today().isoformat()
    manifest["datasets"][name] = entry
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Updated {MANIFEST} → {name}")
