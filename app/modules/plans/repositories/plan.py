import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.plans.models.plan import Plan, PlanItem


class PlanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Plan], int]:
        query = (
            select(Plan)
            .where(Plan.user_id == user_id)
            .options(selectinload(Plan.items))
            .order_by(Plan.created_at.desc())
        )

        count_query = select(func.count()).select_from(
            select(Plan).where(Plan.user_id == user_id).subquery()
        )
        total = await self.db.scalar(count_query)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        plans = result.scalars().all()

        return plans, total
    
    async def update(self, plan: Plan, **kwargs) -> Plan:
        for key, value in kwargs.items():
            if value is not None:
                setattr(plan, key, value)
        await self.db.flush()

        result = await self.db.execute(
            select(Plan)
            .where(Plan.id == plan.id)
            .options(selectinload(Plan.items))
        )
        return result.scalar_one()

    async def get_by_id(
        self,
        plan_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Plan]:
        result = await self.db.execute(
            select(Plan)
            .where(Plan.id == plan_id)
            .where(Plan.user_id == user_id)
            .options(selectinload(Plan.items))
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: uuid.UUID,
        name: str,
        budget: float,
        guest_count: int,
        event_type: Optional[str],
        style: Optional[str],
        total_price: float,
        remaining_budget: float,
        ai_suggestion: str,
        ai_reasoning: str,
        items: List[dict],
    ) -> Plan:
        plan_items = [
            PlanItem(
                vendor_id=item["vendor_id"],
                vendor_name=item["vendor_name"],
                vendor_category=item["vendor_category"],
                price=item["price"],
                notes=item.get("notes"),
            )
            for item in items
        ]

        plan = Plan(
            user_id=user_id,
            name=name,
            budget=budget,
            guest_count=guest_count,
            event_type=event_type,
            style=style,
            total_price=total_price,
            remaining_budget=remaining_budget,
            ai_suggestion=ai_suggestion,
            ai_reasoning=ai_reasoning,
            items=plan_items
        )
        
        self.db.add(plan)
        await self.db.flush()

        return plan

    async def delete(self, plan: Plan) -> None:
        await self.db.delete(plan)
        await self.db.flush()