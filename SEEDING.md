# Demo database seed

`seed.py` fills the existing PostgreSQL schema with fictitious, linked data.
It does not create tables, delete rows, or update existing rows.
It checks each record's identifying fields before insert, so rerunning does not duplicate the generated data.

## Run in PyCharm on Windows

1. Make sure PostgreSQL is running and your local `clientflow` database already has the eight project tables.
2. In the server project's terminal, activate its existing virtual environment if necessary.
3. Install dependencies: `python -m pip install -r requirements.txt`.
4. Configure your local `.env` using `.env.example` as a template. **Never commit `.env`**.
5. Ensure `DB_NAME` is pointing at your local development database.
6. Run: `python seed.py`. There is no need to run Uvicorn first.

## Expected additions on a fresh demo dataset

| Table | Rows added |
|---|---:|
| organizations | 3 |
| users | 15 |
| client_companies | 18 |
| orders | 90 |
| comments | 180 |
| activities | 120 |
| attachments | 9 |
| invitations | 6 |

Existing manually created rows remain in place. On a second run, these demo records should be reported as `existing` rather than added.

## Important details

- Faker uses Russian names and a fixed random seed. All demo emails end in the reserved `.test` domain.
- Order statuses match the current PostgreSQL CHECK constraint: `New`, `In Progress`, `Completed`, `Cancelled`.
- Relationships point to real database IDs returned by PostgreSQL, including members of the correct organization.
- Demo user accounts have bcrypt hashes made from unknown random passwords: they are **not login credentials**.
- Nine real sample `.txt` briefs are created locally in `demo_storage/seed/`. The `storage_key` in `attachments` is relative to `demo_storage/`; serving/downloading files needs a future API.
- Invite tokens are random and are never emailed. The seeder is for development, **not production**.
- Everything is written within one SQL transaction. On database error, SQL writes roll back. Demo files created on disk may remain and can be reused.
- An existing record matching a demo key is left untouched: the script will not overwrite manually edited values.
- Order and client-company routes are PostgreSQL-backed and live in `routers/orders.py` and `routers/companies.py`.
