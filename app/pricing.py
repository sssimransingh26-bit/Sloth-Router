"""Verified Tinker list prices ($ / million tokens), pricing page dated in-repo as Oct 2026."""

MODELS = {
    "Qwen/Qwen3.5-4B": {"prefill": 0.33, "sample": 1.005, "train": 0.737},
    "Qwen/Qwen3.6-35B-A3B": {"prefill": 0.45, "sample": 1.335, "train": 1.177},
    "Qwen/Qwen3.5-397B-A17B": {"prefill": 1.65, "sample": 7.50, "train": 6.60},
}


def usd(model: str, prefill_tokens: int, sample_tokens: int) -> float:
    prices = MODELS[model]
    return (prefill_tokens * prices["prefill"] + sample_tokens * prices["sample"]) / 1_000_000
