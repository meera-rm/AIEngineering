"""Download the Bitext Customer Support dataset (Hugging Face), pinned by commit."""
from datasets import load_dataset
from huggingface_hub import HfApi

from _common import DATA_DIR, DATA_DIRS, save_sample, update_manifest

NAME = "bitext"
REPO = "bitext/Bitext-customer-support-llm-chatbot-training-dataset"


def main() -> None:
    commit = HfApi().dataset_info(REPO).sha                  
    df = load_dataset(REPO, revision=commit, split="train").to_pandas()   
    
    tag = f"{NAME}_{commit[:8]}"
    for base in DATA_DIRS:                                    
        dest = base / NAME
        dest.mkdir(parents=True, exist_ok=True)
        df.to_csv(dest / f"{tag}.csv", index=False, encoding="utf-8")
        df.to_parquet(dest / f"{tag}.parquet", index=False, engine="pyarrow")
        print(f"Wrote CSV + Parquet → {dest}")

    out = DATA_DIR / NAME / f"{tag}.csv" 
    update_manifest(NAME, {
        "source": f"https://huggingface.co/datasets/{REPO}",
        "repo": REPO,
        "commit": commit,                                      
        "license": "CDLA-Sharing 1.0",
        "local_file": str(out),
        "rows": len(df),
    })
    save_sample(df, NAME)
    print(f"{NAME}: {len(df):,} rows @ {commit}")


if __name__ == "__main__":
    main()