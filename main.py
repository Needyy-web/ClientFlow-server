"""FastAPI application entry point."""

from fastapi import FastAPI

from routers.companies import router as companies_router
from routers.orders import router as orders_router

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "FastAPI server is running"}


app.include_router(orders_router)
app.include_router(companies_router)

