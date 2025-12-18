from dataclasses import dataclass
from rapidfuzz import process, fuzz

@dataclass(frozen=True)
class NormalizedMakeModel:
    make: str | None
    model: str | None
    confidence: float
    candidates: list[str]

ALIASES = {
    "vw": "volkswagen",
    "volks": "volkswagen",
    "chevy": "chevrolet",
    "bmv": "bmw",
}

def normalize_token(token: str) -> str:
    t = token.strip().lower()
    return ALIASES.get(t, t)

def best_match(query: str, choices: list[str], limit: int = 5) -> list[tuple[str, float]]:
    if not choices:
        return []
    matches = process.extract(query, choices, scorer=fuzz.WRatio, limit=limit)
    return [(m[0], float(m[1])) for m in matches]

def normalize_make_model(raw_make: str | None, raw_model: str | None, known_pairs: list[str]) -> NormalizedMakeModel:
    if not raw_make and not raw_model:
        return NormalizedMakeModel(None, None, 0.0, [])

    make = normalize_token(raw_make) if raw_make else ""
    model = normalize_token(raw_model) if raw_model else ""
    query = (make + " " + model).strip()

    candidates = best_match(query, known_pairs, limit=5)
    if not candidates:
        return NormalizedMakeModel(raw_make, raw_model, 0.0, [])

    top, score = candidates[0]
    parts = top.split(" ", 1)
    norm_make = parts[0] if parts else None
    norm_model = parts[1] if len(parts) > 1 else None
    return NormalizedMakeModel(norm_make, norm_model, score, [c[0] for c in candidates])