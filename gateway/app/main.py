from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.routes import jobs, control, agents, skills, system, pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Lookbook SNS Automation",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(control.router, prefix="/api/control", tags=["control"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])


@app.get("/health")
def health():
    return {"status": "ok"}
