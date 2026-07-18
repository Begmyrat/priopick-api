import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.vendors.filters.vendor import VendorFilter
from app.modules.vendors.models.vendor import Vendor


class VendorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        filters: VendorFilter,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Vendor], int]:
        query = select(Vendor).where(Vendor.is_active == True)

        if filters.category:
            query = query.where(
                Vendor.category == filters.category.upper()
            )
        if filters.max_price is not None:
            query = query.where(Vendor.min_price <= filters.max_price)
        if filters.min_price is not None:
            query = query.where(Vendor.max_price >= filters.min_price)
        if filters.min_capacity is not None:
            query = query.where(
                Vendor.max_capacity >= filters.min_capacity
            )
        if filters.style is not None:
            query = query.where(
                Vendor.style_tags.ilike(f"%{filters.style}%")
            )
        if filters.rating_min is not None:
            query = query.where(Vendor.rating >= filters.rating_min)
        if filters.search is not None:
            query = query.where(
                Vendor.name.ilike(f"%{filters.search}%")
            )

        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total = await self.db.scalar(count_query)

        query = query.order_by(Vendor.rating.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        vendors = result.scalars().all()

        return vendors, total

    async def get_by_id(
        self, vendor_id: uuid.UUID
    ) -> Optional[Vendor]:
        result = await self.db.execute(
            select(Vendor).where(Vendor.id == vendor_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> Vendor:
        vendor = Vendor(**kwargs)
        self.db.add(vendor)
        await self.db.flush()
        await self.db.refresh(vendor)
        return vendor

    async def update(self, vendor: Vendor, **kwargs) -> Vendor:
        for key, value in kwargs.items():
            if value is not None:
                setattr(vendor, key, value)
        await self.db.flush()
        await self.db.refresh(vendor)
        return vendor

    async def delete(self, vendor: Vendor) -> None:
        vendor.is_active = False
        await self.db.flush()