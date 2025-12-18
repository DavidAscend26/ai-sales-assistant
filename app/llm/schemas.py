from pydantic import BaseModel, Field
from typing import Optional

class ToolCatalogArgs(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    city: Optional[str] = None
    transmission: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=10)

class ToolFinancingArgs(BaseModel):
    price_mxn: float
    down_payment: float
    annual_rate: float = 0.10

class ToolRagArgs(BaseModel):
    query: str
    top_k: int = 4

class ToolNormalizeArgs(BaseModel):
    make: Optional[str] = None
    model: Optional[str] = None