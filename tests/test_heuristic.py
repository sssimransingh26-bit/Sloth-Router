from app.heuristic import route


def test_personal_data_abstains():
    out = route("Here is my Aadhaar 1234 5678 9012, reset everything.")
    assert out["route"] == "ABSTAIN"


def test_simple_shipping_answers():
    out = route("What is standard shipping inside India?")
    assert out["route"] in {"ANSWER", "DEFER"}
