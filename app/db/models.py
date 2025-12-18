from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Numeric, Text, JSON, BigInteger, Index

class Base(DeclarativeBase):
    pass

class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    make: Mapped[str] = mapped_column(String(64), index=True)
    model: Mapped[str] = mapped_column(String(64), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    price_mxn: Mapped[float] = mapped_column(Numeric(12, 2), index=True)
    city: Mapped[str] = mapped_column(String(64), index=True)
    mileage_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    transmission: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fuel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    body_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    features: Mapped[dict | None] = mapped_column(JSON, nullable=True)

# Índices compuestos útiles para búsquedas frecuentes
Index("ix_cars_make_model", Car.make, Car.model)
Index("ix_cars_make_model_year", Car.make, Car.model, Car.year)

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(256), index=True)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    # Nota: embedding omitido para challenge base (prod: pgvector)