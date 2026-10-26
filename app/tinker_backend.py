"""Live Tinker sampling. Optional: the web app still serves replay without this import working."""

from __future__ import annotations

import asyncio
import math
import os
import time

from app.pricing import usd
from app.prompts import SYSTEM_PROMPT, user_prompt
from app.threshold import apply_threshold, parse_router_output

ROUTER_MODEL = os.getenv("ROUTER_MODEL", "Qwen/Qwen3.5-4B")
BIG_MODEL = os.getenv("BIG_MODEL", "Qwen/Qwen3.6-35B-A3B")


def _approx_tokens(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


async def _sample(client, tokenizer, messages: list[dict], max_tokens: int, temperature: float):
    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    prompt_tokens = tokenizer.encode(prompt_text, add_special_tokens=False)
    import tinker

    result = await client.sample_async(
        prompt=tinker.ModelInput.from_ints(prompt_tokens),
        num_samples=1,
        sampling_params=tinker.SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
        ),
    )
    seq = result.sequences[0]
    text = tokenizer.decode(seq.tokens, skip_special_tokens=True).strip()
    mean_lp = None
    if getattr(seq, "logprobs", None):
        mean_lp = math.exp(sum(seq.logprobs) / max(1, len(seq.logprobs)))
    return text, len(prompt_tokens), len(seq.tokens), mean_lp


async def live_route(question: str, threshold: float, timeout: float) -> dict:
    import tinker

    service = tinker.ServiceClient(display_name="sloth-router")
    router_path = os.getenv("TINKER_ROUTER_PATH") or None
    if router_path:
        router = await service.create_sampling_client_async(model_path=router_path)
        router_name = f"tuned:{ROUTER_MODEL}"
        source = "tuned"
    else:
        router = await service.create_sampling_client_async(base_model=ROUTER_MODEL)
        router_name = ROUTER_MODEL
        source = "untuned"
    tokenizer = router.get_tokenizer()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt(question)},
    ]
    t0 = time.perf_counter()
    text, prefill, sample_n, logprob_conf = await asyncio.wait_for(
        _sample(router, tokenizer, messages, max_tokens=180, temperature=0.0),
        timeout=timeout,
    )
    parsed = parse_router_output(text)
    final_route, reason = apply_threshold(parsed, threshold, logprob_conf)
    answer = parsed.answer
    big_prefill = big_sample = 0
    if final_route == "DEFER":
        big = await service.create_sampling_client_async(base_model=BIG_MODEL)
        big_tok = big.get_tokenizer()
        defer_messages = [
            {"role": "system", "content": SYSTEM_PROMPT + "\nYou are the larger fallback model. Answer from the knowledge base. If you cannot, ABSTAIN."},
            {"role": "user", "content": user_prompt(question)},
        ]
        answer, big_prefill, big_sample, _ = await asyncio.wait_for(
            _sample(big, big_tok, defer_messages, max_tokens=220, temperature=0.2),
            timeout=timeout,
        )
    latency_ms = int((time.perf_counter() - t0) * 1000)
    cost = usd(ROUTER_MODEL, prefill, sample_n) + (
        usd(BIG_MODEL, big_prefill, big_sample) if big_prefill else 0.0
    )
    return {
        "route": final_route,
        "model_route": parsed.route,
        "reason": reason,
        "confidence": logprob_conf,
        "logprob_conf": logprob_conf,
        "answer": answer,
        "raw": parsed.raw,
        "malformed": parsed.malformed,
        "latency_ms": latency_ms,
        "cost_usd": round(cost, 6),
        "tokens": {
            "router_prefill": prefill,
            "router_sample": sample_n,
            "big_prefill": big_prefill,
            "big_sample": big_sample,
        },
        "router_model": router_name,
        "source": source,
        "mode": "live",
    }
