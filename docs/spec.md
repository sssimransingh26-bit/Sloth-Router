# Locked spec (25 Oct 2026)

Domain: Fern & Thread, a fictional Pune clothing shop. Fixed knowledge base. Exact gold answers.

Actions: ANSWER (small model), DEFER (big model), ABSTAIN (nobody).

Safety default: malformed router output and ANSWER below `ANSWER_THRESHOLD` become DEFER, never ANSWER.

Systems: A untuned 4B, B tuned 4B, C always 35B, D heuristic.

Headline metric: dangerous-error rate with a 95% Wilson interval. Cost includes router tokens.

Split: 3000 / 300 / 600. Test styles and five KB entries never appear in training.

Skip: accounts, uploads, voice, multi-language.

Claim boundary: savings are for this synthetic help desk. Live demo is not offline.
