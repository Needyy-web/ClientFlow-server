"""Request models for organization endpoints."""

from pydantic import BaseModel

class OrganizationCreate(BaseModel):
    name: str

class OrganizationUpdate(BaseModel):
    name: str

