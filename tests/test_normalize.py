from app.tools.normalize import normalize_make_model

def test_normalize_exact():
    pairs = ["nissan sentra", "mazda mazda3", "toyota corolla"]
    out = normalize_make_model("Nissan", "Sentra", pairs)
    assert out.make == "nissan"
    assert out.model == "sentra"
    assert out.confidence >= 80

def test_normalize_typo():
    pairs = ["nissan sentra", "mazda mazda3", "toyota corolla"]
    out = normalize_make_model("Nisssan", "Sentra", pairs)
    assert out.make == "nissan"
    assert out.confidence >= 70