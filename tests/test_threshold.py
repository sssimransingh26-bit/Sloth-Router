from app.threshold import apply_threshold, dangerous_error, parse_router_output


def test_parse_happy_path():
    parsed = parse_router_output("ROUTE: ANSWER\nANSWER: Ships in 5–7 days.")
    assert parsed.route == "ANSWER"
    assert parsed.answer == "Ships in 5–7 days."
    assert parsed.malformed is False


def test_malformed_defaults_to_defer():
    parsed = parse_router_output("I think this is shipping maybe")
    route, reason = apply_threshold(parsed, 0.72)
    assert route == "DEFER"
    assert reason == "malformed_or_missing_fields"


def test_low_confidence_answer_becomes_defer():
    parsed = parse_router_output("ROUTE: ANSWER\nANSWER: maybe.")
    route, reason = apply_threshold(parsed, 0.72, logprob_conf=0.40)
    assert route == "DEFER"
    assert reason == "below_threshold"


def test_confident_answer_stays():
    parsed = parse_router_output("ROUTE: ANSWER\nANSWER: ₹79.")
    route, reason = apply_threshold(parsed, 0.72, logprob_conf=0.90)
    assert route == "ANSWER"
    assert reason == "model"


def test_tie_logprob_can_force_defer():
    parsed = parse_router_output("ROUTE: ANSWER\nANSWER: ₹79.")
    route, reason = apply_threshold(parsed, 0.72, logprob_conf=0.2)
    assert route == "DEFER"
    assert reason == "below_threshold"


def test_dangerous_error_definition():
    assert dangerous_error("ANSWER", "DEFER")
    assert dangerous_error("ANSWER", "ABSTAIN")
    assert not dangerous_error("DEFER", "ANSWER")
    assert not dangerous_error("ABSTAIN", "ABSTAIN")


def test_missing_logprob_confidence_defers_answer():
    parsed = parse_router_output("ROUTE: ANSWER\nANSWER: x")
    assert parsed.malformed is False
    route, reason = apply_threshold(parsed, 0.72)
    assert route == "DEFER"
    assert reason == "missing_confidence"
