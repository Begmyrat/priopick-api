import json
import math
import uuid
from typing import List, Optional

from app.modules.plans.services.plan_optimizer import PlanOptimizer
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.plans.repositories.plan import PlanRepository
from app.modules.plans.schemas.plan import (
    PlanCompareResponse,
    PlanCreate,
    PlanListResponse,
    PlanResponse,
    PlanUpdate,
    SuggestionType,
)
from app.modules.plans.services.ai_suggester import AISuggester
from app.modules.vendors.models.vendor import Vendor
from sqlalchemy import select


class PlanService:
    def __init__(self, db: AsyncSession):
        self.repo = PlanRepository(db)
        self.db = db
        self.ai = AISuggester()
        self.optimizer = PlanOptimizer()

    async def create_plan(
        self,
        user_id: uuid.UUID,
        data: PlanCreate,
    ) -> PlanResponse:
        vendors = await self._fetch_matching_vendors(
            budget=data.budget,
            guest_count=data.guest_count,
            style=data.style,
            categories=data.categories,
        )

        if not vendors:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No vendors found matching your criteria and chosen categories"
            )

        vendor_list = [
            {
                "vendor_id": str(v.id),
                "vendor_name": v.name,
                "vendor_category": v.category,
                "min_price": v.min_price,
                "max_price": v.max_price,
                "rating": v.rating,
                "style_tags": v.style_tags,
                "min_capacity": v.min_capacity,
                "max_capacity": v.max_capacity,
            }
            for v in vendors
        ]

        if data.suggestion_type == SuggestionType.ALGORITHM:
            suggestion_result = self.optimizer.suggest_plan(
                budget=data.budget,
                guest_count=data.guest_count,
                event_type=data.event_type,
                style=data.style,
                vendors=vendor_list,
            )
        else:
            try:
                suggestion_result = await self.ai.suggest_plan(
                    budget=data.budget,
                    guest_count=data.guest_count,
                    event_type=data.event_type,
                    style=data.style,
                    vendors=vendor_list,
                )
            except Exception as e:
                suggestion_result = self.optimizer.suggest_plan(
                    budget=data.budget,
                    guest_count=data.guest_count,
                    event_type=data.event_type,
                    style=data.style,
                    vendors=vendor_list,
                )
                suggestion_result["reasoning"] += f" (Fallback: {str(e)})"

        total_price = suggestion_result.get("total_price", 0.0)
        remaining = data.budget - total_price

        plan = await self.repo.create(
            user_id=user_id,
            name=data.name,
            budget=data.budget,
            guest_count=data.guest_count,
            event_type=data.event_type,
            style=data.style,
            total_price=total_price,
            remaining_budget=remaining,
            ai_suggestion=json.dumps(suggestion_result),
            ai_reasoning=suggestion_result.get("reasoning", ""),
            items=suggestion_result.get("selected_vendors", []),
        )

        return plan
    
    async def update(
        self,
        plan_id: uuid.UUID,
        user_id: uuid.UUID,
        data: PlanUpdate,
    ) -> PlanResponse:
        plan = await self.repo.get_by_id(plan_id, user_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        return await self.repo.update(
            plan=plan,
            **data.model_dump(exclude_unset=True)
        )

    async def get_all(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> PlanListResponse:
        plans, total = await self.repo.get_all(
            user_id=user_id,
            page=page,
            page_size=page_size,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return PlanListResponse(
            items=plans,
            total=total,
            page=page,
            page_size=page_size,
            pages=total_pages,
        )

    async def get_by_id(
        self,
        plan_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> PlanResponse:
        plan = await self.repo.get_by_id(plan_id, user_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        return plan

    async def delete(
        self,
        plan_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> dict:
        plan = await self.repo.get_by_id(plan_id, user_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        await self.repo.delete(plan)
        return {"message": "Plan deleted successfully"}

    async def compare(
        self,
        plan_a_id: uuid.UUID,
        plan_b_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> PlanCompareResponse:
        plan_a = await self.repo.get_by_id(plan_a_id, user_id)
        plan_b = await self.repo.get_by_id(plan_b_id, user_id)

        if not plan_a or not plan_b:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or both plans not found"
            )

        price_diff = abs(plan_a.total_price - plan_b.total_price)
        cheaper = plan_a.name if plan_a.total_price < plan_b.total_price \
            else plan_b.name

        recommendation = (
            f"{cheaper} is cheaper by ${price_diff:.2f}. "
            f"Consider your priorities between the two plans."
        )

        return PlanCompareResponse(
            plan_a=plan_a,
            plan_b=plan_b,
            cheaper_plan=cheaper,
            price_difference=price_diff,
            recommendation=recommendation,
        )

    async def _fetch_matching_vendors(
        self,
        budget: float,
        guest_count: int,
        style: Optional[str],
        categories: Optional[List[str]] = None,
    ) -> list:
        query = (
            select(Vendor)
            .where(Vendor.is_active == True)
            .where(Vendor.min_price <= budget)
        )

        if categories:
            query = query.where(Vendor.category.in_(categories))

        if guest_count:
            query = query.where(
                Vendor.max_capacity >= guest_count
            )

        if style:
            query = query.where(
                Vendor.style_tags.ilike(f"%{style}%")
            )
        query = query.order_by(Vendor.category, Vendor.rating.desc())

        result = await self.db.execute(query)
        return result.scalars().all()