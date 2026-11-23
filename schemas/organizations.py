"""Request models for organization endpoints."""

from pydantic import BaseModel, EmailStr

class OrganizationCreate(BaseModel):
    name: str

class OrganizationUpdate(BaseModel):
    name: str

class OrganizationRegister(BaseModel):
    organization_name: str
    owner_name: str
    email: EmailStr
    password: str

