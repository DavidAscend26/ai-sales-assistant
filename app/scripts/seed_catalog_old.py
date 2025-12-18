import argparse
import asyncio
import csv
from decimal import Decimal
from sqlalchemy import delete
from app.db.session import SessionLocal
from app.db.models import Car

async def main(csv_path: str, truncate: bool):
    async with SessionLocal() as session:
        if truncate:
            await session.execute(delete(Car))
            await session.commit()

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                car = Car(
                    make=(row.get("make") or "").strip(),
                    model=(row.get("model") or "").strip(),
                    year=int(row.get("year") or 0),
                    price_mxn=Decimal(str(row.get("price_mxn") or "0")),
                    city=(row.get("city") or "").strip(),
                    mileage_km=int(row.get("mileage_km") or 0) if row.get("mileage_km") else None,
                    transmission=(row.get("transmission") or None),
                    fuel=(row.get("fuel") or None),
                    body_type=(row.get("body_type") or None),
                    features=None,
                )
                session.add(car)
            await session.commit()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--truncate", action="store_true")
    args = p.parse_args()
    asyncio.run(main(args.csv, args.truncate))