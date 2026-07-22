from typing import List
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Which user created this plan
    # ForeignKey links to users table
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Plan name — user can name their plans
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # User preferences used to generate this plan
    budget: Mapped[float] = mapped_column(Float, nullable=False)
    guest_count: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=True)
    style: Mapped[str] = mapped_column(String(50), nullable=True)

    # AI generated results
    total_price: Mapped[float] = mapped_column(Float, nullable=True)
    remaining_budget: Mapped[float] = mapped_column(Float, nullable=True)

    # AI suggestion stored as JSON string
    # Contains the full list of suggested vendors
    ai_suggestion: Mapped[str] = mapped_column(Text, nullable=True)

    # AI explanation of why it chose these vendors
    ai_reasoning: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    # Relationship to plan items
    # One plan has many items
    items: Mapped[List["PlanItem"]] = relationship(
        "PlanItem",
        back_populates="plan",
        cascade="all, delete-orphan",
    )


class PlanItem(Base):
    """
    Each row = one vendor selected for a plan.
    One plan has multiple items (venue + DJ + photographer etc.)
    """
    __tablename__ = "plan_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id"),
        nullable=False
    )

    # We store vendor details directly here
    # So plan stays intact even if vendor is deleted later
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_category: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationship back to plan
    plan: Mapped["Plan"] = relationship("Plan", back_populates="items")