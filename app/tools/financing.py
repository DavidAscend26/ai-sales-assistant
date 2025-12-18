from dataclasses import dataclass
from decimal import Decimal, getcontext

getcontext().prec = 28

@dataclass(frozen=True)
class FinancingOption:
    years: int
    months: int
    monthly_payment: Decimal
    total_paid: Decimal
    total_interest: Decimal

def calc_financing(
    price_mxn: Decimal,
    down_payment: Decimal,
    annual_rate: Decimal = Decimal("0.10"),
) -> list[FinancingOption]:
    if price_mxn <= 0:
        raise ValueError("price_mxn must be positive")
    if down_payment < 0:
        raise ValueError("down_payment cannot be negative")
    if down_payment >= price_mxn:
        return []

    principal = price_mxn - down_payment
    r = annual_rate / Decimal(12)

    options: list[FinancingOption] = []
    for years in (3, 4, 5, 6):
        n = years * 12
        one_plus = (Decimal(1) + r)
        pow_ = one_plus ** Decimal(n)
        denom = (pow_ - Decimal(1))
        if denom == 0:
            continue
        monthly = principal * (r * pow_) / denom
        total = monthly * Decimal(n)
        interest = total - principal

        options.append(
            FinancingOption(
                years=years,
                months=n,
                monthly_payment=monthly.quantize(Decimal("0.01")),
                total_paid=total.quantize(Decimal("0.01")),
                total_interest=interest.quantize(Decimal("0.01")),
            )
        )
    return options