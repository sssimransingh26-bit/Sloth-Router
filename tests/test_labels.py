from pathlib import Path

from gen.checks import check_records
from gen.generate import generate_split
from gen.kb import TEST_IDS, TRAIN_IDS
from gen.styles import TEST_STYLES, TRAIN_STYLES, VAL_STYLES
import random

ROOT = Path(__file__).resolve().parent.parent


def test_generator_balances_and_does_not_leak():
    rng = random.Random(1)
    train = generate_split(rng, "train", 40, 35, 25)
    val = generate_split(rng, "val", 12, 11, 8)
    test = generate_split(rng, "test", 24, 21, 15)
    check_records(train, set(TRAIN_STYLES), set(TRAIN_IDS))
    check_records(val, set(VAL_STYLES), set(TRAIN_IDS))
    check_records(test, set(TEST_STYLES), set(TRAIN_IDS + TEST_IDS))
    assert all(r["style"] in TRAIN_STYLES for r in train)
    assert all(r["style"] in TEST_STYLES for r in test)
    assert all(kid not in TEST_IDS for r in train for kid in r["kb_ids"])
    assert all(kid not in TEST_IDS for r in val for kid in r["kb_ids"])


def test_answer_gold_is_kb_sentence():
    rng = random.Random(2)
    train = generate_split(rng, "train", 20, 10, 10)
    answers = [r for r in train if r["label"] == "ANSWER"]
    assert answers
    from gen.kb import BY_ID

    for rec in answers:
        assert rec["gold_answer"] == BY_ID[rec["kb_ids"][0]]["answer"]


def test_frozen_files_if_present():
    path = ROOT / "data" / "hashes.json"
    if not path.exists():
        return
    import json

    man = json.loads(path.read_text(encoding="utf-8"))
    assert man["seed"] == 20261025
    assert man["counts"]["train"] == 3000
    assert man["counts"]["test"] == 600
