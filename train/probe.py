"""Phase 1: one sampling call on the untuned 4B router. Spends a fraction of a cent."""

from __future__ import annotations

import asyncio
import os
import time

from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    import tinker

    key = os.getenv("TINKER_API_KEY")
    if not key:
        raise SystemExit("Set TINKER_API_KEY in .env")

    service = tinker.ServiceClient(display_name="sloth-router-probe")
    client = await service.create_sampling_client_async(base_model="Qwen/Qwen3.5-4B")
    tokenizer = client.get_tokenizer()
    prompt_text = tokenizer.apply_chat_template(
        [{"role": "user", "content": "Reply with the single word pong."}],
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    tokens = tokenizer.encode(prompt_text, add_special_tokens=False)
    t0 = time.perf_counter()
    result = await client.sample_async(
        prompt=tinker.ModelInput.from_ints(tokens),
        num_samples=1,
        sampling_params=tinker.SamplingParams(max_tokens=8, temperature=0.0),
    )
    seq = result.sequences[0]
    text = tokenizer.decode(seq.tokens, skip_special_tokens=True)
    has_logprobs = bool(getattr(seq, "logprobs", None))
    print(f"text={text!r}")
    print(f"stop_reason={seq.stop_reason}")
    print(f"logprobs_present={has_logprobs}")
    if has_logprobs:
        print(f"n_logprobs={len(seq.logprobs)}")
    print(f"latency_s={time.perf_counter() - t0:.2f}")
    print("probe_ok=true")


if __name__ == "__main__":
    asyncio.run(main())
