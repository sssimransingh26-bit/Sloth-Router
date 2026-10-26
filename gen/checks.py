"""Label must match the generation rule. Near-copies are rejected."""

from __future__ import annotations

import re

from gen.kb import ABSTAIN_REASONS, BY_ID

LABELS = {"ANSWER", "DEFER", "ABSTAIN"}

_WS = re.compile(r"\s+")
_PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def near_duplicate_key(question: str) -> str:
    text = question.lower()
    text = _PUNCT.sub(" ", text)
    text = _WS.sub(" ", text).strip()
    return text


def check_record(rec: dict, allowed_styles: set[str], allowed_kb: set[str]) -> None:
    if rec["label"] not in LABELS:
        raise ValueError(f"bad label {rec['label']}")
    if rec["style"] not in allowed_styles:
        raise ValueError(f"style leak {rec['style']} not in {allowed_styles}")
    for kb_id in rec["kb_ids"]:
        if kb_id not in allowed_kb:
            raise ValueError(f"kb leak {kb_id}")
        if rec["split"] != "test" and BY_ID[kb_id]["split"] != "train":
            raise ValueError(f"train/val used held-out kb {kb_id}")

    rule = rec["rule"]
    label = rec["label"]
    if label == "ANSWER":
        if rule != "single_kb_entry" or len(rec["kb_ids"]) != 1:
            raise ValueError(f"ANSWER rule mismatch {rec}")
        entry = BY_ID[rec["kb_ids"][0]]
        if rec["gold_answer"] != entry["answer"]:
            raise ValueError("ANSWER gold must be the KB sentence")
    elif label == "DEFER":
        if rule != "two_policies" or len(rec["kb_ids"]) != 2:
            raise ValueError(f"DEFER rule mismatch {rec}")
        if rec["kb_ids"][0] == rec["kb_ids"][1]:
            raise ValueError("DEFER needs two distinct policies")
    elif label == "ABSTAIN":
        if rec["kb_ids"]:
            raise ValueError("ABSTAIN must not cite KB ids")
        if rule not in ABSTAIN_REASONS and rule != "canonical_demo":
            raise ValueError(f"unknown abstain rule {rule}")
        if rule in ABSTAIN_REASONS and rec["gold_answer"] != ABSTAIN_REASONS[rule]:
            raise ValueError("ABSTAIN gold must match the reason template")


def check_records(rows: list[dict], allowed_styles: set[str], allowed_kb: set[str]) -> None:
    keys = [near_duplicate_key(r["question"]) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("near-duplicate questions in split")
    for rec in rows:
        check_record(rec, allowed_styles, allowed_kb)
    n = len(rows)
    if n == 0:
        raise ValueError("empty split")
    for label in LABELS:
        share = sum(1 for r in rows if r["label"] == label) / n
        if not (0.15 <= share <= 0.55):
            raise ValueError(f"{label} balance off: {share:.2f}")
