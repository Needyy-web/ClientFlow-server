"""FastAPI application entry point."""

from fastapi import FastAPI

from routers.companies import router as companies_router
from routers.orders import router as orders_router
from routers.organizations import router as organizations_router
from routers.auth import router as auth_router

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "FastAPI server is running"}


app.include_router(orders_router)
app.include_router(companies_router)
app.include_router(organizations_router)

app.include_router(auth_router)