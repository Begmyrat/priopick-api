import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VendorCategory(str, Enum):
    VENUE = "VENUE"
    CATERING = "CATERING"
    SINGER = "SINGER"
    DJ = "DJ"
    CAR = "CAR"
    PHOTOGRAPHER = "PHOTOGRAPHER"
    FLORIST = "FLORIST"
    CAKE = "CAKE"


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    min_price: Mapped[float] = mapped_column(Float, nullable=False)
    max_price: Mapped[float] = mapped_column(Float, nullable=False)
    min_capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=True)
    style_tags: Mapped[str] = mapped_column(String(500), nullable=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )