from decimal import Decimal
from app.tools.financing import calc_financing

def test_financing_basic():
    options = calc_financing(Decimal("200000"), Decimal("50000"), Decimal("0.10"))
    assert len(options) == 4
    assert options[0].years == 3
    assert options[-1].years == 6
    assert all(o.monthly_payment > 0 for o in options)

def test_financing_no_needed():
    options = calc_financing(Decimal("200000"), Decimal("200000"), Decimal("0.10"))
    assert options == []