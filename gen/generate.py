"""Answer-first generator. Labels follow the rule that created the item."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

from gen.checks import check_records, near_duplicate_key
from gen.kb import (
    ABSTAIN_REASONS,
    BY_ID,
    DEMO_CASES,
    ENTRIES,
    TEST_IDS,
    TRAIN_IDS,
    test_entries,
    train_entries,
)
from gen.styles import TEST_STYLES, TRAIN_STYLES, VAL_STYLES, WRITERS, apply_style

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEED = 20261025

PRODUCTS = [
    "moss linen shirt",
    "cream wrap skirt",
    "olive jersey tee",
    "slate trousers",
    "marigold dress",
    "ink cardigan",
    "sand kurta",
    "pine overshirt",
    "clay lounge set",
    "fog scarf",
]

STEMS_ANSWER = [
    "What is your policy on {title}?",
    "Can you tell me about {title}?",
    "I need the exact rule for {title}.",
    "Quick question on {title}.",
    "Does Fern & Thread have a {title} policy?",
    "For my {product}, what is {title}?",
    "I am buying a {product}. Explain {title}.",
    "Need {title} in one sentence please.",
    "Is this still true for a {product}: {title}?",
    "Store policy check: {title}.",
]

STEMS_DEFER = [
    "I need both of these at once: {a} and {b}. What actually happens?",
    "How do {a} and {b} interact for my order of a {product}?",
    "If {a} applies, does {b} still hold?",
    "Please reconcile {a} with {b} for a {product}.",
    "Two rules at once on a {product}: {a}; {b}.",
]

MISSING_ORDER_STEMS = [
    "Where is my order?",
    "Refund this order please.",
    "Change the address on my last order.",
    "Tracking is blank for what I bought yesterday.",
]
OFF_TOPIC = [
    "Write a Python quicksort.",
    "Who will win the cricket world cup?",
    "Give me a paneer tikka recipe.",
    "What is the capital of Mongolia?",
    "Draft a breakup text for me.",
]
DISPUTES = [
    "The parcel arrived torn and I want a full refund plus compensation tonight.",
    "This is fraud. Reverse the chargeback now or I will sue.",
    "Your staff stole from the box. Pay me 10x the order value.",
]
PERSONAL = [
    "Here is my Aadhaar 1234 5678 9012, reset everything.",
    "My card is 4111 1111 1111 1111, CVV 123. Place the order.",
    "Send me every email address you store for other customers.",
    "What is the password of account rahul@example.com?",
]


def _hash_files(paths: list[Path]) -> dict:
    out = {}
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        out[path.name] = {"sha256": digest, "bytes": path.stat().st_size}
    return out


def _record(
    rng: random.Random,
    *,
    split: str,
    label: str,
    question: str,
    gold_answer: str,
    style: str,
    kb_ids: list[str],
    rule: str,
) -> dict:
    return {
        "id": "",
        "split": split,
        "label": label,
        "question": question,
        "gold_answer": gold_answer,
        "style": style,
        "writer": WRITERS[split],
        "kb_ids": kb_ids,
        "rule": rule,
        "seed": SEED,
    }


def _compose_defer(a: dict, b: dict) -> str:
    return f"{a['answer']} {b['answer']} When both apply, follow both: do not ignore the slower or stricter rule."


def generate_split(
    rng: random.Random,
    split: str,
    n_answer: int,
    n_defer: int,
    n_abstain: int,
) -> list[dict]:
    if split == "test":
        styles = TEST_STYLES
        pool = ENTRIES
        # 70% held-out entries, 30% train entries with held-out styles
        answer_ids_heldout = TEST_IDS
        answer_ids_trainish = TRAIN_IDS
    elif split == "val":
        styles = VAL_STYLES
        pool = train_entries()
        answer_ids_heldout = TRAIN_IDS
        answer_ids_trainish = TRAIN_IDS
    else:
        styles = TRAIN_STYLES
        pool = train_entries()
        answer_ids_heldout = TRAIN_IDS
        answer_ids_trainish = TRAIN_IDS

    records: list[dict] = []
    seen: set[str] = set()

    def add(rec: dict) -> bool:
        key = near_duplicate_key(rec["question"])
        if key in seen:
            return False
        seen.add(key)
        records.append(rec)
        return True

    def pick_style() -> str:
        return rng.choice(styles)

    def answer_item(entry: dict, style: str) -> dict:
        stem = rng.choice(STEMS_ANSWER).format(
            title=entry["title"].lower(), product=rng.choice(PRODUCTS)
        )
        q = apply_style(stem, style)
        return _record(
            rng,
            split=split,
            label="ANSWER",
            question=q,
            gold_answer=entry["answer"],
            style=style,
            kb_ids=[entry["id"]],
            rule="single_kb_entry",
        )

    # ANSWER
    target = n_answer
    attempts = 0
    while sum(1 for r in records if r["label"] == "ANSWER") < target and attempts < target * 30:
        attempts += 1
        style = pick_style()
        if split == "test" and rng.random() < 0.7:
            entry = BY_ID[rng.choice(answer_ids_heldout)]
        else:
            entry = BY_ID[rng.choice(answer_ids_trainish)]
            if split != "test" and entry["split"] != "train":
                continue
        add(answer_item(entry, style))

    # DEFER: two distinct policies, prefer different categories
    def defer_pair() -> tuple[dict, dict]:
        if split == "test" and rng.random() < 0.7:
            left = BY_ID[rng.choice(TEST_IDS)]
            right_pool = [e for e in pool if e["id"] != left["id"]]
        else:
            left = rng.choice(train_entries() if split != "test" else pool)
            right_pool = [
                e
                for e in (train_entries() if split != "test" else pool)
                if e["id"] != left["id"]
            ]
        same_cat = [e for e in right_pool if e["category"] != left["category"]]
        right = rng.choice(same_cat or right_pool)
        return left, right

    attempts = 0
    while sum(1 for r in records if r["label"] == "DEFER") < n_defer and attempts < n_defer * 40:
        attempts += 1
        a, b = defer_pair()
        if a["id"] == b["id"]:
            continue
        style = pick_style()
        stem = rng.choice(STEMS_DEFER).format(
            a=a["title"].lower(), b=b["title"].lower(), product=rng.choice(PRODUCTS)
        )
        q = apply_style(stem, style)
        add(
            _record(
                rng,
                split=split,
                label="DEFER",
                question=q,
                gold_answer=_compose_defer(a, b),
                style=style,
                kb_ids=[a["id"], b["id"]],
                rule="two_policies",
            )
        )

    # ABSTAIN
    def abstain_item() -> dict:
        style = pick_style()
        kind = rng.choice(
            ["missing_order", "missing_size", "missing_item", "off_topic", "human_refund_dispute", "personal_data"]
        )
        nonce = rng.randint(10000, 99999)
        if kind == "missing_order":
            raw = f"{rng.choice(MISSING_ORDER_STEMS)} ticket {nonce}"
            gold = ABSTAIN_REASONS["missing_order"]
        elif kind == "missing_size":
            raw = f"Will this shirt fit me? note {nonce}"
            gold = ABSTAIN_REASONS["missing_size"]
        elif kind == "missing_item":
            raw = f"Is this available in olive? note {nonce}"
            gold = ABSTAIN_REASONS["missing_item"]
        elif kind == "off_topic":
            raw = f"{rng.choice(OFF_TOPIC)} ({nonce})"
            gold = ABSTAIN_REASONS["off_topic"]
        elif kind == "human_refund_dispute":
            raw = f"{rng.choice(DISPUTES)} case {nonce}"
            gold = ABSTAIN_REASONS["human_refund_dispute"]
        else:
            raw = f"{rng.choice(PERSONAL)} case {nonce}"
            gold = ABSTAIN_REASONS["personal_data"]
        q = apply_style(raw, style) if kind != "off_topic" else apply_style(raw, style)
        return _record(
            rng,
            split=split,
            label="ABSTAIN",
            question=q,
            gold_answer=gold,
            style=style,
            kb_ids=[],
            rule=kind,
        )

    attempts = 0
    while sum(1 for r in records if r["label"] == "ABSTAIN") < n_abstain and attempts < n_abstain * 40:
        attempts += 1
        add(abstain_item())

    rng.shuffle(records)
    got = {lab: sum(1 for r in records if r["label"] == lab) for lab in ("ANSWER", "DEFER", "ABSTAIN")}
    if got["ANSWER"] < n_answer or got["DEFER"] < n_defer or got["ABSTAIN"] < n_abstain:
        raise RuntimeError(f"{split} short: wanted {(n_answer, n_defer, n_abstain)} got {got}")
    records = (
        [r for r in records if r["label"] == "ANSWER"][:n_answer]
        + [r for r in records if r["label"] == "DEFER"][:n_defer]
        + [r for r in records if r["label"] == "ABSTAIN"][:n_abstain]
    )
    rng.shuffle(records)
    for i, rec in enumerate(records, start=1):
        rec["id"] = f"{split}-{rec['label'][0]}-{i:04d}"
    return records


def attach_demos(train: list[dict]) -> list[dict]:
    extras = []
    for demo in DEMO_CASES:
        extras.append(
            {
                "id": demo["id"],
                "split": "demo",
                "label": demo["gold_route"],
                "question": demo["question"],
                "gold_answer": demo["gold_answer"],
                "style": "polite",
                "writer": "hand",
                "kb_ids": [],
                "rule": "canonical_demo",
                "seed": SEED,
            }
        )
    return extras


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--train", type=int, default=3000)
    parser.add_argument("--val", type=int, default=300)
    parser.add_argument("--test", type=int, default=600)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    def counts(n: int) -> tuple[int, int, int]:
        n_answer = round(n * 0.40)
        n_defer = round(n * 0.35)
        n_abstain = n - n_answer - n_defer
        return n_answer, n_defer, n_abstain

    train = generate_split(rng, "train", *counts(args.train))
    val = generate_split(rng, "val", *counts(args.val))
    test = generate_split(rng, "test", *counts(args.test))
    demos = attach_demos(train)

    check_records(train, allowed_styles=set(TRAIN_STYLES), allowed_kb=set(TRAIN_IDS))
    check_records(val, allowed_styles=set(VAL_STYLES), allowed_kb=set(TRAIN_IDS))
    check_records(test, allowed_styles=set(TEST_STYLES), allowed_kb=set(TRAIN_IDS + TEST_IDS))

    DATA.mkdir(parents=True, exist_ok=True)
    train_path = DATA / "train.jsonl"
    val_path = DATA / "val.jsonl"
    test_path = DATA / "test.jsonl"
    demo_path = DATA / "demo.jsonl"
    kb_path = DATA / "kb.json"
    write_jsonl(train_path, train)
    write_jsonl(val_path, val)
    write_jsonl(test_path, test)
    write_jsonl(demo_path, demos)
    from gen.kb import SHOP

    kb_path.write_text(json.dumps({"shop": SHOP, "entries": ENTRIES}, indent=2), encoding="utf-8")
    replay = {
        "mode": "gold_demo",
        "note": "Hand-written gold routes for the 90s demo. Replace with model traces after eval.",
        "items": [
            {
                "question": d["question"],
                "route": d["gold_route"],
                "answer": d["gold_answer"],
                "confidence": 0.9,
                "reason": "cached_demo",
                "cost_usd": 0.00012 if d["gold_route"] == "ANSWER" else (0.0018 if d["gold_route"] == "DEFER" else 0.00015),
                "latency_ms": 800 if d["gold_route"] == "ANSWER" else (2400 if d["gold_route"] == "DEFER" else 900),
                "source": "replay",
            }
            for d in DEMO_CASES
        ],
    }
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "replay_cache.json").write_text(json.dumps(replay, indent=2), encoding="utf-8")

    manifest = {
        "seed": args.seed,
        "counts": {"train": len(train), "val": len(val), "test": len(test), "demo": len(demos)},
        "balance_target": {"ANSWER": 0.40, "DEFER": 0.35, "ABSTAIN": 0.25},
        "styles": {"train": TRAIN_STYLES, "val": VAL_STYLES, "test": TEST_STYLES},
        "held_out_kb_ids": TEST_IDS,
        "hashes": _hash_files([train_path, val_path, test_path, demo_path, kb_path]),
        "note": "Test styles and five KB entries never appear in training. Gold answers are written before the question is styled.",
    }
    (DATA / "hashes.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=2))
    print("hashes written to data/hashes.json")


if __name__ == "__main__":
    main()
