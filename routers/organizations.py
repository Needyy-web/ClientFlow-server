"""Organizations endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
import bcrypt

from database import engine
from schemas.organizations import OrganizationCreate, OrganizationUpdate, OrganizationRegister

from dependencies import get_current_user, require_admin, require_owner

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get('')
def get_organizations(user=Depends(get_current_user)):
    with engine.connect() as connection:
        query = text(
            "SELECT organizations.id, organizations.name, organizations.created_at FROM organizations "
            "WHERE id = :organization_id "
        )
        result = connection.execute(query, {"organization_id": user["organization_id"]})
        organization = result.mappings().one_or_none()

        if organization is None:
            raise HTTPException(status_code=404, detail="Organization not found")
        return dict(organization)


@router.patch('/{organization_id}')
def patched_organization(organization_id: int, organization: OrganizationUpdate, user=Depends(require_admin)):
    with engine.begin() as connection:
        query = text(
            "UPDATE organizations "
            "SET name = :name "
            "WHERE organizations.id = :id "
            "AND id = :organization_id "
            "RETURNING name, id, created_at"
        )
        result = connection.execute(query, {
            "name": organization.name,
            "id": organization_id,
            "organization_id": user["organization_id"]
        })
        patched_organization = result.mappings().one_or_none()
        if patched_organization is None:
            raise HTTPException(status_code=404, detail="Organization not patched.")
        return dict(patched_organization)


@router.delete('/{organization_id}')
def delete_organization(organization_id: int, user=Depends(require_owner)):
    with engine.begin() as connection:
        query = text(
            "DELETE FROM organizations "
            "WHERE organizations.id = :id "
            "AND organizations.id = :organization_id "
            "RETURNING name, id, created_at"
        )
        result = connection.execute(query, {"id": organization_id, "organization_id": user["organization_id"]})
        deleted_organization = result.mappings().one_or_none()
        if deleted_organization is None:
            raise HTTPException(status_code=404, detail="Organization not deleted.")
        return dict(deleted_organization)


def hash_password(password: str):
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode("utf-8")


@router.post("/register")
def register_organization(organization: OrganizationRegister):
    with engine.begin() as connection:
        query = text("SELECT EXISTS "
                     "(SELECT 1 "
                     "FROM users "
                     "WHERE LOWER(email) = LOWER(:email)"
                     ") AS email_exists "
                     )
        result = connection.execute(query, {"email": organization.email})
        is_email_exists = result.scalar_one()
        if is_email_exists:
            raise HTTPException(status_code=409, detail="Email already registered")
        insert_organization = text(
            "INSERT INTO organizations (name) "
            "VALUES (:name) "
            "RETURNING id"
        )
        result = connection.execute(insert_organization, {"name": organization.organization_name})
        organization_id = result.scalar_one()

        hashed_password = hash_password(organization.password)
        insert_owner = text(
            "INSERT INTO users (name, email, password_hash, organization_id, role) "
            "VALUES (:name, :email, :password_hash, :organization_id, :role) "
            "RETURNING id, email, organization_id, role"
        )
        result = connection.execute(insert_owner, {"name": organization.owner_name,
                                                   "email": organization.email,
                                                   "password_hash": hashed_password,
                                                   "organization_id": organization_id,
                                                   "role": "Owner"
                                                   })
        created_owner = result.mappings().one()
        return dict(created_owner)
