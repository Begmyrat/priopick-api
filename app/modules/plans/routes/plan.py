import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.plans.schemas.plan import (
    PlanCompareResponse,
    PlanCreate,
    PlanListResponse,
    PlanResponse,
    PlanUpdate,
)
from app.modules.plans.services.plan import PlanService

router = APIRouter(prefix="/api/v1/plans", tags=["Plans"])


def get_plan_service(
    db: AsyncSession = Depends(get_db),
) -> PlanService:
    return PlanService(db)


@router.post("/", response_model=PlanResponse, status_code=201)
async def create_plan(
    data: PlanCreate,
    current_user=Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
):
    """Create a new AI-powered plan."""
    return await plan_service.create_plan(
        user_id=current_user.id,
        data=data,
    )


@router.get("/", response_model=PlanListResponse)
async def get_plans(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user=Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
):
    """Get all my plans."""
    return await plan_service.get_all(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


# ─────────────────────────────────────────────────────
# IMPORTANT: /compare MUST be defined BEFORE /{plan_id}
# Otherwise FastAPI treats "compare" as a UUID and fails
# ─────────────────────────────────────────────────────
@router.get("/compare", response_model=PlanCompareResponse)
async def compare_plans(
    plan_a_id: uuid.UUID = Query(description="First plan ID"),
    plan_b_id: uuid.UUID = Query(description="Second plan ID"),
    current_user=Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
):
    """
    Compare two plans side by side.

    Usage: /plans/compare?plan_a_id=uuid&plan_b_id=uuid
    """
    return await plan_service.compare(
        plan_a_id=plan_a_id,
        plan_b_id=plan_b_id,
        user_id=current_user.id,
    )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    current_user=Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
):
    """Get a single plan."""
    return await plan_service.get_by_id(
        plan_id=plan_id,
        user_id=current_user.id,
    )


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    data: PlanUpdate,
    current_user=Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
):
    """
    Update plan name or style.
    Cannot change budget or guest count — create a new plan instead.
    """
    return await plan_service.update(
        plan_id=plan_id,
        user_id=current_user.id,
        data=data,
    )


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: uuid.UUID,
    current_user=Depends(get_current_user),
    plan_service: PlanService = Depends(get_plan_service),
):
    """Delete a plan."""
    return await plan_service.delete(
        plan_id=plan_id,
        user_id=current_user.id,
    )