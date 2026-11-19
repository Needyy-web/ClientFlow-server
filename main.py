from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import engine
from sqlalchemy import text
app = FastAPI()

@app.get('/')
def read_root():
    return {"message": "FastAPI server is running"}
@app.get('/orders')
def get_orders():
    return orders

class OrderCreate(BaseModel):
    title: str
    status: str

@app.post('/orders')
def create_order(order: OrderCreate):
    creating_order = order.model_dump()
    creating_order["id"] = len(orders) + 1
    orders.append(creating_order)
    return creating_order

@app.get('/orders/{order_id}')
def get_order(order_id: int):
    for order in orders:
        if order["id"] == order_id:
            return order
    raise HTTPException(status_code=404, detail="Order not found")


class OrderUpdate(BaseModel):
    status: str
@app.patch('/orders/{order_id}')
def update_order(order_id: int, order: OrderUpdate):
    for current_order in orders:
        if current_order["id"] == order_id:
            current_order["status"] = order.status
            return current_order
    raise HTTPException(status_code=404, detail="Order not found")

@app.delete('/orders/{order_id}')
def delete_order(order_id: int):
    for current_order in orders:
        if current_order["id"] == order_id:
            orders.remove(current_order)
            return current_order
    raise HTTPException(status_code=404, detail="Order not found")

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