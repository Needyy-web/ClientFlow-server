"""Request models for client companies."""

from pydantic import BaseModel


class ClientCompanyCreate(BaseModel):
    name: str
    organization_id: int


class ClientCompanyUpdate(BaseModel):
    name: str
