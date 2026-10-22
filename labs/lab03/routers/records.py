import sqlite3
from typing import Literal

from fastapi import APIRouter, Body, HTTPException, Path, Query, Response

from .. import repository
from ..config import MAX_VALUE, MIN_VALUE
from ..schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["Записи"])


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Отримати список записів",
)
def list_records(
    category_id: int | None = Query(
        default=None, gt=0, description="Ідентифікатор категорії"
    ),
    status: Literal["new", "in_progress", "done"] | None = Query(
        default=None, description="Статус опрацювання"
    ),
    min_value: float | None = Query(
        default=None,
        ge=MIN_VALUE,
        le=MAX_VALUE,
        allow_inf_nan=False,
        description="Мінімальна оцінка ризику",
    ),
    q: str | None = Query(
        default=None,
        min_length=1,
        max_length=120,
        description="Буквальний підрядок у назві з урахуванням регістру",
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Кількість результатів"),
    offset: int = Query(default=0, ge=0, description="Кількість пропущених записів"),
) -> list[dict]:
    """Повернути відфільтровані записи за зростанням id."""
    return repository.get_records(
        category_id=category_id,
        status=status,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )

@router.post(
    "/many",
    response_model=list[RecordRead],
    status_code=201,
    summary="Додати пакет записів",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Дублікат коду в базі або всередині пакета"},
    },
)

def add_records_many(
    data: list[RecordCreate] = Body(min_length=1, max_length=100),
) -> list[dict]:
    """Перевірити та додати весь пакет записів однією транзакцією."""
    try:
        return repository.create_records_many([item.model_dump() for item in data])
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Дублікат коду в базі або всередині пакета",
        ) from error

@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис за id",
    responses={404: {"description": "Запис не знайдено"}},
)
def read_record(
    record_id: int = Path(gt=0, description="Ідентифікатор запису"),
) -> dict:
    """Повернути запис разом із назвою категорії."""
    try:
        return repository.get_record(record_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post(
    "",
    response_model=RecordRead,
    status_code=201,
    summary="Створити запис",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Запис із таким кодом уже існує"},
    },
)
def add_record(data: RecordCreate) -> dict:
    """Створити запис у наявній категорії."""
    try:
        return repository.create_record(**data.model_dump())
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409, detail="Запис із таким кодом уже існує"
        ) from error


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю оновити запис",
    responses={
        404: {"description": "Запис або категорію не знайдено"},
        409: {"description": "Запис із таким кодом уже існує"},
    },
)
def replace_record(
    data: RecordReplace,
    record_id: int = Path(gt=0, description="Ідентифікатор запису"),
) -> dict:
    """Замінити всі змінювані поля запису зі збереженням id."""
    try:
        return repository.update_record(record_id, **data.model_dump())
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409, detail="Запис із таким кодом уже існує"
        ) from error


@router.delete(
    "/{record_id}",
    status_code=204,
    summary="Видалити запис",
    responses={404: {"description": "Запис не знайдено"}},
)
def remove_record(
    record_id: int = Path(gt=0, description="Ідентифікатор запису"),
) -> Response:
    """Видалити наявний запис."""
    try:
        repository.delete_record(record_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    return Response(status_code=204)