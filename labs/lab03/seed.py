
import sqlite3
from contextlib import closing
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .database import BASE_DIR, get_connection, initialize_database


class SeedCategory(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)

    id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=40)


class SeedRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)

    code: str = Field(min_length=3, max_length=40)
    title: str = Field(min_length=3, max_length=120)
    category_id: int = Field(gt=0)
    value: float = Field(ge=0, le=10, allow_inf_nan=False)
    status: Literal["new", "in_progress", "done"]


class SeedData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    categories: list[SeedCategory] = Field(min_length=3, max_length=3)
    records: list[SeedRecord] = Field(min_length=8, max_length=8)


def main():

    try:
        initialize_database()

        with closing(get_connection()) as connection:
            categories_count = connection.execute(
                "SELECT COUNT(*) FROM categories"
            ).fetchone()[0]
            records_count = connection.execute(
                "SELECT COUNT(*) FROM records"
            ).fetchone()[0]

            if categories_count or records_count:
                print("Початкові дані додано: 3 категорії та 8 записів.")
                return 0

            seed_path = BASE_DIR / "data" / "seed.json"
            data = SeedData.model_validate_json(seed_path.read_text(encoding="utf-8"))

            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(item.id, item.name) for item in data.categories],
                )
                connection.executemany(
                    "INSERT INTO records "
                    "(code, title, category_id, value, status) "
                    "VALUES (?, ?, ?, ?, ?)",
                    [
                        (
                            item.code,
                            item.title,
                            item.category_id,
                            item.value,
                            item.status,
                        )
                        for item in data.records
                    ],
                )

        print("Початкові дані додано: 3 категорії та 8 записів.")
        return 0

    except (OSError, UnicodeError, ValidationError, sqlite3.Error) as error:
        print(f"Помилка =( {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())