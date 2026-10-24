"""Download the Tobi-Bueck Customer Support Tickets dataset (Hugging Face), pinned by commit."""

from datasets import load_dataset
from huggingface_hub import HfApi

from _common import DATA_DIR, save_sample, update_manifest

NAME = "tobi_bueck"
REPO = "Tobi-Bueck/customer-support-tickets"


def main() -> None:
    commit = HfApi().dataset_info(REPO).sha                  
    df = load_dataset(REPO, revision=commit, split="train").to_pandas()   

    out = DATA_DIR / NAME    
    out.mkdir(parents=True, exist_ok=True)
   

  
    language = df["language"].astype(str).str.strip().str.lower()
    df_en = df[language.eq("en")].reset_index(drop=True)    

    
    tag = f"{NAME}_{commit[:8]}"
    out_csv = out / f"{tag}.csv"
    out_parquet = out / f"{tag}.parquet"
    out_en_csv = out / f"{tag}_en.csv"
    out_en_parquet = out / f"{tag}_en.parquet"


  
    df.to_csv(out_csv, index=False, encoding="utf-8")        
    df.to_parquet(out_parquet, index=False, engine="pyarrow")
    df_en.to_csv(out_en_csv, index=False, encoding="utf-8")
    df_en.to_parquet(out_en_parquet, index=False, engine="pyarrow")


    
  
    update_manifest(NAME, {
        "source": f"https://huggingface.co/datasets/{REPO}",
        "repo": REPO,
        "commit": commit,                                     
        "doi": "10.57967/hf/6184",
        "license": "CC BY-NC 4.0",
        "local_file_csv": str(out_csv),
        "local_file_parquet": str(out_parquet),
        "local_file_en_csv": str(out_en_csv),
        "local_file_en_parquet": str(out_en_parquet),
        "rows": len(df),
        "rows_english": len(df_en),                           
    })


    save_sample(df_en, NAME)                              
    print(f"{NAME}: {len(df):,} rows total, {len(df_en):,} English @ {commit}")

if __name__ == "__main__":
    main()