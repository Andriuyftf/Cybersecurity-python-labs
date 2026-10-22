import sqlite3
from contextlib import closing

from .database import get_connection


def create_category(name: str) -> dict:
    """Додати категорію та повернути її дані."""
    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute("INSERT INTO categories (name) VALUES (?)",(name,),)

        return {"id": cursor.lastrowid, "name": name}


def get_categories() -> list[dict]:
    """Отримати категорії за зростанням id."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()

        return [{"id": row[0], "name": row[1]} for row in rows]


def delete_category(category_id: int) -> None:
    """Видалити порожню категорію за її id."""
    with closing(get_connection()) as connection:  # noqa: SIM117
        with connection:
            cursor = connection.execute(
                "DELETE FROM categories WHERE id = ?",
                (category_id,),
            )

            if cursor.rowcount == 0:
                raise LookupError("Категорію не знайдено")

def create_record(
    code: str,
    title: str,
    category_id: int,
    value: float,
    status: str,
) -> dict:
    
    """Додати запис і повернути його разом із назвою категорії."""
    with closing(get_connection()) as connection:  # noqa: SIM117
        with connection:
            category = connection.execute(
                "SELECT id FROM categories WHERE id = ?",
                (category_id,),
            ).fetchone()

            if category is None:
                raise LookupError("Категорію не знайдено")

            cursor = connection.execute(
                "INSERT INTO records "
                "(code, title, category_id, value, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (code, title, category_id, value, status),
            )
            record_id = cursor.lastrowid

    return get_record(record_id)


def get_record(record_id: int) -> dict:
    """Отримати запис за id разом із назвою категорії."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT records.*, categories.name AS category_name
            FROM records
            JOIN categories ON records.category_id = categories.id
            WHERE records.id = ?
            """,
            (record_id,),
        ).fetchone()

        if row is None:
            raise LookupError("Запис не знайдено")

        return dict(row)

def get_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    
    """Отримати записи з фільтрами та поділом на сторінки."""

    query = """
        SELECT records.*, categories.name AS category_name
        FROM records
        JOIN categories ON records.category_id = categories.id
    """
    conditions = []
    parameters = []

    if category_id is not None:
        conditions.append("records.category_id = ?")
        parameters.append(category_id)

    if status is not None:
        conditions.append("records.status = ?")
        parameters.append(status)

    if min_value is not None:
        conditions.append("records.value >= ?")
        parameters.append(min_value)

    if q is not None:
        conditions.append("instr(records.title, ?) > 0")
        parameters.append(q)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY records.id LIMIT ? OFFSET ?"
    parameters.extend([limit, offset])

    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

def update_record(
    record_id: int,
    code: str,
    title: str,
    category_id: int,
    value: float,
    status: str,
) -> dict:
    
    """Повністю оновити змінювані поля запису."""
    
    with closing(get_connection()) as connection:  # noqa: SIM117
        with connection:
            category = connection.execute(
                "SELECT id FROM categories WHERE id = ?",
                (category_id,),
            ).fetchone()

            if category is None:
                raise LookupError("Категорію не знайдено")

            cursor = connection.execute(
                "UPDATE records "
                "SET code = ?, title = ?, category_id = ?, value = ?, status = ? "
                "WHERE id = ?",
                (code, title, category_id, value, status, record_id),
            )

            if cursor.rowcount == 0:
                raise LookupError("Запис не знайдено")

    return get_record(record_id)


def delete_record(record_id: int) -> None:

    """Видалити запис за його id."""
    
    with closing(get_connection()) as connection:  # noqa: SIM117
        with connection:
            cursor = connection.execute(
                "DELETE FROM records WHERE id = ?",
                (record_id,),
            )

            if cursor.rowcount == 0:
                raise LookupError("Запис не знайдено")

def create_records_many(records: list[dict]) -> list[dict]:
    """Додати всі записи пакета в одній транзакції."""
    
    record_ids = []

    with closing(get_connection()) as connection:  # noqa: SIM117
        with connection:
            for record in records:
                category = connection.execute(
                    "SELECT id FROM categories WHERE id = ?",
                    (record["category_id"],),
                ).fetchone()

                if category is None:
                    raise LookupError("Категорію не знайдено")

                cursor = connection.execute(
                    "INSERT INTO records "
                    "(code, title, category_id, value, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        record["code"],
                        record["title"],
                        record["category_id"],
                        record["value"],
                        record["status"],
                    ),
                )
                record_ids.append(cursor.lastrowid)

    return [get_record(record_id) for record_id in record_ids]