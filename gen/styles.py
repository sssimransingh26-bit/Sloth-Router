"""Phrasing styles. Train and test styles are disjoint to block leakage."""

from __future__ import annotations

TRAIN_STYLES = ("polite", "terse", "typo", "hinglish")
VAL_STYLES = ("polite", "terse")
TEST_STYLES = ("email_formal", "genz", "allcaps", "staccato")
WRITERS = {
    "train": "clerk_templates",
    "val": "clerk_templates",
    "test": "heldout_family",
}


def apply_style(text: str, style: str) -> str:
    if style == "polite":
        return f"Hi, could you please help? {text} Thank you."
    if style == "terse":
        return text.rstrip("?") + "?"
    if style == "typo":
        return (
            text.replace("shipping", "shiping")
            .replace("return", "retrun")
            .replace("please", "plz")
            .replace("account", "acount")
        )
    if style == "hinglish":
        return f"bhai {text.rstrip('?')} bata do na?"
    if style == "email_formal":
        return (
            "Dear Fern & Thread support team,\n\n"
            f"I am writing to enquire: {text}\n\n"
            "Yours sincerely,\nA customer"
        )
    if style == "genz":
        return f"ok wait so like {text.rstrip('?')} ?? not to be dramatic but need this fr"
    if style == "allcaps":
        return text.upper()
    if style == "staccato":
        words = text.replace("?", "").split()
        return " / ".join(words) + " ?"
    raise ValueError(f"unknown style {style}")
