"""Fixed knowledge base for Fern & Thread, a fictional small clothing shop in Pune."""

from __future__ import annotations

SHOP = {
    "name": "Fern & Thread",
    "tagline": "Slow clothes, honest shipping.",
    "city": "Pune",
    "currency": "INR",
    "support_hours": "Mon–Sat, 10:00–18:00 IST",
}

# Train/val may use only train-split entries. Test may use both, but held-out
# entries appear only in the test set.
ENTRIES = [
    {
        "id": "ship_standard",
        "category": "shipping",
        "split": "train",
        "title": "Standard shipping (India)",
        "answer": "Standard shipping inside India takes 5–7 business days after dispatch and costs ₹79.",
        "keywords": ["standard shipping", "delivery time", "how long", "kitne din"],
    },
    {
        "id": "ship_express",
        "category": "shipping",
        "split": "train",
        "title": "Express shipping (India)",
        "answer": "Express shipping inside India takes 2–3 business days after dispatch and costs ₹199.",
        "keywords": ["express", "fast delivery", "jaldi"],
    },
    {
        "id": "ship_free",
        "category": "shipping",
        "split": "train",
        "title": "Free shipping threshold",
        "answer": "Shipping is free on prepaid orders of ₹1,499 or more inside India. COD orders never get free shipping.",
        "keywords": ["free shipping", "threshold", "1499"],
    },
    {
        "id": "ship_tracking",
        "category": "shipping",
        "split": "train",
        "title": "Tracking",
        "answer": "A tracking link is emailed and SMSed within 24 hours of dispatch. Status updates come from the courier, not from Fern & Thread chat.",
        "keywords": ["tracking", "awb", "where is my order"],
    },
    {
        "id": "ship_delay",
        "category": "shipping",
        "split": "train",
        "title": "Monsoon and festival delays",
        "answer": "During monsoon (June–September) and Diwali week, add 2 extra business days to every shipping estimate.",
        "keywords": ["monsoon", "diwali", "delay"],
    },
    {
        "id": "ret_window",
        "category": "returns",
        "split": "train",
        "title": "Return window",
        "answer": "You may request a return within 30 days of delivery. The request must be opened from the order page.",
        "keywords": ["return window", "30 days", "wapas"],
    },
    {
        "id": "ret_condition",
        "category": "returns",
        "split": "train",
        "title": "Return condition",
        "answer": "Returned items must be unworn, unwashed, and have the original tags attached. Innerwear and face masks cannot be returned.",
        "keywords": ["tags", "unworn", "condition"],
    },
    {
        "id": "ret_refund",
        "category": "returns",
        "split": "train",
        "title": "Refund timeline",
        "answer": "Once we receive the return, prepaid refunds go back to the original payment method in 5–7 business days. COD returns are refunded as store credit in 7–10 business days.",
        "keywords": ["refund", "store credit", "how long refund"],
    },
    {
        "id": "ret_exchange",
        "category": "returns",
        "split": "train",
        "title": "Exchange vs return",
        "answer": "Size exchanges are free once per order if the replacement is in stock. A return-for-refund uses one of your two free return pickups per calendar year; extra pickups cost ₹99.",
        "keywords": ["exchange", "size change", "pickup"],
    },
    {
        "id": "size_tops",
        "category": "sizing",
        "split": "train",
        "title": "Tops size chart",
        "answer": "Tops: S 34–36 in chest, M 38–40, L 42–44, XL 46–48. Charts are body measurements, not garment measurements.",
        "keywords": ["size chart", "chest", "tops"],
    },
    {
        "id": "size_bottoms",
        "category": "sizing",
        "split": "train",
        "title": "Bottoms size chart",
        "answer": "Bottoms: S 28–30 in waist, M 32–34, L 36–38, XL 40–42. Inseams are 28 in (short), 30 in (regular), 32 in (long).",
        "keywords": ["waist", "inseam", "pants"],
    },
    {
        "id": "size_between",
        "category": "sizing",
        "split": "train",
        "title": "Between sizes",
        "answer": "If you are between sizes, size up for linen and size down for stretch jersey. Linen relaxes after the first wash; jersey does not.",
        "keywords": ["between sizes", "linen", "jersey"],
    },
    {
        "id": "pay_methods",
        "category": "payments",
        "split": "train",
        "title": "Payment methods",
        "answer": "We accept UPI, Visa, Mastercard, RuPay, and net banking. We do not accept American Express or international cards on the Indian checkout.",
        "keywords": ["upi", "cards", "payment methods"],
    },
    {
        "id": "pay_failed",
        "category": "payments",
        "split": "train",
        "title": "Failed payment",
        "answer": "A failed payment does not place an order. The bank hold, if any, drops in 3–5 business days. Try a different UPI app or card; we cannot release a bank hold ourselves.",
        "keywords": ["failed payment", "hold", "debited"],
    },
    {
        "id": "pay_gst",
        "category": "payments",
        "split": "train",
        "title": "GST invoice",
        "answer": "A GST invoice is emailed in PDF within 24 hours of payment. To add a GSTIN, enter it at checkout; it cannot be added after dispatch.",
        "keywords": ["gst", "invoice", "gstin"],
    },
    {
        "id": "acc_password",
        "category": "account",
        "split": "train",
        "title": "Reset password",
        "answer": "Use Forgot password on the login page. The reset link expires in 30 minutes and can be requested three times per day.",
        "keywords": ["password", "reset", "login"],
    },
    {
        "id": "acc_address",
        "category": "account",
        "split": "train",
        "title": "Change address",
        "answer": "You may change the delivery address until the order is marked Packed. After Packed, the courier has the label and we cannot redirect it.",
        "keywords": ["change address", "packed", "redirect"],
    },
    {
        "id": "acc_history",
        "category": "account",
        "split": "train",
        "title": "Order history",
        "answer": "Signed-in buyers see two years of orders under Account → Orders. Guest checkout orders are only in the confirmation email.",
        "keywords": ["order history", "guest", "past orders"],
    },
    # Held-out entries: never in training questions.
    {
        "id": "ship_intl",
        "category": "shipping",
        "split": "test",
        "title": "International shipping",
        "answer": "We ship to UAE, Singapore, and Germany only. International shipping takes 8–12 business days and starts at ₹1,290. Duties are paid by the buyer.",
        "keywords": ["international", "uae", "duties"],
    },
    {
        "id": "ret_sale",
        "category": "returns",
        "split": "test",
        "title": "Sale items",
        "answer": "Final-sale and warehouse-sale items can be exchanged for size only. They cannot be refunded to the original payment method.",
        "keywords": ["final sale", "warehouse sale"],
    },
    {
        "id": "size_kids",
        "category": "sizing",
        "split": "test",
        "title": "Kids sizes",
        "answer": "Kids tops: 3–4y 56 cm height, 5–6y 116 cm, 7–8y 128 cm. Kids items use height, not chest.",
        "keywords": ["kids", "children", "height"],
    },
    {
        "id": "pay_cod",
        "category": "payments",
        "split": "test",
        "title": "Cash on delivery",
        "answer": "COD is available on Indian orders under ₹5,000 and adds a ₹49 fee. COD is not available for international checkouts or for custom embroidery.",
        "keywords": ["cod", "cash on delivery", "49"],
    },
    {
        "id": "acc_delete",
        "category": "account",
        "split": "test",
        "title": "Delete account",
        "answer": "Email privacy@fernandthread.example from the same address as the account. Deletion completes in 14 days and cannot be undone. Open orders must finish or be cancelled first.",
        "keywords": ["delete account", "privacy", "gdpr"],
    },
]

BY_ID = {e["id"]: e for e in ENTRIES}
TRAIN_IDS = [e["id"] for e in ENTRIES if e["split"] == "train"]
TEST_IDS = [e["id"] for e in ENTRIES if e["split"] == "test"]
CATEGORIES = sorted({e["category"] for e in ENTRIES})

ABSTAIN_REASONS = {
    "missing_order": "I need the order number (starts with FT-) before I can look this up.",
    "missing_size": "I need your chest or waist measurement, or the size on the label, before I can advise.",
    "missing_item": "I need the product name or SKU before I can answer.",
    "off_topic": "This help desk only answers Fern & Thread shipping, returns, sizing, payments, and account questions.",
    "human_refund_dispute": "A refund dispute about damage, fraud, or a chargeback needs a human. I will not decide this from chat.",
    "personal_data": "I will not collect or repeat personal data such as passwords, card numbers, Aadhaar, or PAN in this chat. Use the account page or email privacy@fernandthread.example.",
}

DEMO_CASES = [
    {
        "id": "demo-answer",
        "question": "How long does standard shipping take inside India?",
        "gold_route": "ANSWER",
        "gold_answer": "Standard shipping inside India takes 5–7 business days after dispatch and costs ₹79.",
    },
    {
        "id": "demo-defer",
        "question": "If I order linen during Diwali week with express shipping, when should I actually expect it, and is shipping still free if I pay ₹1,600 prepaid?",
        "gold_route": "DEFER",
        "gold_answer": "Express shipping is 2–3 business days plus 2 extra days in Diwali week. Prepaid orders of ₹1,499 or more get free shipping inside India, so a ₹1,600 prepaid order qualifies.",
    },
    {
        "id": "demo-abstain",
        "question": "The courier left my parcel torn and I want a full refund plus compensation to my personal bank account tonight. Also here is my Aadhaar 1234 5678 9012.",
        "gold_route": "ABSTAIN",
        "gold_answer": "A refund dispute about damage, fraud, or a chargeback needs a human. I will not decide this from chat. I will not collect or repeat personal data such as passwords, card numbers, Aadhaar, or PAN in this chat. Use the account page or email privacy@fernandthread.example.",
    },
]


def train_entries() -> list[dict]:
    return [e for e in ENTRIES if e["split"] == "train"]


def test_entries() -> list[dict]:
    return [e for e in ENTRIES if e["split"] == "test"]
