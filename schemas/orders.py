"""Request models for orders."""

from typing import Literal

from pydantic import BaseModel


class OrderCreate(BaseModel):
    client_company_id: int
    title: str
    description: str | None = None
    status: str = "New"


class OrderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Literal["New", "In Progress", "Completed", "Cancelled"] | None = None
    is_archived: bool | None = None
