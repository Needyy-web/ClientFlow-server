# ClientFlow server

FastAPI API backed by PostgreSQL. The application currently exposes orders and client companies CRUD routes.

## Project layout

- `main.py` — creates the FastAPI app and includes route modules.
- `database.py` — configures the shared SQLAlchemy engine from local environment variables.
- `routers/orders.py` — orders CRUD and archive filter.
- `routers/companies.py` — client companies CRUD.
- `schemas/orders.py`, `schemas/companies.py` — Pydantic request models.
- `seed.py` — optional Faker demo-data generator; see `SEEDING.md`.

## Run locally

1. Configure a local PostgreSQL database with the existing ClientFlow tables and relationships. This repository does not create or migrate the schema automatically.
2. Copy `.env.example` to `.env` and supply your **local** database connection values. Never commit `.env`.
3. Install requirements: `python -m pip install -r requirements.txt`.
4. Start from the repository root: `python -m uvicorn main:app --reload`.
5. Open `http://127.0.0.1:8000/docs`.

## Endpoints

- `GET /orders` — active orders by default, or `?archived=true` for archived orders.
- `GET /orders/{order_id}`, `POST /orders`, `PATCH /orders/{order_id}`, `DELETE /orders/{order_id}`.
- `GET /client_companies`, `POST /client_companies`, `PATCH /client_companies/{company_id}`, `DELETE /client_companies/{company_id}`.
- `GET /` — basic server health message.

**Caution:** `DELETE /orders/{order_id}` permanently removes an order. If the database has `ON DELETE CASCADE` configured, its related rows may also be deleted. This does not delete any physical files stored outside PostgreSQL.
