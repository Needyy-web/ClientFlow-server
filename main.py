from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import engine
from sqlalchemy import text
from typing import Literal
app = FastAPI()

@app.get('/')
def read_root():
    return {"message": "FastAPI server is running"}

@app.get("/orders")
def get_orders(archived: bool = False):
    with engine.connect() as connection:
        query = text("SELECT id, client_company_id, title, description, assignee_id, due_date, status, created_at "
                     "FROM orders "
                     "WHERE is_archived = :archived "
                     "ORDER BY created_at DESC, id DESC;"
                     )
        result = connection.execute(query, {"is_archived": archived})
        orders = result.mappings().all()
        return [dict(order) for order in orders]

@app.get('/orders/{order_id}')
def get_order(order_id: int):
    with engine.connect() as connection:
        query = text("SELECT id, client_company_id, title, description, assignee_id, due_date, status, created_at "
                     "FROM orders "
                     "WHERE id = :id"
                     )
        result = connection.execute(query, {"id": order_id})
        order = result.mappings().one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return dict(order)

class OrderCreate(BaseModel):
    client_company_id: int
    title: str
    description: str | None = None
    status: str = "New"
@app.post('/orders')
def create_order(order: OrderCreate):
    with engine.begin() as connection:
        query = text(
            "INSERT INTO orders (client_company_id, title, description, status) "
            "VALUES (:client_company_id, :title, :description, :status) "
            "RETURNING id, title, description, status"
        )
        result = connection.execute(query, order.model_dump())
        posted_order = result.mappings().one()
        return dict(posted_order)

class OrderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Literal["New", "In Progress", "Completed", "Cancelled"] | None = None
    is_archived: bool | None = None
@app.patch('/orders/{order_id}')
def patch_order(order_id: int, update: OrderUpdate):
    with engine.begin() as connection:
        data = update.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(
                status_code=400,
                detail="No fields to update"
            )
        if ("title" in data and data["title"] is None) or \
                ("status" in data and data["status"] is None):
            raise HTTPException(
                status_code=422,
                detail="Title and status cannot be null"
            )
        set_parts = []
        for field in data:
            set_parts.append(f"{field} = :{field}")
        set_clause = ", ".join(set_parts)
        query = text(f"UPDATE orders SET {set_clause} "
                     "WHERE id = :id "
                     "RETURNING id, title, description, status, is_archived"
                     )

        result = connection.execute(query, {**data, "id": order_id})
        patched_order = result.mappings().one_or_none()
        if patched_order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return dict(patched_order)

@app.delete('/orders/{order_id}')
def delete_order(order_id: int):
    with engine.begin() as connection:
        query = text(
            "DELETE FROM orders "
            "WHERE id = :id "
            "RETURNING id, title, description, status, is_archived"
        )
        result = connection.execute(query, {"id": order_id})
        deleted_order = result.mappings().one_or_none()
        if deleted_order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return dict(deleted_order)

@app.get("/client_companies")
def get_client_companies():
    with engine.connect() as connection:
        query = text("SELECT id, organization_id, name FROM client_companies")
        result = connection.execute(query)
        companies = result.mappings().all()

    return [dict(company) for company in companies]

class ClientCompanyCreate(BaseModel):
    name: str
    organization_id: int

@app.post('/client_companies')
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

class ClientCompanyUpdate(BaseModel):
    name: str
@app.patch('/client_companies/{company_id}')
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
        patched_company_name = result.mappings().one()
        return dict(patched_company_name)

@app.delete('/client_companies/{company_id}')
def delete_client_company(company_id: int):
    with engine.begin() as connection:
        query = text(
            "DELETE FROM client_companies "
            "WHERE id = :id "
            "RETURNING id, name, organization_id"
             )
        result = connection.execute(query, {"id": company_id})
        deleted_company = result.mappings().one()
        return dict(deleted_company)

