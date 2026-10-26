# Sloth Router

The laziest model that never lies about being lazy.

A customer of **Fern & Thread**, a fictional Pune shop, types one message. A 4B open model does the least work it can safely do:

1. **ANSWER** for about $0.0001 when a single policy sentence is enough.
2. **DEFER** to Qwen3.6-35B-A3B when two policies interact, or when it is unsure.
3. **ABSTAIN** when information is missing, the question is off-topic, or a human must handle a refund dispute or personal data. Nobody answers those blindly.

The headline metric is the **dangerous error**: the small model confidently answering something it should have deferred or refused. Cost includes the router’s own tokens. The test set uses knowledge-base entries and phrasing styles that never appear in training.

This is not a general router. Savings, if any, hold for this synthetic help desk only. Live answers call [Tinker](https://tinker.thinkingmachines.ai/); the app is not fully offline.

## Results

Benchmark not run yet. After eval, this table is overwritten from `results/table.json`. Do not type numbers by hand.

| System | Route acc. | Dangerous error | Answer correct | Cost / 1k | Latency |
| --- | --- | --- | --- | --- | --- |
| A untuned 4B | — | — | — | — | — |
| B tuned 4B | — | — | — | — | — |
| C always-big 35B | — | — | — | — | — |
| D keyword heuristic | — | — | — | — | — |

Dangerous-error rate will be reported with a 95% Wilson interval. Failures go in `results/failures_*.md`.

## Architecture

```
request → FastAPI (Render) → 4B router on Tinker → Python threshold
        → ANSWER | DEFER (35B) | ABSTAIN
        → if credits or key missing: replay cache
```

Python, not the model, owns the safety default: malformed output, a tie, or ANSWER below `ANSWER_THRESHOLD` (default 0.72) becomes **DEFER**, never ANSWER. No weights are loaded on Render (free instances have 512 MB; a 4B model does not fit).

Sampling a saved LoRA checkpoint through Tinker is documented (`tinker://…/sampler_weights/…`). Sequence logprobs are returned. Serverless inference is Inkling-only; this project uses the ordinary sampling client.

Details: [docs/architecture.md](docs/architecture.md).

## Credit math (list prices, Tinker models page)

| Model | Prefill | Sample | Train | Role |
| --- | ---: | ---: | ---: | --- |
| Qwen3.5-4B | $0.33 | $1.005 | $0.737 | router |
| Qwen3.6-35B-A3B | $0.45 | $1.335 | $1.177 | defer / always-big |
| Qwen3.5-397B-A17B | $1.65 | $7.50 | $6.60 | optional upper bound |

Prices are USD per million tokens. About 3,000 × 300 tokens × 3 epochs ≈ 2.7M train tokens × $0.737 ≈ **$2**. Evaluating 600 items on the 35B model is on the order of **$0.30**. That leaves room for two or three reruns inside a **$10** Tinker credit.

## Reproduce

Python 3.12 recommended. From the repo root:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m gen.generate          # freezes 3000 / 300 / 600 + hashes
python -m pytest                # label + threshold tests
uvicorn app.main:app --reload   # playground in replay mode, no key needed
```

Training and live routing (spends Tinker credit):

```bash
pip install -r requirements-train.txt
# .env: TINKER_API_KEY=...
python -m train.probe           # one cheap ping; confirm logprobs
python -m train.sft             # writes train/logs/checkpoint.json
# set TINKER_ROUTER_PATH to the printed tinker:// sampler path
python -m eval.run --systems A,D --split test
python -m eval.run --systems B,C --split test
```

Choose the threshold on **val** only (`--split val`, sweep `ANSWER_THRESHOLD`). Freeze test before training. Report the seed in `train/config.json` (20261025).

Render: one web service, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Put `TINKER_API_KEY` in the dashboard, never in git. Without the key, visitors get replay mode and a badge.

## Dataset

Answer-first: every ANSWER gold is a knowledge-base sentence written before the question is styled. DEFER items combine two policies. ABSTAIN items drop a needed detail, go off-topic, or demand a human (damage/chargeback/personal data).

| Split | N | Styles | KB |
| --- | ---: | --- | --- |
| train | 3000 | polite, terse, typo, hinglish | train entries only |
| val | 300 | polite, terse | train entries only |
| test | 600 | email, gen-z, ALL CAPS, staccato | held-out entries + train entries in held-out style |

Target mix: 40% ANSWER, 35% DEFER, 25% ABSTAIN. `data/hashes.json` stores SHA-256 of the frozen files.

## Honest claims

- The router is small and open-weight (Qwen3.5-4B). You can inspect, swap, and rerun it. Read the [Qwen model card](https://huggingface.co/Qwen) for license before publishing adapters.
- You cannot claim “fully offline” if Tinker or the 35B model is called.
- You cannot claim a universal cost saving. Any saving is for this synthetic inbox.
- A strong untuned baseline is a feature. If B barely beats A, the README will say so.

## 90-second demo

Landing → cheap ANSWER → two-policy DEFER → ABSTAIN → metrics table and dangerous-error number → this repo.

Identity: moss green, cream, slow easing, a small sloth glyph. Calm, not cartoonish.

## License

Code in this repo: MIT. Base model: Qwen license on the model card. Training runs on Tinker (Thinking Machines).
