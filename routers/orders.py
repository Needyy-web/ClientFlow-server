"""Order endpoints, including archived-order filtering."""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import engine
from schemas.orders import OrderCreate, OrderUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("")
def get_orders(archived: bool = False):
    with engine.connect() as connection:
        query = text("SELECT id, client_company_id, title, description, assignee_id, due_date, status, is_archived, created_at "
                     "FROM orders "
                     "WHERE is_archived = :archived "
                     "ORDER BY created_at DESC, id DESC;"
                     )
        result = connection.execute(query, {"archived": archived})
        orders = result.mappings().all()
        return [dict(order) for order in orders]

@router.get('/{order_id}')
def get_order(order_id: int):
    with engine.connect() as connection:
        query = text("SELECT id, client_company_id, title, description, assignee_id, due_date, status, is_archived, created_at "
                     "FROM orders "
                     "WHERE id = :id"
                     )
        result = connection.execute(query, {"id": order_id})
        order = result.mappings().one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return dict(order)

@router.post('/orders')
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

@router.patch('/{order_id}')
def patch_order(order_id: int, update: OrderUpdate):
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

@router.delete('/{order_id}')
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
