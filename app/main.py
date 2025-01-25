from fastapi import FastAPI
from app.api.v1.routes import users
from app.db.database import get_database, sqlalchemy_engine
from app.models.models import Base
from fastapi.middleware.cors import CORSMiddleware
from app.settings import origins

app = FastAPI(
    title="Procuremet App API",
    docs_url="/",
    description="The purpose of this API Rest is to provide the tools to store and bring data related to some procurement processes.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await get_database().connect()
    Base.metadata.create_all(sqlalchemy_engine)


@app.on_event("shutdown")
async def shutdown():
    await get_database().disconnect()


app.include_router(users.router, prefix="/api/v1", tags=["Users"])
