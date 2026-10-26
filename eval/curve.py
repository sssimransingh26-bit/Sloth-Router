"""Sweep ANSWER_THRESHOLD on a saved per-example file to plot quality vs cost.

Live sweep: python -m eval.run --systems A --split val
Then this module can re-threshold if you store raw confidences later.
Until then it writes an empty plot spec the UI can render as 'not run yet'.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    spec = {
        "x": "cost_per_1k_usd",
        "y": "answer_correct",
        "series": [],
        "reference": "always-big is the upper-right point when C is evaluated",
        "status": "not_run_yet",
    }
    path = ROOT / "results" / "curve.json"
    if not path.exists():
        path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
        print("wrote empty curve spec")
    else:
        print(path.read_text(encoding="utf-8")[:500])


if __name__ == "__main__":
    main()
