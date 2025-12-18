from dataclasses import dataclass
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Car

@dataclass(frozen=True)
class CatalogQuery:
    make: str | None = None
    model: str | None = None
    year_min: int | None = None
    year_max: int | None = None
    price_min: float | None = None
    price_max: float | None = None
    city: str | None = None
    transmission: str | None = None
    limit: int = 5

async def known_make_model_pairs(session: AsyncSession) -> list[str]:
    rows = (await session.execute(select(Car.make, Car.model).distinct())).all()
    return [f"{r[0]} {r[1]}".strip().lower() for r in rows]

async def search_catalog(session: AsyncSession, q: CatalogQuery) -> list[dict]:
    filters = []
    if q.make:
        filters.append(Car.make.ilike(q.make))
    if q.model:
        filters.append(Car.model.ilike(q.model))
    if q.city:
        filters.append(Car.city.ilike(q.city))
    if q.transmission:
        filters.append(Car.transmission.ilike(q.transmission))
    if q.year_min is not None:
        filters.append(Car.year >= q.year_min)
    if q.year_max is not None:
        filters.append(Car.year <= q.year_max)
    if q.price_min is not None:
        filters.append(Car.price_mxn >= q.price_min)
    if q.price_max is not None:
        filters.append(Car.price_mxn <= q.price_max)

    stmt = select(Car).where(and_(*filters)) if filters else select(Car)
    stmt = stmt.order_by(Car.price_mxn.asc()).limit(q.limit)

    res = await session.execute(stmt)
    cars = res.scalars().all()

    return [
        {
            "id": c.id,
            "make": c.make,
            "model": c.model,
            "year": c.year,
            "price_mxn": float(c.price_mxn),
            "city": c.city,
            "mileage_km": c.mileage_km,
            "transmission": c.transmission,
            "fuel": c.fuel,
            "body_type": c.body_type,
        }
        for c in cars
    ]