import json
import math
import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.plans.repositories.plan import PlanRepository
from app.modules.plans.schemas.plan import (
    PlanCompareResponse,
    PlanCreate,
    PlanListResponse,
    PlanResponse,
    PlanUpdate,
)
from app.modules.plans.services.ai_suggester import AISuggester
from app.modules.vendors.models.vendor import Vendor
from sqlalchemy import select


class PlanService:
    def __init__(self, db: AsyncSession):
        self.repo = PlanRepository(db)
        self.db = db
        self.ai = AISuggester()

    async def create_plan(
        self,
        user_id: uuid.UUID,
        data: PlanCreate,
    ) -> PlanResponse:
        """
        Main planning flow:
        1. Fetch matching vendors from DB
        2. Send to AI for suggestion
        3. Save plan to DB
        4. Return complete plan
        """

        # Step 1 — fetch vendors matching budget + capacity + style
        vendors = await self._fetch_matching_vendors(
            budget=data.budget,
            guest_count=data.guest_count,
            style=data.style,
        )

        if not vendors:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No vendors found matching your criteria"
            )

        # Step 2 — format vendors for AI
        vendor_list = [
            {
                "vendor_id": str(v.id),
                "vendor_name": v.name,
                "vendor_category": v.category,
                "min_price": v.min_price,
                "max_price": v.max_price,
                "rating": v.rating,
                "style_tags": v.style_tags,
                "max_capacity": v.max_capacity,
            }
            for v in vendors
        ]

        # Step 3 — ask AI for best combination
        ai_result = await self.ai.suggest_plan(
            budget=data.budget,
            guest_count=data.guest_count,
            event_type=data.event_type,
            style=data.style,
            vendors=vendor_list,
        )

        # Step 4 — save plan to database
        total_price = ai_result.get("total_price", 0.0)
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
            ai_suggestion=json.dumps(ai_result),
            ai_reasoning=ai_result.get("reasoning", ""),
            items=ai_result.get("selected_vendors", []),
        )

        return plan
    
    async def update(
        self,
        plan_id: uuid.UUID,
        user_id: uuid.UUID,
        data: PlanUpdate,
    ) -> PlanResponse:
        """Update plan name or style."""
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
        """Get all plans for current user."""
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
        """Get one plan — only if it belongs to current user."""
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
        """Delete a plan."""
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
        """
        Compare two plans side by side.
        Shows which is cheaper and why.
        """
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
    ) -> list:
        """
        Fetch vendors from DB that match user criteria.
        These are what we send to the AI.
        """
        query = (
            select(Vendor)
            .where(Vendor.is_active == True)
            .where(Vendor.min_price <= budget)
        )

        if guest_count:
            query = query.where(
                Vendor.max_capacity >= guest_count
            )

        if style:
            query = query.where(
                Vendor.style_tags.ilike(f"%{style}%")
            )

        # Get top 20 vendors by rating
        # We don't send ALL vendors to AI — just the best ones
        # This keeps the AI prompt focused and fast
        query = query.order_by(
            Vendor.rating.desc()
        ).limit(20)

        result = await self.db.execute(query)
        return result.scalars().all()