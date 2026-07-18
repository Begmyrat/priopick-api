import math
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.vendors.filters.vendor import VendorFilter
from app.modules.vendors.repositories.vendor import VendorRepository
from app.modules.vendors.schemas.vendor import (
    VendorCreate,
    VendorListResponse,
    VendorResponse,
    VendorUpdate,
)


class VendorService:
    def __init__(self, db: AsyncSession):
        self.repo = VendorRepository(db)

    async def get_all(
        self,
        filters: VendorFilter,
        page: int = 1,
        page_size: int = 10,
    ) -> VendorListResponse:
        vendors, total = await self.repo.get_all(
            filters=filters,
            page=page,
            page_size=page_size,
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        return VendorListResponse(
            items=vendors,
            total=total,
            page=page,
            page_size=page_size,
            pages=total_pages,
        )

    async def get_by_id(self, vendor_id: uuid.UUID) -> VendorResponse:
        vendor = await self.repo.get_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        return vendor

    async def create(self, data: VendorCreate) -> VendorResponse:
        return await self.repo.create(
            name=data.name,
            category=data.category.value,
            description=data.description,
            min_price=data.min_price,
            max_price=data.max_price,
            min_capacity=data.min_capacity,
            max_capacity=data.max_capacity,
            style_tags=data.style_tags,
            location=data.location,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
        )

    async def update(
        self,
        vendor_id: uuid.UUID,
        data: VendorUpdate,
    ) -> VendorResponse:
        vendor = await self.repo.get_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        update_data = data.model_dump(exclude_unset=True)
        return await self.repo.update(vendor, **update_data)

    async def delete(self, vendor_id: uuid.UUID) -> dict:
        vendor = await self.repo.get_by_id(vendor_id)
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor not found"
            )
        await self.repo.delete(vendor)
        return {"message": "Vendor deleted successfully"}