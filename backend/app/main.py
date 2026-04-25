from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import routers
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.services.bootstrap import seed_defaults


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routers:
    app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_defaults(db)
