import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )
    style_preference: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )
    guest_count: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )
    budget: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )