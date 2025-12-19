import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.models import Base, Car
from app.tools.catalog import search_catalog, CatalogQuery

@pytest.mark.asyncio
async def test_search_catalog_sqlite():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with Session() as s:
        s.add_all([
            Car(make="nissan", model="sentra", year=2020, price_mxn=200000, city="cdmx", mileage_km=50000, transmission="auto", fuel="gas", body_type="sedan", features=None),
            Car(make="mazda", model="mazda3", year=2021, price_mxn=280000, city="cdmx", mileage_km=30000, transmission="auto", fuel="gas", body_type="sedan", features=None),
        ])
        await s.commit()

        out = await search_catalog(s, CatalogQuery(make="nissan", limit=5))
        assert len(out) == 1
        assert out[0]["model"] == "sentra"