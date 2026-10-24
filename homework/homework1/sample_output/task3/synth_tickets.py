#!/usr/bin/env python3
#Task 3: 50 synthetic 'Service Outages and Maintenance' tickets (local, deterministic, no LLM).


import argparse, hashlib, json, random, re
from pathlib import Path
from collections import Counter
import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_SOURCE = HERE.parent / "task2" / "tobibueck_dataset" / "tobi_bueck_ddf1c81a.parquet"
SEED, N_RECORDS, GENERATOR_VERSION = 42, 50, "recombine-v1"
TARGET = "Service Outages and Maintenance"
RAW_COLS = ["subject", "body", "answer", "type", "queue", "priority",
            "language", "version"] + [f"tag_{i}" for i in range(1, 9)]
MIN_WORDS, MIN_SENTENCES = 12, 3
MIN_SUBSTRING_WORDS = 6
SUBJECT_RATE, P_TWO_MIDDLES = 1 - 0.1288, 0.4

OUTAGE = re.compile(r"\b(outages?|downtime|down|maintenance|disruptions?|interruptions?|unavailab\w*|"
                    r"offline|restor\w*|uptime|service (?:failure|degradation))\b", re.I)
OFF_TOPIC = re.compile(r"\b(refunds?|invoices?|billing|returns?|exchanges?|hiring|recruit\w*|payroll|salary|"
                       r"pricing|quotes?|purchase|marketing|seo|investments?)\b", re.I)
PLACEHOLDER = re.compile(r"<[a-z_]+>|\[[A-Z][A-Za-z ]*\]|\\n")
HTML = re.compile(r"<br\s*/?>|</?p>", re.I)
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
WORD = re.compile(r"\b[\w']+\b")
SYNONYMS = {"issue": ["issue", "problem"], "please": ["please", "kindly"],
            "urgent": ["urgent", "time-sensitive"], "disruption": ["disruption", "interruption"],
            "resolve": ["resolve", "fix"], "assistance": ["assistance", "help"]}


def is_missing(v):
    return v is None or (not isinstance(v, str) and pd.isna(v))

def clean(t):
    return "" if is_missing(t) else re.sub(r"\s+", " ", HTML.sub(" ", str(t))).strip()

def sentences(t):
    return [s.strip() for s in SENT_SPLIT.split(t or "") if s.strip()]

def source_id(row):  # Task 2 ID scheme
    lines = [f"{c}=<NULL>" if is_missing(row[c]) else f"{c}={row[c]}" for c in sorted(RAW_COLS)]
    return "tb_" + hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:12]


def load_english(path):
    df = pd.read_parquet(path)
    df["record_id"] = [source_id(r) for r in df[RAW_COLS].to_dict("records")]
    en = df[df["language"] == "en"].copy()
    en["subject_c"], en["body_c"] = en["subject"].map(clean), en["body"].map(clean)
    en["ticket_text"] = (en["subject_c"] + "\n" + en["body_c"]).str.strip()
    return en.sort_values("record_id").reset_index(drop=True)


def select_seeds(en):
    seeds, seen, excluded = [], set(), Counter()
    for r in en[en["queue"] == TARGET].to_dict("records"):
        body, text = r["body_c"], r["ticket_text"]
        sents = sentences(body)
        checks = [("too_short", len(body.split()) < MIN_WORDS),
                  ("too_few_sentences", len(sents) < MIN_SENTENCES),
                  ("placeholder_or_escaped_newline", bool(PLACEHOLDER.search("" if is_missing(r["body"]) else str(r["body"])))),
                  ("no_outage_vocabulary", not OUTAGE.search(text)),
                  ("off_topic_terms", bool(OFF_TOPIC.search(text))),
                  ("duplicate_text", text.lower() in seen)]
        failed = next((name for name, bad in checks if bad), None)
        if failed:
            excluded[failed] += 1
            continue
        seen.add(text.lower())
        seeds.append({"id": r["record_id"], "subject": r["subject_c"], "sents": sents,
                      "type": r["type"],
                      "priority": r["priority"]})
    return seeds, excluded


def compose(rng, group):
    k_mid = 2 if rng.random() < P_TWO_MIDDLES else 1
    picks = rng.sample(group, 2 + k_mid)                      # all parts from different seeds
    opener, closer, mids = picks[0], picks[1], picks[2:]
    parts = [opener["sents"][0]] + [rng.choice(m["sents"][1:-1]) for m in mids] + [closer["sents"][-1]]
    topic = mids[0]
    subject = topic["subject"] if topic["subject"] and rng.random() < SUBJECT_RATE else ""
    return subject, " ".join(parts), [p["id"] for p in picks], topic


def perturb(rng, text):
    def swap(m):
        w, opts = m.group(0), SYNONYMS.get(m.group(0).lower())
        if not opts:
            return w
        rep = rng.choice(opts)
        return rep[0].upper() + rep[1:] if w[0].isupper() else rep
    return WORD.sub(swap, text)


def generate(args):
    en = load_english(args.source)
    seeds, excluded = select_seeds(en)
    by_type = {}
    for s in seeds:
        by_type.setdefault(s["type"], []).append(s)
    usable = {t: g for t, g in sorted(by_type.items()) if len(g) >= 4}
    types, weights = list(usable), [len(g) for g in usable.values()]

    long_bodies = [b.lower() for b in en["body_c"] if len(b.split()) >= MIN_SUBSTRING_WORDS]

    rng, out, seen = random.Random(SEED), [], set()
    attempts, rejected = 0, Counter()
    while len(out) < N_RECORDS:
        attempts += 1
        t = rng.choices(types, weights=weights)[0]
        subject, body, seed_ids, topic = compose(rng, usable[t])
        subject, body = perturb(rng, subject), perturb(rng, body)
        text = (subject + "\n" + body).strip()
        if text.lower() in seen:
            rejected["duplicate"] += 1
            continue
        if any(b in body.lower() for b in long_bodies):
            rejected["copies_source_body"] += 1
            continue                                          # duplicate or copies a source ticket
        seen.add(text.lower())
        out.append({
            "record_id": "syn_" + hashlib.sha256(f"{GENERATOR_VERSION}|{text}".encode("utf-8")).hexdigest()[:12],
            "subject": subject or None, "body": body, "ticket_text": text,
            "queue": TARGET, "type": t, "priority": topic["priority"], "language": "en",
            "provenance": "synthetic", "seed_record_ids": seed_ids,
        })

    with open(args.out, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in out)
    print(f"Seed funnel: {int((en['queue'] == TARGET).sum())} target tickets -> {len(seeds)} clean seeds; "
          f"excluded: {dict(excluded)}; rejected candidates: {dict(rejected)} of {attempts} attempts")
    print(f"Wrote {len(out)} records to {args.out} from {len(seeds)} clean seeds")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", default=str(DEFAULT_SOURCE))
    p.add_argument("--out", default=str(HERE / "synthetic_50.jsonl"))
    generate(p.parse_args())
