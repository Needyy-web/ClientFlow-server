"""Request models for client companies."""

from pydantic import BaseModel


class ClientCompanyCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    contact_name: str | None = None


class ClientCompanyUpdate(BaseModel):
    name: str
