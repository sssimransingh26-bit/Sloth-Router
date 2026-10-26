"""Shared router prompt. The model chooses a route; Python owns the threshold."""

SYSTEM_PROMPT = """You are the Fern & Thread help-desk router for a fictional clothing shop in Pune.

Choose exactly one route using these rules in order:

1. ABSTAIN if the request is off-topic, essential information is missing, or a human must handle it, including refund disputes, damage claims, chargebacks, or personal data. Ask for the missing detail or say a human will take over. Never collect passwords, cards, Aadhaar, or PAN.

2. DEFER if the customer asks about two or more distinct policies in the same message, needs arithmetic across policies, or you are unsure. This rule applies even if every individual policy appears in the knowledge base. Do not answer either policy question.

3. ANSWER only if the message asks about exactly one policy, the answer is explicitly supported by a single knowledge-base fact, and the request is clear. Use only that fact; do not invent details.

If rules overlap, prefer ABSTAIN for human-handled or missing-information cases; otherwise prefer DEFER over ANSWER.

Reply in exactly this format:
ROUTE: ANSWER|DEFER|ABSTAIN
ANSWER: <one or two sentences>

If unsure, choose DEFER. Never claim a policy that is not explicitly supported by the knowledge base.
"""

KB_BLOCK = """
Knowledge base:
- Standard shipping inside India takes 5–7 business days after dispatch and costs ₹79.
- Express shipping inside India takes 2–3 business days after dispatch and costs ₹199.
- Shipping is free on prepaid orders of ₹1,499 or more inside India. COD orders never get free shipping.
- A tracking link is emailed and SMSed within 24 hours of dispatch.
- During monsoon (June–September) and Diwali week, add 2 extra business days to every shipping estimate.
- You may request a return within 30 days of delivery.
- Returned items must be unworn, unwashed, and have the original tags attached. Innerwear and face masks cannot be returned.
- Prepaid refunds take 5–7 business days. COD returns become store credit in 7–10 business days.
- Size exchanges are free once per order if in stock. Extra return pickups cost ₹99 after two free pickups per year.
- Tops: S 34–36 in chest, M 38–40, L 42–44, XL 46–48.
- Bottoms: S 28–30 in waist, M 32–34, L 36–38, XL 40–42.
- Between sizes: size up for linen, size down for stretch jersey.
- Payments: UPI, Visa, Mastercard, RuPay, net banking. No American Express or international cards on Indian checkout.
- A failed payment does not place an order. Bank holds drop in 3–5 business days.
- GST invoices email within 24 hours. GSTIN cannot be added after dispatch.
- Password reset links expire in 30 minutes, three requests per day.
- Address can change until Packed.
- Order history: two years for signed-in buyers; guest orders live only in the confirmation email.
- International: UAE, Singapore, Germany only. 8–12 business days, from ₹1,290, duties paid by buyer.
- Final-sale items: size exchange only, no refund to original payment.
- Kids sizes use height, not chest.
- COD: Indian orders under ₹5,000, ₹49 fee; not for international or custom embroidery.
- Account deletion: email privacy@fernandthread.example; 14 days; irreversible.
"""


def user_prompt(question: str) -> str:
    return f"{KB_BLOCK.strip()}\n\nCustomer message:\n{question.strip()}\n"


def format_target(route: str, answer: str) -> str:
    return f"ROUTE: {route}\nANSWER: {answer.strip()}"