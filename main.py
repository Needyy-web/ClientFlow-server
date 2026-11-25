"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.companies import router as companies_router
from routers.orders import router as orders_router
from routers.organizations import router as organizations_router
from routers.auth import router as auth_router

app = FastAPI()

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def read_root():
    return {"message": "FastAPI server is running"}


app.include_router(orders_router)
app.include_router(companies_router)
app.include_router(organizations_router)

app.include_router(auth_router)