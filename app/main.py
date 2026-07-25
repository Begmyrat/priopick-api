from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import Base, engine
from app.modules.auth.models import user  # noqa
from app.modules.vendors.models import vendor  # noqa
from app.modules.plans.models import plan  # noqa
from app.modules.auth.routes.auth import router as auth_router
from app.modules.vendors.routes.vendor import router as vendor_router
from app.modules.plans.routes.plan import router as plan_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="PrioPick API",
    version="1.0.0",
    description="Smart budget planner with AI suggestions",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(vendor_router)
app.include_router(plan_router)
