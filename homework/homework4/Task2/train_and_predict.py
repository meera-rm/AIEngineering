
from pathlib import Path
import pandas as pd 
import json

from ticket_router import TicketRouter

HERE= Path(__file__).resolve().parent
DATA = HERE.parent / "Task1"   # canonical dataset and split manifest
MODEL_PATH = HERE / "artifacts" / "ticket_router.joblib"
PRED_PATH = HERE / "validation_predictions.csv"
EXPECTED = ["ticket_id", "true_label", "recommended_department","class_scores" ]


def load_train_split():
    """Join the raw source to the official manifest; return train and validation rows."""
    source   = pd.read_csv(DATA/"support_tickets.csv")
    manifest = pd.read_csv(DATA/"split_manifest.csv")
    df = source.merge(manifest[["ticket_id", "split"]], on="ticket_id",
                       how="inner", validate="one_to_one")
    assert len(df) == len(manifest), "Some manifest ticket_ids are missing from the source"
    df["split"] = df["split"].str.strip().str.lower()
    df = df.sort_values("ticket_id").reset_index(drop=True)
    train = df[df["split"] == "train"].reset_index(drop=True)
    validation = df[df["split"] == "validation"].reset_index(drop=True)
    assert len(train) > 0, "Train split is empty"
    assert len(validation) > 0 ,"Validation split is empty"
    return train, validation


def check_reproducible(router, train, validation):
    refit = TicketRouter().fit(train["Body"], train["Department"])

    # compare all labels all validation labels match 
    assert ( refit.predict_labels(validation["Body"])
             == router.predict_labels(validation["Body"]) ).all(), "Refit predictions differ: training is not reproducible"

    #compare 5 full outputs also check scores
    for sample in validation["Body"].iloc[:5]:
        assert refit.predict(sample) == router.predict(sample),"Refit class_scores differ"

    print("Reproducibility checks passed")

def write_predictions(router, validation):

    rows = []
    for tid, body, label in zip(validation["ticket_id"], validation["Body"], validation["Department"]):
        out = router.predict(body)
        rows.append({"ticket_id":tid,
            "true_label":label,
            "recommended_department":out["recommended_department"],
            "class_scores":json.dumps(out["class_scores"])})
    preds=pd.DataFrame(rows)
    preds.to_csv(PRED_PATH, index=False)
    return preds

    
def main():
    # Train
    train, validation = load_train_split()
    print(f"Training rows: {len(train):,}")
    print(f"Validation rows: {len(validation):,}")
    
    router = TicketRouter().fit(train["Body"], train["Department"])
    router.save(MODEL_PATH)
    loaded = TicketRouter.load(MODEL_PATH)
    assert (loaded.predict_labels(validation["Body"]) ==
        router.predict_labels(validation["Body"])).all(), "Loaded model predictions differ"

    
    check_reproducible(router, train, validation)

    preds = write_predictions(router, validation)
    assert len(preds) == len(validation), \
        f"Expected {len(validation)} predictions, got {len(preds)}"
    assert list(preds.columns) == EXPECTED,  \
        f"Columns are {list(preds.columns)}"
    assert preds["ticket_id"].is_unique,\
        f"{preds['ticket_id'].duplicated().sum()} duplicate ticket_ids in the predictions, e.g. " \
        f"{preds.loc[preds['ticket_id'].duplicated(), 'ticket_id'].head(5).tolist()}"
    print(f"Predictions written: {len(preds):,} rows → {PRED_PATH.name}")
   

if __name__ == "__main__":
    main()
