
"""Supervised fine-tune of Qwen3.5-4B as the lazy router. Needs TINKER_API_KEY."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from app.prompts import SYSTEM_PROMPT, format_target, user_prompt

CONFIG = json.loads(
    (ROOT / "train" / "config.json").read_text(encoding="utf-8")
)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def conversation(row: dict) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt(row["question"])},
        {
            "role": "assistant",
            "content": format_target(row["label"], row["gold_answer"]),
        },
    ]

async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Debug: use only N examples",
    )
    args = parser.parse_args()

    if not os.getenv("TINKER_API_KEY"):
        raise SystemExit("Set TINKER_API_KEY in your .env file.")

    import numpy as np
    import tinker
    from tinker_cookbook.renderers import TrainOnWhat, get_renderer
    from tinker_cookbook.supervised.data import conversation_to_datum

    cfg = CONFIG
    rng = random.Random(cfg["seed"])

    train_rows = load_jsonl(ROOT / "data" / "train.jsonl")
    if not train_rows:
        raise ValueError("The training dataset is empty.")

    rng.shuffle(train_rows)

    if args.limit > 0:
        train_rows = train_rows[: args.limit]

    service = tinker.ServiceClient(display_name="sloth-router-sft")

    training_client = await service.create_lora_training_client_async(
        base_model=cfg["base_model"],
        rank=cfg["lora_rank"],
    )
    print("Training client created.", flush=True)

    tokenizer = training_client.get_tokenizer()
    renderer = get_renderer("qwen3_5_disable_thinking", tokenizer)

    data = [
        conversation_to_datum(
            conversation(row),
            renderer,
            max_length=cfg["max_length"],
            train_on_what=TrainOnWhat.LAST_ASSISTANT_MESSAGE,
        )
        for row in train_rows
    ]
    print(f"Data built: {len(data)} examples.", flush=True)

    
    # Check loss weights before starting remote training.
    for index, datum in enumerate(data):
        weights = datum.loss_fn_inputs["weights"].to_numpy()
        if weights.size == 0 or not np.isfinite(weights).all():
            raise ValueError(
                f"Example {index} has empty or non-finite training weights."
            )
        if weights.sum() <= 0:
            raise ValueError(
                f"Example {index} has zero training weights. "
                "Training stopped before optimizer steps."
            )
   
    batch_size = cfg["batch_size"]
    steps_per_epoch = max(1, len(data) // batch_size)

    log_path = ROOT / "train" / "logs" / "loss.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    losses = []
    step = 0

    with log_path.open("w", encoding="utf-8") as log:
        for epoch in range(cfg["epochs"]):
            rng.shuffle(data)

            for i in range(steps_per_epoch):
                batch = data[i * batch_size : (i + 1) * batch_size]

                print(
                    f"Sending epoch {epoch} step {step} "
                    f"({len(batch)} examples)...",
                    flush=True,
                )
                fw = await training_client.forward_backward_async(
                    batch, "cross_entropy"
                )
                fw_res = await fw.result_async()
                print(f"Step {step} result received.", flush=True)

                # Do not update weights if the returned loss is invalid.
                logprobs = np.concatenate(
                    [
                        out["logprobs"].to_numpy()
                        for out in fw_res.loss_fn_outputs
                    ]
                )

                weights = np.concatenate(
                    [
                        d.loss_fn_inputs["weights"].to_numpy()
                        for d in batch
                    ]
                )

                weight_sum = weights.sum()

                if (
                    weight_sum <= 0
                    or not np.isfinite(weight_sum)
                    or not np.isfinite(logprobs).all()
                ):
                    raise ValueError(
                        "Invalid loss data detected. "
                        "Stopping before the optimizer update."
                    )

                loss = float(-np.dot(logprobs, weights) / weight_sum)

                if not np.isfinite(loss):
                    raise ValueError(
                        f"Non-finite loss at step {step}: {loss}"
                    )

                # Update parameters only after validating the loss.
                opt = await training_client.optim_step_async(
                    tinker.AdamParams(
                        learning_rate=cfg["learning_rate"]
                    )
                )
                await opt.result_async()

                losses.append(loss)
                record = {
                    "step": step,
                    "epoch": epoch,
                    "loss": loss,
                }

                log.write(json.dumps(record) + "\n")
                log.flush()

                if step % 10 == 0:
                    print(record)

                step += 1

            sampler_future = training_client.save_weights_for_sampler(
                f"sloth-router-epoch-{epoch + 1}"
            )
            sampler = await sampler_future.result_async()
            checkpoint_path = sampler.path
            (ROOT / "train" / "logs" / "checkpoint.json").write_text(
                json.dumps(
                    {
                        "path": checkpoint_path,
                        "epoch": epoch + 1,
                        "steps": step,
                        "final_loss": losses[-1] if losses else None,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(
                f"Checkpoint saved after epoch {epoch + 1}: {checkpoint_path}",
                flush=True,
            )

    print("Checkpoint:", checkpoint_path)
    print(
        "Set TINKER_ROUTER_PATH to this tinker:// path "
        "for live tuned routing."
    )


if __name__ == "__main__":
    asyncio.run(main())
