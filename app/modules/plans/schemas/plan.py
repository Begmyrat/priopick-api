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
    vendors: List[PlanItemResponse] = []
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # If obj is a SQLAlchemy Plan model
        if hasattr(obj, "items"):
            return cls(
                id=obj.id,
                user_id=obj.user_id,
                name=obj.name,
                budget=obj.budget,
                guest_count=obj.guest_count,
                event_type=obj.event_type,
                style=obj.style,
                total_price=obj.total_price,
                remaining_budget=obj.remaining_budget,
                ai_reasoning=obj.ai_reasoning,
                created_at=obj.created_at,
                # Map SQLAlchemy "items" → Pydantic "vendors"
                vendors=[
                    PlanItemResponse.model_validate(item)
                    for item in obj.items
                ],
            )
        return super().model_validate(obj, **kwargs)


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