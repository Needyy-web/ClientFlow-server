"""Client-company endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text

from database import engine
from schemas.companies import ClientCompanyCreate, ClientCompanyUpdate
from dependencies import get_current_user

router = APIRouter(prefix="/client_companies", tags=["client_companies"])


@router.get("")
def get_client_companies(user=Depends(get_current_user)):
    with engine.connect() as connection:
        query = text(
            "SELECT id, organization_id, name FROM client_companies "
            "WHERE organization_id = :organization_id "
        )
        result = connection.execute(query, {"organization_id": user["organization_id"]})
        companies = result.mappings().all()

    return [dict(company) for company in companies]


@router.post('')
def create_client_companies(client_company: ClientCompanyCreate, user=Depends(get_current_user)):
    with engine.begin() as connection:
        query = text(
            "INSERT INTO client_companies (name, organization_id, email, notes, phone, contact_name) "
            "VALUES (:name, :organization_id, :email, :notes, :phone, :contact_name) "
            "RETURNING id, name, organization_id"
        )

        data = client_company.model_dump()
        data["organization_id"] = user["organization_id"]
        result = connection.execute(query, data)
        connection_companies = result.mappings().one()
        return dict(connection_companies)


@router.patch('/{company_id}')
def patch_client_company(company_id: int,
                         client_company_name: ClientCompanyUpdate,
                         user=Depends(get_current_user)
                         ):
    with engine.begin() as connection:
        query = text(
            "UPDATE client_companies "
            "SET name = :name "
            "WHERE id = :id "
            "AND organization_id = :organization_id "
            "RETURNING id, name, organization_id"
        )
        result = connection.execute(query,
                                    {
                                        "name": client_company_name.name,
                                        "id": company_id,
                                        "organization_id": user["organization_id"]
                                    }
                                    )
        patched_company_name = result.mappings().one_or_none()
        if patched_company_name is None:
            raise HTTPException(status_code=404, detail="Company not found")
        return dict(patched_company_name)


@router.delete('/{company_id}')
def delete_client_company(company_id: int, user=Depends(get_current_user)):
    with engine.begin() as connection:
        query = text(
            "DELETE FROM client_companies "
            "WHERE id = :id "
            "AND organization_id = :organization_id "
            "RETURNING id, name, organization_id"
        )
        result = connection.execute(query, {"id": company_id, "organization_id": user["organization_id"]})
        deleted_company = result.mappings().one_or_none()
        if deleted_company is None:
            raise HTTPException(status_code=404, detail="Company not found")
        return dict(deleted_company)
