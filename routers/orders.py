"""Order endpoints, including archived-order filtering."""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text

from database import engine
from schemas.orders import OrderCreate, OrderUpdate
from dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("")
def get_orders(archived: bool = False, user=Depends(get_current_user)):
    with engine.connect() as connection:
        query = text("SELECT "
                     "orders.id, "
                     "orders.client_company_id, "
                     "orders.title, "
                     "orders.description, "
                     "orders.assignee_id, "
                     "orders.due_date, "
                     "orders.status, "
                     "orders.is_archived, "
                     "orders.created_at "
                     "FROM orders "
                     "JOIN client_companies "
                     "ON orders.client_company_id = client_companies.id "
                     "WHERE orders.is_archived = :archived "
                     "AND client_companies.organization_id = :organization_id "
                     "ORDER BY orders.created_at DESC, orders.id DESC;"
                     )
        result = connection.execute(query, {"archived": archived, "organization_id": user["organization_id"]})
        orders = result.mappings().all()
        return [dict(order) for order in orders]

@router.get('/{order_id}')
def get_order(order_id: int, user=Depends(get_current_user)):
    with engine.connect() as connection:
        query = text("SELECT "
                     "orders.id, "
                     "orders.client_company_id, "
                     "orders.title, "
                     "orders.description, "
                     "orders.assignee_id, "
                     "orders.due_date, "
                     "orders.status, "
                     "orders.is_archived,"
                     "orders.created_at "
                     "FROM orders "
                     "JOIN client_companies "
                     "ON orders.client_company_id = client_companies.id "
                     "WHERE orders.id = :id "
                     "AND client_companies.organization_id = :organization_id"
                     )
        result = connection.execute(query, {"id": order_id, "organization_id": user["organization_id"]})
        order = result.mappings().one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return dict(order)

@router.post('')
def create_order(order: OrderCreate, user=Depends(get_current_user)):
    with engine.begin() as connection:
        check_query = text(
            "SELECT id FROM client_companies "
            "WHERE id = :client_company_id "
            "AND organization_id = :organization_id"
        )

        check_result = connection.execute(check_query, {
            "client_company_id": order.client_company_id,
            "organization_id": user["organization_id"]
        })

        company = check_result.mappings().one_or_none()

        if company is None:
            raise HTTPException(
                status_code=404,
                detail="Company not found"
            )

        query = text(
            "INSERT INTO orders (client_company_id, title, description, status) "
            "VALUES (:client_company_id, :title, :description, :status) "
            "RETURNING id, title, description, status"
        )

        result = connection.execute(query, order.model_dump())
        posted_order = result.mappings().one()

        return dict(posted_order)

@router.patch('/{order_id}')
def patch_order(order_id: int, update: OrderUpdate, user=Depends(get_current_user)):
    with engine.begin() as connection:
        data = update.model_dump(exclude_unset=True)

        if not data:
            raise HTTPException(
                status_code=400,
                detail="No fields to update"
            )

        if any(
            field in data and data[field] is None
            for field in ("title", "status", "is_archived")
        ):
            raise HTTPException(
                status_code=422,
                detail="Title, status and is_archived cannot be null"
            )

        allowed_fields = {
            "title", "description", "status", "is_archived", "due_date"
        }

        if not data.keys() <= allowed_fields:
            raise HTTPException(
                status_code=400,
                detail="Invalid fields"
            )

        set_parts = []

        for field in data:
            set_parts.append(f"{field} = :{field}")

        set_clause = ", ".join(set_parts)

        query = text(
            f"UPDATE orders SET {set_clause} "
            "WHERE orders.id = :id "
            "AND EXISTS ("
            "SELECT 1 FROM client_companies "
            "WHERE client_companies.id = orders.client_company_id "
            "AND client_companies.organization_id = :organization_id"
            ") "
            "RETURNING id, title, description, status, is_archived"
        )

        result = connection.execute(query, {
            **data,
            "id": order_id,
            "organization_id": user["organization_id"]
        })

        patched_order = result.mappings().one_or_none()

        if patched_order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        return dict(patched_order)

@router.delete('/{order_id}')
def delete_order(order_id: int, user=Depends(get_current_user)):
    with engine.begin() as connection:
        query = text(
            "DELETE FROM orders "
            "WHERE orders.id = :id "
            "AND EXISTS ("
            "SELECT 1 FROM client_companies "
            "WHERE client_companies.id = orders.client_company_id "
            "AND client_companies.organization_id = :organization_id"
            ") "
            "RETURNING id, title, description, status, is_archived"
        )

        result = connection.execute(query, {
            "id": order_id,
            "organization_id": user["organization_id"]
        })

        deleted_order = result.mappings().one_or_none()

        if deleted_order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        return dict(deleted_order)