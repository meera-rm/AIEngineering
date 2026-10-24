# Datasets

Task 1 raw data is not included; it can be recreated exactly from pinned versions. The Tobi-Bueck raw parquet used by Tasks 2 and 3 is bundled in `../../task2/tobibueck_dataset/`. Paths in `manifest.json` are relative to the project root (the download scripts write absolute paths when re-run).

1. `pip install -r ../../materials/requirements.txt` (plus `datasets`, `huggingface_hub`, `kagglehub`, `pyarrow`, which the download scripts import)
2. Download the Kaggle dataset (free account required) into `~/hw1_data/it_service_tickets/`:
   - https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset → Download → unzip, or
   - `kaggle datasets download -d adisongoh/it-service-ticket-classification-dataset --unzip -p ~/hw1_data/it_service_tickets`
3. `python datasets/download_it_service_tickets.py
   python datasets/download_bitext.py
   python datasets/download_tobi_bueck.py`

Set `DATA_DIR` to use a different location than `~/hw1_data`.

- `manifest.json`: retrieval date, Hugging Face commit hashes, row counts, and the SHA-256
  checksum of the Kaggle file, so the exact data analyzed can be verified.
- `<name>/SOURCE.md`: provenance, license, and attribution for each dataset.
- `<name>/sample_20.csv`: 20-row preview (`random_state=42`), shared under each dataset's license.