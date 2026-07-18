from typing import Optional
from pydantic import BaseModel, Field


class VendorFilter(BaseModel):
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    style: Optional[str] = None
    min_capacity: Optional[int] = None
    rating_min: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    search: Optional[str] = None

    class Config:
        extra = "ignore"