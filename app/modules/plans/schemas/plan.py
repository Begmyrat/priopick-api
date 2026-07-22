import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PlanCreate(BaseModel):
    name: str
    budget: float = Field(gt=0)
    guest_count: int = Field(gt=0)
    event_type: Optional[str] = None
    style: Optional[str] = None


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
    
    # ← Tell Pydantic to look for the ORM's "items" attribute and map it to "vendors"
    vendors: List[PlanItemResponse] = Field(default=[], validation_alias="items")
    
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class PlanListResponse(BaseModel):
    items: List[PlanResponse]   # ← this "items" = list of plans
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