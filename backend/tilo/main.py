from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tilo.api.routes import routers
from tilo.core.config import get_settings
from tilo.core.database import Base, SessionLocal, engine
from tilo.core.migrations import ensure_v02_schema
from tilo.services.bootstrap import seed_defaults


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_v02_schema(engine)
    with SessionLocal() as db:
        seed_defaults(db)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)
