# Architecture

```
request
  → FastAPI (Render)
  → length cap, per-IP rate limit, daily spend cap
  → if no TINKER_API_KEY or cap hit: replay cache
  → else Qwen3.5-4B (base or LoRA via tinker:// path)
  → Python threshold (ANSWER below threshold, malformed, or timeout → DEFER)
  → ANSWER: small-model text
    DEFER: Qwen3.6-35B-A3B
    ABSTAIN: refusal / missing-info template
  → UI (route lanes, answer, cost, latency)
```

No weights run on Render. The 4B model is sampled through Tinker. Render free tier is 512 MB, which is too small to host a 4B model locally.

Sampling a saved LoRA checkpoint is documented (`create_sampling_client_async(model_path="tinker://…")`). Sequence logprobs are returned. Serverless inference is Inkling-only; this app uses the ordinary sampling client, which bills Tinker credits.
