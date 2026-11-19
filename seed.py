"""Fill the local ClientFlow database with realistic, related demo records.

Run: python seed.py

Preserves existing rows and skips demo rows already present on a repeated run.
"""

from __future__ import annotations

import json
import secrets
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
from faker import Faker
from sqlalchemy import text

from database import engine


fake = Faker("ru_RU")
fake.seed_instance(20261119)

# These are the exact statuses allowed by the existing PostgreSQL CHECK.
STATUSES = ("New", "In Progress", "Completed", "Cancelled")
ROLES = ("Owner", "Admin", "Employee", "Employee", "Employee")

ORGANIZATIONS = (
    "Атлас Диджитал (демо)",
    "Орбита Продакшн (демо)",
    "Вектор Проекты (демо)",
)

CLIENT_NAMES = (
    "Аврора Ритейл", "Меридиан Девелопмент", "Лайм Маркет", "Северный Парк",
    "Бриз Логистика", "Орион Образование", "Зенит Консалтинг", "Клевер Медиа",
    "Горизонт Тур", "Альфа Интерьер", "Пульс Фитнес", "Сигма Сервис",
    "Маяк Недвижимость", "Лотос Кафе", "Терра Эко", "Старт Академия",
    "Форум Тех", "Призма Дизайн",
)

ORDER_TEMPLATES = (
    ("Разработка корпоративного сайта", "Разработать адаптивные страницы, настроить форму заявки и подготовить сайт к публикации."),
    ("Редизайн личного кабинета", "Обновить навигацию, переработать карточки и улучшить сценарии пользователя."),
    ("Интеграция с CRM", "Подключить обмен заявками, добавить проверку данных и обработку ошибок API."),
    ("Разработка каталога услуг", "Реализовать категории, фильтры и страницу услуги с подробным описанием."),
    ("Оптимизация веб-приложения", "Уменьшить время загрузки, проверить мобильную версию и исправить найденные проблемы."),
)

COMMENT_TEMPLATES = (
    "Подготовил предварительный план работ и распределил задачи по этапам.",
    "Уточнил требования по форме обратной связи и добавил замечания в описание.",
    "Первый вариант готов. Проверьте структуру страниц и навигацию.",
    "Исправил замечания после внутреннего ревью, ожидаю подтверждения.",
    "Проверил отображение на мобильных устройствах и обновил стили.",
    "Согласовал изменения с командой и обновил сроки реализации.",
    "Собрал список пограничных случаев для проверки API.",
    "Добавил комментарии по следующему этапу работы.",
)

STORAGE_ROOT = Path(__file__).resolve().parent / "demo_storage"

# SQL identifiers are taken only from these constants, never external input.
TABLE_COLUMNS = {
    "organizations": {"name"},
    "users": {"name", "email", "password_hash", "organization_id", "role"},
    "client_companies": {"organization_id", "name", "contact_name", "email", "phone", "notes"},
    "orders": {"client_company_id", "title", "description", "assignee_id", "due_date", "status", "created_at"},
    "comments": {"order_id", "user_id", "content", "created_at"},
    "activities": {"order_id", "user_id", "action_type", "details", "created_at"},
    "attachments": {"order_id", "file_name", "storage_key", "mime_type", "file_size"},
    "invitations": {"organization_id", "email", "role", "token", "expires_at"},
}


def get_or_create(connection, table: str, identity: dict, fields: dict, stats: Counter) -> int:
    """Return the existing database ID, or insert a row and return its new ID."""
    valid = TABLE_COLUMNS[table]
    if not identity or not set(identity | fields).issubset(valid):
        raise ValueError(f"Invalid columns for {table}")

    where = " AND ".join(f"{column} = :key_{column}" for column in identity)
    existing = connection.execute(
        text(f"SELECT id FROM {table} WHERE {where} LIMIT 1"),
        {f"key_{column}": value for column, value in identity.items()},
    ).scalar_one_or_none()

    if existing is not None:
        stats[f"{table}: existing"] += 1
        return existing

    values = identity | fields
    columns = ", ".join(values)
    placeholders = ", ".join(f":{column}" for column in values)
    row_id = connection.execute(
        text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"),
        values,
    ).scalar_one()
    stats[f"{table}: added"] += 1
    return row_id


def create_demo_attachment(index: int, company_name: str, order_title: str) -> tuple[str, str, int]:
    relative = Path("seed") / f"brief_{index:03d}.txt"
    path = STORAGE_ROOT / relative
    contents = (
        f"ClientFlow / демонстрационный документ №{index}\n"
        f"Клиент: {company_name}\n"
        f"Заказ: {order_title}\n"
        "Назначение: пример текстового брифа для локальной демонстрации.\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != contents:
            raise RuntimeError(f"Demo file already exists with different content: {path}")
    else:
        path.write_bytes(contents)
    return relative.as_posix(), f"Бриф проекта {index:03d}.txt", len(contents)


def seed() -> Counter:
    stats: Counter = Counter()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    order_index = 0
    global_client_index = 0

    # A single database transaction; PostgreSQL rolls back on SQL errors.
    with engine.begin() as connection:
        for org_index, org_name in enumerate(ORGANIZATIONS, start=1):
            org_id = get_or_create(connection, "organizations", {"name": org_name}, {}, stats)
            employee_ids: list[int] = []

            for member_index, role in enumerate(ROLES, start=1):
                member_key = f"{org_index:02d}{member_index:02d}"
                email = f"demo.user{member_key}@clientflow.test"
                password_hash = bcrypt.hashpw(secrets.token_bytes(32), bcrypt.gensalt()).decode()
                member_id = get_or_create(
                    connection, "users", {"email": email},
                    {"name": fake.name(), "password_hash": password_hash,
                     "organization_id": org_id, "role": role}, stats,
                )
                actual_org = connection.execute(
                    text("SELECT organization_id FROM users WHERE id = :id"), {"id": member_id}
                ).scalar_one()
                if actual_org != org_id:
                    raise RuntimeError(f"Demo email already belongs to another organization: {email}")
                employee_ids.append(member_id)

            for company_position in range(6):
                global_client_index += 1
                base_name = CLIENT_NAMES[global_client_index - 1]
                company_name = f"{base_name} (демо)"
                company_id = get_or_create(
                    connection, "client_companies",
                    {"organization_id": org_id, "name": company_name},
                    {"contact_name": fake.name(),
                     "email": f"contact{global_client_index:02d}@clientflow.test",
                     "phone": f"+7 900 000 {global_client_index:02d} 00",
                     "notes": "Демонстрационная компания: контакты вымышлены."}, stats,
                )

                for template_index, (topic, description) in enumerate(ORDER_TEMPLATES):
                    order_index += 1
                    title = f"{topic} — {base_name}"
                    status = STATUSES[(order_index - 1) % len(STATUSES)]
                    created_at = now - timedelta(days=82 - ((order_index * 7) % 70))
                    due_date = (now + timedelta(days=7 + order_index % 45)).date()
                    if status in ("Completed", "Cancelled"):
                        due_date = (now - timedelta(days=order_index % 30 + 1)).date()
                    assignee = None if template_index == 0 else employee_ids[(order_index + 1) % len(employee_ids)]

                    order_id = get_or_create(
                        connection, "orders", {"client_company_id": company_id, "title": title},
                        {"description": description, "assignee_id": assignee,
                         "due_date": due_date, "status": status,
                         "created_at": created_at}, stats,
                    )

                    for comment_index in range(2):
                        author_id = employee_ids[(order_index + comment_index) % len(employee_ids)]
                        content = COMMENT_TEMPLATES[(order_index + comment_index * 3) % len(COMMENT_TEMPLATES)]
                        get_or_create(
                            connection, "comments",
                            {"order_id": order_id, "user_id": author_id, "content": content},
                            {"created_at": created_at + timedelta(days=comment_index + 1)}, stats,
                        )

                    activity_types = ["order_created"]
                    if order_index <= 30:
                        activity_types.append("status_changed")
                    for activity_type in activity_types:
                        details = json.dumps(
                            {"source": "demo_seed", "event": activity_type,
                             "order_number": order_index, "status": status},
                            ensure_ascii=False, sort_keys=True,
                        )
                        get_or_create(
                            connection, "activities",
                            {"order_id": order_id, "action_type": activity_type, "details": details},
                            {"user_id": employee_ids[0], "created_at": created_at + timedelta(hours=2)},
                            stats,
                        )

                    if order_index % 10 == 0:
                        storage_key, filename, size = create_demo_attachment(order_index, company_name, title)
                        get_or_create(
                            connection, "attachments", {"storage_key": storage_key},
                            {"order_id": order_id, "file_name": filename,
                             "mime_type": "text/plain", "file_size": size}, stats,
                        )

            for invitation_number, role in enumerate(("Admin", "Employee"), start=1):
                email = f"demo.invite{org_index:02d}{invitation_number:02d}@clientflow.test"
                get_or_create(
                    connection, "invitations", {"organization_id": org_id, "email": email},
                    {"role": role, "token": secrets.token_urlsafe(32),
                     "expires_at": now + timedelta(days=14)}, stats,
                )
    return stats


if __name__ == "__main__":
    print(f"Seeding local database: {engine.url.render_as_string(hide_password=True)}")
    print("Development only. Existing database records will be preserved.")
    results = seed()
    for table in TABLE_COLUMNS:
        print(f"{table:18} added={results[f'{table}: added']:3} existing={results[f'{table}: existing']:3}")
    print("Done. Example files are in demo_storage/seed/.")
