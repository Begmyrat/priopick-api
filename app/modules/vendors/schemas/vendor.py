import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.modules.vendors.models.vendor import VendorCategory


class VendorCreate(BaseModel):
    name: str
    category: VendorCategory
    description: Optional[str] = None
    min_price: float
    max_price: float
    min_capacity: Optional[int] = None
    max_capacity: Optional[int] = None
    style_tags: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    @field_validator("max_price")
    @classmethod
    def max_price_valid(cls, v: float, info) -> float:
        if "min_price" in info.data and v < info.data["min_price"]:
            raise ValueError("max_price must be >= min_price")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_capacity: Optional[int] = None
    max_capacity: Optional[int] = None
    style_tags: Optional[str] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None


class VendorResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    description: Optional[str] = None
    min_price: float
    max_price: float
    min_capacity: Optional[int] = None
    max_capacity: Optional[int] = None
    style_tags: Optional[str] = None
    rating: float
    review_count: int
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class VendorListResponse(BaseModel):
    items: List[VendorResponse]
    total: int
    page: int
    page_size: int
    pages: int