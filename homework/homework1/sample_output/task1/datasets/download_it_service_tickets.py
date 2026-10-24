# Download the IT service ticket classification dataset from Kaggle and save it locally.
import re
import shutil
from pathlib import Path

import kagglehub
import pandas as pd

from _common import DATA_DIR, DATA_DIRS, save_sample, sha256, update_manifest

NAME = "it_service_tickets"                                   
REF = "adisongoh/it-service-ticket-classification-dataset"   
CSV_NAME = "all_tickets_processed_improved_v3.csv"            
PARQUET_NAME = Path(CSV_NAME).with_suffix(".parquet").name    
FILE = DATA_DIR / NAME / CSV_NAME                             



def download() -> str:
    """Download with kagglehub, copy the CSV to DATA_DIR, and return the Kaggle version."""
    path = Path(kagglehub.dataset_download(REF))              
    print("Path to dataset files:", path)

    match = re.search(r"versions/(\d+)", str(path))           
    version = match.group(1) if match else "unknown"

    src = next(path.rglob(CSV_NAME), None)                    
    if src is None:
        found = [p.name for p in path.rglob("*.csv")]
        raise SystemExit(f"{CSV_NAME} not found in {path}. CSV files found: {found}")

    #FILE.parent.mkdir(parents=True, exist_ok=True)
    #shutil.copy2(src, FILE)      
    for base in DATA_DIRS:                                   
        dest = base / NAME / CSV_NAME
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"Copied → {dest}")                             
    return version


def main() -> None:
    version = download()
    df = pd.read_csv(FILE)

    
    for base in DATA_DIRS:                                       
        dest = base / NAME / PARQUET_NAME
        df.to_parquet(dest, index=False, engine="pyarrow")
        print(f"Wrote Parquet → {dest}")

    update_manifest(NAME, {
        "source": f"https://www.kaggle.com/datasets/{REF.split('/versions')[0]}",
        "kaggle_ref": REF,
        "kaggle_version": version,                            
        "license": "CC0 1.0",
        "local_file": str(FILE),
        "local_file_parquet": str(DATA_DIR / NAME /PARQUET_NAME),
        "bytes": FILE.stat().st_size,
        "sha256": sha256(FILE),                             
        "rows": len(df),                                       
        "columns": list(df.columns),                           
    })
    save_sample(df, NAME)
    print(f"{NAME}: {len(df):,} rows, Kaggle version {version}")


if __name__ == "__main__":
    main()