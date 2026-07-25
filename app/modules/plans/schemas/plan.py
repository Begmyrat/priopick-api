import uuid
from datetime import datetime
from typing import List, Optional
from app.modules.vendors.models.vendor import VendorCategory
from pydantic import BaseModel, Field
from enum import Enum

class SuggestionType(str, Enum):
    AI = "ai"
    ALGORITHM = "algorithm"


class PlanCreate(BaseModel):
    name: str
    budget: float = Field(gt=0)
    guest_count: int = Field(gt=0)
    event_type: Optional[str] = None
    style: Optional[str] = None
    categories: Optional[List[VendorCategory]] = None
    suggestion_type: SuggestionType = SuggestionType.AI


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    style: Optional[str] = None


class PlanItemResponse(BaseModel):
    id: uuid.UUID
    vendor_id: uuid.UUID
    vendor_name: str
    vendor_category: str
    price: float
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class PlanResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    budget: float
    guest_count: int
    event_type: Optional[str] = None
    style: Optional[str] = None
    total_price: Optional[float] = None
    remaining_budget: Optional[float] = None
    ai_reasoning: Optional[str] = None
    vendors: List[PlanItemResponse] = Field(default=[], validation_alias="items")
    
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class PlanListResponse(BaseModel):
    items: List[PlanResponse]
    total: int
    page: int
    page_size: int
    pages: int


class PlanCompareResponse(BaseModel):
    plan_a: PlanResponse
    plan_b: PlanResponse
    cheaper_plan: str
    price_difference: float
    recommendation: str