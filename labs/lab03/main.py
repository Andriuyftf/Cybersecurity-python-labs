import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

from .config import MAX_VALUE, MIN_VALUE, THRESHOLD, UNIT
from .database import initialize_database
from .routers import categories, records

log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Створити відсутні таблиці під час запуску API."""
    initialize_database()
    yield


app = FastAPI(
    title="Реєстр ризиків хмарної конфігурації",
    description=(
        "Облік знахідок аудиту хмарної конфігурації. "
        f"Навчальна оцінка ризику: від {MIN_VALUE} до {MAX_VALUE} {UNIT}. "
        f"Поріг: {THRESHOLD} {UNIT}."
    ),
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", summary="Перевірка доступності API")
def ping() -> dict[str, str]:
    """Повернути повідомлення про доступність API."""
    return {"status": "ok"}

@app.exception_handler(sqlite3.Error)
async def database_error_handler(
    _request: Request, error: sqlite3.Error
) -> JSONResponse:
    """Записати технічну помилку SQLite та повернути відповідь 500."""
    log.error("Помилка роботи з базою даних =(", exc_info=error)
    return JSONResponse(
        status_code=500,
        content={"detail": "Помилка роботи з базою даних"},
    )

@app.get("/student", summary="Отримати дані студента")
def get_student() -> dict[str, str | int]:
    """Повернути ПІБ, групу та номер варіанта."""
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }