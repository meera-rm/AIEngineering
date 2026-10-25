from pathlib import Path
import pandas as pd 
import json


HERE= Path(__file__).resolve().parent
PRED_PATH = HERE / "validation_predictions.csv"
DATA = HERE.parent / "Task1"   # canonical dataset and split manifest
MANIFEST_PATH = DATA / "split_manifest.csv"


SHORT = {
    "Billing and Payments": "Billing",
    "Customer Service": "CustSvc",
    "General Inquiry": "GenInq",
    "Human Resources": "HR",
    "IT Support": "IT",
    "Product Support": "Product",
    "Returns and Exchanges": "Returns",
    "Sales and Pre-Sales": "Sales",
    "Service Outages and Maintenance": "Outages",
    "Technical Support": "TechSup",
}

def confusion_matrix(y_true, y_pred, labels) -> pd.DataFrame:
    colms = pd.DataFrame(0, index=labels,columns=labels)
    for t, p in zip(y_true, y_pred):  
        colms.loc[t, p] = colms.loc[t, p] + 1
    return colms

def one_vs_rest(cm) -> pd.DataFrame:
    rows = []
    for c in cm.index:
        tp = cm.loc[c, c]
        fn = cm.loc[c].sum() - tp
        fp = cm[c].sum() - tp
        tn = cm.values.sum() - tp - fn - fp
        assert min(tp, fp, fn, tn) >= 0, f"Negative count for {c}"
        rows.append({"department": c, "TP": int(tp), "FP": int(fp),
                     "FN": int(fn), "TN": int(tn)})
    return pd.DataFrame(rows)  

def safe_div(a, b):
    if b == 0:
        return 0.0
    return a / b


def per_class_metrics(ovr):

    rows =[]
    
    for _, r in ovr.iterrows():

        department = r["department"]
        tp = r["TP"]
        fp = r["FP"]
        fn = r["FN"]
        tn = r["TN"]

        support = tp + fn 
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1=safe_div(2 * precision * recall, precision + recall)

        if (tp + fp == 0 ) :
            print (f"precision set to 0 for {department} (never predicted)")
       
        rows.append({"department":department, "support":support, 
                    "precision":precision, "recall":recall, "f1":f1,
                    "TP":tp, "FP":fp, "FN":fn, "TN":tn})
        

    return pd.DataFrame(rows) 



def top2_accuracy(df):
    hits = 0
    for true, scores in zip(df["true_label"], df["class_scores"]):
        ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        top2 =  [ranked[0][0], ranked[1][0]]
        #top2 = [name for name, score in ranked[:2]]
        if true in top2: hits += 1
    return hits / len(df)


def summary_metrics(per_class, df):

    accuracy =  per_class["TP"].sum() / per_class["support"].sum()
    macro_precision = per_class["precision"].mean()
    macro_recall    = per_class["recall"].mean()
    macro_f1        = per_class["f1"].mean()
    weighted_f1     = (per_class["support"]* per_class["f1"]).sum() / per_class["support"].sum()
    top2            = top2_accuracy(df)

    d = {
    "accuracy": accuracy,
    "macro_precision": macro_precision,
    "macro_recall": macro_recall,
    "macro_f1": macro_f1,
    "weighted_f1": weighted_f1,
    "top2_accuracy": top2,
    }
    return pd.DataFrame(list(d.items()) , columns=["metric", "value"])



def word_count(body: pd.Series) -> pd.Series:
    """Number of whitespace-separated words in each Body (missing -> 0)."""
    return body.fillna("").str.split().str.len()


def slice_cut_points(source: pd.DataFrame) -> tuple[float, float]:
    """33rd / 67th percentile of word count on the canonical TRAINING tickets."""
    manifest = pd.read_csv(MANIFEST_PATH)
    manifest["split"] = manifest["split"].str.strip().str.lower()
    train_ids = manifest.loc[manifest["split"] == "train", "ticket_id"]

    train = source[source["ticket_id"].isin(train_ids)]
    assert len(train) == len(train_ids), "Some training ticket_ids are missing from the source"

    q1, q2 = word_count(train["Body"]).quantile([1/3, 2/3])
    return q1, q2



def main():
  

    source   = pd.read_csv(DATA/"support_tickets.csv")
    #(HERE.parent / "Task2" / "validation_predictions.csv")
    predictions = pd.read_csv( PRED_PATH)

    df = predictions.merge(source[["ticket_id","Body"]], on="ticket_id",
                        how="left", validate="one_to_one")
    df["class_scores"] = df["class_scores"].apply(json.loads)
    assert len(df) == len(predictions), "Join changed the number of prediction rows"
    print(f"Loaded {len(df):,} predictions; {df['Body'].isna().sum()} have no Body")
    assert df["Body"].isna().sum() == 0, "Some tickets have no Body"

    labels = sorted(df["true_label"].unique())
    assert set(df["recommended_department"]) <= set(labels), "Model predicted a department not in true_label"
    conf_matrix = confusion_matrix(df["true_label"],df["recommended_department"] ,labels)
    assert len(labels) == 10, f"Expected 10 departments, got {len(labels)}"
    assert len(df) == conf_matrix.values.sum(),"Confusion matrix total doesn't match the number of predictions"
    print("Confusion matrix:")
    #print(conf_matrix.to_string())
    assert set(SHORT) == set(labels), "SHORT is missing or misspelling a department"
    print(conf_matrix.rename(index=SHORT, columns=SHORT).to_string())

    ovr = one_vs_rest(conf_matrix)
    assert ovr["FP"].sum() == ovr["FN"].sum(), "Every error should be one FP and one FN"
    assert ovr["TP"].sum() == (df["true_label"] == df["recommended_department"]).sum(), "TP total != correct predictions"
    print(ovr.replace({"department": SHORT}).to_string(index=False))

    per_class = per_class_metrics(ovr)
    assert per_class["support"].sum() == len(df),"Support doesn't add up to the number of tickets"
    m = per_class[["precision", "recall", "f1"]]
    assert ((m >= 0) & (m <= 1)).all().all(), "A metric is outside 0–1"
    print(per_class.replace({"department": SHORT}).round(3).to_string(index=False))


    summary = summary_metrics(per_class, df)
    s = dict(zip(summary["metric"], summary["value"])) 

    # 1. Two independent ways to compute accuracy must agree
    direct_acc = (df["true_label"] == df["recommended_department"]).mean()
    assert abs(s["accuracy"] - direct_acc) < 1e-9, \
    f"Accuracy mismatch: {s['accuracy']} vs {direct_acc}"

    # 2. Top-2 always includes the top-1 pick, so it can't be lower
    assert s["top2_accuracy"] >= s["accuracy"], \
    f"top2 ({s['top2_accuracy']:.3f}) < accuracy ({s['accuracy']:.3f})"

    # 3. Every summary value is a proportion
    assert summary["value"].between(0, 1).all(), \
    f"Value outside 0–1:\n{summary[~summary['value'].between(0, 1)]}"

    print(summary.round(3).to_string(index=False))

    # word count of each VALIDATION ticket
    df["words"] = word_count(df["Body"])

    #  slice cut points from TRAINING data only
    q1, q2 = slice_cut_points(source)
    print(f"Slice cut points (train word counts): short <= {q1:.0f} < medium <= {q2:.0f} < long")

    df["words"] = word_count(df["Body"])
    df["slice"] = pd.cut(df["words"], bins=[-1, q1, q2, float("inf")],
                     labels=["short", "medium", "long"])

    assert df["slice"].notna().all(), "Some tickets were not assigned a slice"
    print(df["slice"].value_counts().reindex(["short", "medium", "long"]).to_string())
    
        # 5d: same metrics for each body-length slice
    slice_summaries = []
    slice_per_class = []

    for name in ["short", "medium", "long"]:
        sub = df[df["slice"] == name]

        cm  = confusion_matrix(sub["true_label"], sub["recommended_department"], labels)
        slice_ovr = one_vs_rest(cm)   # own name, so the overall `ovr` saved below isn't overwritten
        pc  = per_class_metrics(slice_ovr)
        sm  = summary_metrics(pc, sub)

        assert cm.values.sum() == len(sub), f"{name}: confusion matrix total != slice size"
        assert pc["support"].sum() == len(sub), f"{name}: support total != slice size"

        sm["slice"] = name
        pc["slice"] = name
        slice_summaries.append(sm)
        slice_per_class.append(pc)

    slice_summary = pd.concat(slice_summaries, ignore_index=True)
    slice_pc      = pd.concat(slice_per_class, ignore_index=True)

    # side-by-side view: one row per metric, one column per slice (+ overall)
    table = slice_summary.pivot(index="metric", columns="slice", values="value")
    table = table[["short", "medium", "long"]]
    table["overall"] = summary.set_index("metric")["value"]
    print("Summary metrics by body-length slice:")
    print(table.round(3).to_string())



    # save tables as static CSVs (full department names)
    conf_matrix.to_csv(HERE / "confusion_matrix.csv", index_label="true \\ predicted")
    ovr.to_csv(HERE / "one_vs_rest.csv", index=False)
    per_class.round(4).to_csv(HERE / "per_class_metrics.csv", index=False)
    summary.round(4).to_csv(HERE / "summary_metrics.csv", index=False)
    table.round(4).to_csv(HERE / "slice_metrics.csv")
    slice_pc.round(4).to_csv(HERE / "slice_per_class_metrics.csv", index=False)
    print("Saved 6 CSV files to", HERE.name)




    

if __name__ == "__main__":
    main()