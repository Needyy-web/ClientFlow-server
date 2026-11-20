"""Client-company endpoints."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import engine
from schemas.companies import ClientCompanyCreate, ClientCompanyUpdate

router = APIRouter(prefix="/client_companies", tags=["client_companies"])


@router.get("")
def get_client_companies():
    with engine.connect() as connection:
        query = text("SELECT id, organization_id, name FROM client_companies")
        result = connection.execute(query)
        companies = result.mappings().all()

    return [dict(company) for company in companies]

@router.post('')
def create_client_companies(client_company: ClientCompanyCreate):
    with engine.begin() as connection:
        query = text(
            "INSERT INTO client_companies (name, organization_id) "
                     "VALUES (:name, :organization_id) "
            "RETURNING id, name, organization_id"
                     )
        result = connection.execute(query, client_company.model_dump())
        connection_companies = result.mappings().one()
        return dict(connection_companies)

@router.patch('/{company_id}')
def patch_client_company(company_id: int, client_company_name: ClientCompanyUpdate):
    with engine.begin() as connection:
        query = text(
            "UPDATE client_companies "
            "SET name = :name "
            "WHERE id = :id "
            "RETURNING id, name, organization_id"
        )
        result = connection.execute(query,
                                    {
                                        "name": client_company_name.name,
                                        "id": company_id
                                    }
                                    )
        patched_company_name = result.mappings().one_or_none()
        if patched_company_name is None:
            raise HTTPException(status_code=404, detail="Company not found")
        return dict(patched_company_name)

@router.delete('/{company_id}')
def delete_client_company(company_id: int):
    with engine.begin() as connection:
        query = text(
            "DELETE FROM client_companies "
            "WHERE id = :id "
            "RETURNING id, name, organization_id"
             )
        result = connection.execute(query, {"id": company_id})
        deleted_company = result.mappings().one_or_none()
        if deleted_company is None:
            raise HTTPException(status_code=404, detail="Company not found")
        return dict(deleted_company)
