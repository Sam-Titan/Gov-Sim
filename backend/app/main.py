from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.errors import add_error_handlers
from app.routes import health, places, report, simulate
from govsim.service import Service


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.service = Service()  # load data, sample agents, build the design once
    yield


app = FastAPI(title="GovSim API", version="0.1.0", lifespan=lifespan)
add_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (health.router, places.router, simulate.router, report.router):
    app.include_router(r, prefix="/api")
