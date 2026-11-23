"""Organizations endpoints."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import engine
from schemas.organizations import OrganizationCreate, OrganizationUpdate

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get('')
def get_organizations():
    with engine.connect() as connection:
        query = text("SELECT id, name, created_at FROM organizations; ")
        result = connection.execute(query)
        organizations = result.mappings().all()

        return [dict(organization) for organization in organizations]

@router.post('')
def create_organization(organization: OrganizationCreate):
    with engine.begin() as connection:
        query = text(
            "INSERT INTO organizations (name) "
            "VALUES (:name) "
            "RETURNING name, id, created_at"
        )
        result = connection.execute(query, organization.model_dump())
        create_organization = result.mappings().one_or_none()
        if create_organization is None:
            raise HTTPException(status_code=404, detail="Organization not found.")
        return dict(create_organization)

@router.patch('/{organization_id}')
def patched_organization(organization_id: int, organization: OrganizationUpdate):
    with engine.begin() as connection:
        query = text(
            "UPDATE organizations "
            "SET name = :name "
            "WHERE id = :id "
            "RETURNING name, id, created_at"
        )
        result = connection.execute(query, {
            "name": organization.name,
            "id": organization_id
        })
        patched_organization = result.mappings().one_or_none()
        if patched_organization is None:
            raise HTTPException(status_code=404, detail="Organization not patched.")
        return dict(patched_organization)

@router.delete('/{organization_id}')
def delete_organization(organization_id: int):
    with engine.begin() as connection:
        query = text(
            "DELETE FROM organizations "
            "WHERE id = :id "
            "RETURNING name, id, created_at"
        )
        result = connection.execute(query, {"id": organization_id})
        deleted_organization = result.mappings().one_or_none()
        if deleted_organization is None:
            raise HTTPException(status_code=404, detail="Organization not deleted.")
        return dict(deleted_organization)


