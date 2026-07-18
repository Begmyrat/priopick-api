import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.vendors.filters.vendor import VendorFilter
from app.modules.vendors.schemas.vendor import (
    VendorCreate,
    VendorListResponse,
    VendorResponse,
    VendorUpdate,
)
from app.modules.vendors.services.vendor import VendorService

router = APIRouter(prefix="/api/v1/vendors", tags=["Vendors"])


def get_vendor_service(
    db: AsyncSession = Depends(get_db),
) -> VendorService:
    return VendorService(db)


@router.get("/", response_model=VendorListResponse)
async def get_vendors(
    filters: VendorFilter = Depends(),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    vendor_service: VendorService = Depends(get_vendor_service),
):
    return await vendor_service.get_all(
        filters=filters,
        page=page,
        page_size=page_size,
    )


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: uuid.UUID,
    vendor_service: VendorService = Depends(get_vendor_service),
):
    return await vendor_service.get_by_id(vendor_id)


@router.post("/", response_model=VendorResponse, status_code=201)
async def create_vendor(
    data: VendorCreate,
    vendor_service: VendorService = Depends(get_vendor_service),
):
    return await vendor_service.create(data)


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: uuid.UUID,
    data: VendorUpdate,
    vendor_service: VendorService = Depends(get_vendor_service),
):
    return await vendor_service.update(vendor_id, data)


@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: uuid.UUID,
    vendor_service: VendorService = Depends(get_vendor_service),
):
    return await vendor_service.delete(vendor_id)