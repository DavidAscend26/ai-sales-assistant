import argparse
import asyncio
import csv
import json
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import delete
from app.db.session import SessionLocal
from app.db.models import Car


def _strip(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def _to_int(v: Any) -> int | None:
    s = _strip(v)
    if not s:
        return None
    try:
        # soporta "77,400" o "77400.0"
        s = s.replace(",", "")
        return int(float(s))
    except ValueError:
        return None


def _to_decimal(v: Any) -> Decimal | None:
    s = _strip(v)
    if not s:
        return None
    try:
        # soporta "461999.0" y "461,999.0"
        s = s.replace(",", "")
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _to_bool(v: Any) -> bool | None:
    s = _strip(v).lower()
    if not s:
        return None
    if s in {"si", "sí", "true", "1", "yes", "y"}:
        return True
    if s in {"no", "false", "0", "n"}:
        return False
    return None


def _sniff_delimiter(csv_path: str) -> str:
    # intenta detectar si es ',' o ';'
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        sample = f.read(4096)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t"])
        return dialect.delimiter
    except Exception:
        return ","


async def main(csv_path: str, truncate: bool):
    delimiter = _sniff_delimiter(csv_path)

    async with SessionLocal() as session:
        if truncate:
            await session.execute(delete(Car))
            await session.commit()

        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)

            rows = 0
            inserted = 0

            for row in reader:
                rows += 1

                make = _strip(row.get("make"))
                model = _strip(row.get("model"))
                year = _to_int(row.get("year"))

                # Soporta price o price_mxn
                price = _to_decimal(row.get("price")) or _to_decimal(row.get("price_mxn"))

                # Soporta km o mileage_km
                mileage = _to_int(row.get("km")) or _to_int(row.get("mileage_km"))

                # Algunos CSV no traen city; default demo
                city = _strip(row.get("city")) or "N/A"

                # Extras a features (para no perder info)
                features = {
                    "stock_id": _to_int(row.get("stock_id")),
                    "version": _strip(row.get("version")),
                    "bluetooth": _to_bool(row.get("bluetooth")),
                    "car_play": _to_bool(row.get("car_play")),
                    "largo": _to_int(row.get("largo")),
                    "ancho": _to_int(row.get("ancho")),
                    "altura": _to_int(row.get("altura")),
                }

                # limpia features vacías
                features = {k: v for k, v in features.items() if v not in (None, "", [])}

                # Filtros mínimos de calidad
                if not make or not model or not year or not price:
                    # saltamos filas incompletas para no ensuciar DB
                    continue

                car = Car(
                    external_id=features.get("stock_id"),  # si agregaste la columna
                    make=make.strip(),
                    model=model.strip(),
                    year=year,
                    price_mxn=price,
                    city=city,
                    mileage_km=mileage,
                    transmission=_strip(row.get("transmission")) or None,
                    fuel=_strip(row.get("fuel")) or None,
                    body_type=_strip(row.get("body_type")) or None,
                    features=features if features else None,
                )

                session.add(car)
                inserted += 1

            await session.commit()

    print(json.dumps({"rows_read": rows, "inserted": inserted, "delimiter": delimiter}, ensure_ascii=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--truncate", action="store_true")
    args = p.parse_args()
    asyncio.run(main(args.csv, args.truncate))