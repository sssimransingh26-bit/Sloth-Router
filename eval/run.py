"""Run systems A (untuned), B (tuned), C (always-big), D (heuristic) on a frozen split."""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from app.heuristic import route as heuristic_route
from app.pricing import usd
from app.prompts import SYSTEM_PROMPT, user_prompt
from app.threshold import apply_threshold, parse_router_output
from eval.metrics import answer_correct, summarize

load_dotenv()
ROOT = Path(__file__).resolve().parent.parent
ROUTER = os.getenv("ROUTER_MODEL", "Qwen/Qwen3.5-4B")
BIG = os.getenv("BIG_MODEL", "Qwen/Qwen3.6-35B-A3B")


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def heuristic_eval(rows: list[dict]) -> dict:
    preds = []
    costs = []
    lats = []
    for row in rows:
        t0 = time.perf_counter()
        out = heuristic_route(row["question"])
        lats.append((time.perf_counter() - t0) * 1000)
        costs.append(0.0)
        preds.append(
            {
                "id": row["id"],
                "gold": row["label"],
                "pred": out["route"],
                "answer_ok": answer_correct(out["answer"], row["gold_answer"], row["label"], out["route"]),
                "question": row["question"],
                "pred_answer": out["answer"],
            }
        )
    summary = summarize(preds, costs, lats)
    failures = [p for p in preds if p["pred"] != p["gold"] or not p["answer_ok"]]
    return {"system": "D_heuristic", "summary": summary, "failures": failures[:50]}


async def tinker_eval(system: str, rows: list[dict], threshold: float) -> dict:
    import tinker

    service = tinker.ServiceClient(display_name=f"sloth-eval-{system}")
    if system == "B":
        path = os.getenv("TINKER_ROUTER_PATH")
        if not path:
            raise SystemExit("TINKER_ROUTER_PATH required for system B")
        router = await service.create_sampling_client_async(model_path=path)
    else:
        router = await service.create_sampling_client_async(base_model=ROUTER)
    big = await service.create_sampling_client_async(base_model=BIG)
    rtok = router.get_tokenizer()
    btok = big.get_tokenizer()

    async def sample(client, tok, messages, max_tokens):
        prompt_text = tok.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        prompt_tokens = tok.encode(prompt_text, add_special_tokens=False)
        result = await client.sample_async(
            prompt=tinker.ModelInput.from_ints(prompt_tokens),
            num_samples=1,
            sampling_params=tinker.SamplingParams(max_tokens=max_tokens, temperature=0.0),
        )
        seq = result.sequences[0]
        text = tok.decode(seq.tokens, skip_special_tokens=True).strip()
        logprob_conf = None
        if getattr(seq, "logprobs", None):
            logprob_conf = math.exp(sum(seq.logprobs) / max(1, len(seq.logprobs)))
        return text, len(prompt_tokens), len(seq.tokens), logprob_conf

    preds = []
    costs = []
    lats = []
    for row in rows:
        t0 = time.perf_counter()
        if system == "C":
            text, pre, samp, logprob_conf = await sample(
                big,
                btok,
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt(row["question"])},
                ],
                220,
            )
            parsed = parse_router_output(text)
            final, _reason = apply_threshold(
                parsed, threshold=0.0, logprob_conf=logprob_conf
            )
            cost = usd(BIG, pre, samp)
            pred_route = final
            pred_answer = parsed.answer
        else:
            text, pre, samp, logprob_conf = await sample(
                router,
                rtok,
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt(row["question"])},
                ],
                180,
            )
            parsed = parse_router_output(text)
            final, _reason = apply_threshold(parsed, threshold, logprob_conf)
            pred_answer = parsed.answer
            extra = 0.0
            if final == "DEFER":
                btext, bpre, bsamp, _ = await sample(
                    big,
                    btok,
                    [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt(row["question"])},
                    ],
                    220,
                )
                pred_answer = parse_router_output(btext).answer or btext
                extra = usd(BIG, bpre, bsamp)
            cost = usd(ROUTER, pre, samp) + extra
            pred_route = final
        lats.append((time.perf_counter() - t0) * 1000)
        costs.append(cost)
        preds.append(
            {
                "id": row["id"],
                "gold": row["label"],
                "pred": pred_route,
                "answer_ok": answer_correct(pred_answer, row["gold_answer"], row["label"], pred_route),
                "question": row["question"],
                "pred_answer": pred_answer,
            }
        )
    summary = summarize(preds, costs, lats)
    failures = [p for p in preds if dangerous_error_row(p) or p["pred"] != p["gold"]]
    return {"system": system, "summary": summary, "failures": failures[:80], "n": len(preds)}


def dangerous_error_row(p: dict) -> bool:
    return p["pred"] == "ANSWER" and p["gold"] in {"DEFER", "ABSTAIN"}


def write_outputs(name: str, payload: dict) -> None:
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / f"{name}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    failures_md = ["# What failed\n", f"System `{name}`\n"]
    for item in payload.get("failures", [])[:25]:
        failures_md.append(
            f"- `{item['id']}` gold={item['gold']} pred={item['pred']}: {item['question'][:140]}"
        )
    (out / f"failures_{name}.md").write_text("\n".join(failures_md) + "\n", encoding="utf-8")


async def async_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", default="test", choices=["val", "test"])
    parser.add_argument("--systems", default="D", help="comma list: A,B,C,D")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--threshold", type=float, default=float(os.getenv("ANSWER_THRESHOLD", "0.72")))
    args = parser.parse_args()
    rows = load_jsonl(ROOT / "data" / f"{args.split}.jsonl")
    if args.limit:
        rows = rows[: args.limit]
    wanted = [s.strip() for s in args.systems.split(",")]
    table_rows = []
    for sys in wanted:
        if sys == "D":
            payload = heuristic_eval(rows)
            write_outputs("D_heuristic", payload)
        else:
            payload = await tinker_eval(sys, rows, args.threshold)
            write_outputs({"A": "A_untuned", "B": "B_tuned", "C": "C_always_big"}[sys], payload)
        s = payload["summary"]
        table_rows.append(
            {
                "system": payload["system"],
                "route_acc": s["route_acc"],
                "dangerous_error": s["dangerous_error"],
                "dangerous_error_ci95": s["dangerous_error_ci95"],
                "answer_correct": s["answer_correct"],
                "cost_per_1k_usd": s["cost_per_1k_usd"],
                "latency_ms_mean": s["latency_ms_mean"],
            }
        )
        print(json.dumps(table_rows[-1], indent=2))
    (ROOT / "results" / "table.json").write_text(
        json.dumps({"split": args.split, "threshold": args.threshold, "systems": table_rows}, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(async_main())
