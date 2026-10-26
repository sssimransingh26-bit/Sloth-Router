# Sloth Router

The laziest model that never lies about being lazy.

A customer of Fern & Thread, a fictional Pune shop, types one message. A small open model (Qwen3.5-4B) does the least work it can safely do:

- **ANSWER** when a single policy sentence is enough.
- **DEFER** to a larger model (Qwen3.6-35B-A3B) when two policies interact, or when it is unsure.
- **ABSTAIN** when information is missing, the question is off-topic, or a human must handle it (refund disputes, damage claims, personal data). Nobody answers those blindly.

The headline metric is the **dangerous error**: the small model confidently answering something it should have deferred or refused. The test set uses knowledge-base entries and phrasing styles that never appear in training.

This is not a general router. Any saving holds for this synthetic help desk only. Live answers call Tinker; the project is not fully offline.

## Status

Working today: the synthetic data generator, an untuned-router baseline, 12 unit tests, and a Tinker LoRA fine-tuning pipeline (400 examples, 1 epoch, loss 1.41 -> 0.003, checkpoint saved).

## Roadmap

Score the tuned router against the baseline on the test set, add the always-big and keyword baselines, sweep the threshold on logprob confidence, and ship a web playground.

## Results

Numbers below were copied from console output on the 600-item test set. They come from an earlier prompt version that asked the model for a CONF line, and were not written to `results/table.json`.

| System | Route acc. | Dangerous error | Answer correct | Cost / 1k | Latency |
|---|---|---|---|---|---|
| A untuned 4B | 64.2% | 4.2% (95% CI 2.8-6.1%) | 26.3% | $0.41 | 3.2 s |
| B tuned 4B | next | next | next | next | next |
| C always-big 35B | next | next | next | next | next |
| D keyword heuristic | next | next | next | next | next |

## Design

```
request -> FastAPI -> 4B router on Tinker -> Python threshold
        -> ANSWER | DEFER (35B) | ABSTAIN
```

Python, not the model, owns the safety default: malformed output, a tie, or ANSWER below the threshold becomes DEFER, never ANSWER.

The model no longer writes a confidence number. An early training target gave every label a fixed confidence, which carried no information, so it was removed. Confidence is meant to come from the model's own probabilities. Sampling a saved LoRA checkpoint through Tinker is documented (`tinker://.../sampler_weights/...`). Whether the sampling client returns usable sequence logprobs is not verified here.

## Models and prices (Tinker pricing page, USD per million tokens)

| Model | Prefill | Sample | Train | Role |
|---|---|---|---|---|
| Qwen3.5-4B | $0.33 | $1.005 | $0.737 | router |
|
