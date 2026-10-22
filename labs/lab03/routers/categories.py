import sqlite3

from fastapi import APIRouter, HTTPException, Path, Response

from .. import repository
from ..schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Категорії"])


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Отримати список категорій",
)
def list_categories() -> list[dict]:
    """Повернути категорії за зростанням id."""
    return repository.get_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=201,
    summary="Створити категорію",
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
)
def add_category(data: CategoryCreate) -> dict:
    """Створити категорію з унікальною назвою."""
    try:
        return repository.create_category(data.name)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Категорія з такою назвою вже існує",
        ) from error


@router.delete(
    "/{category_id}",
    status_code=204,
    summary="Видалити порожню категорію",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
)
def remove_category(
    category_id: int = Path(gt=0, description="Ідентифікатор категорії"),
) -> Response:
    """Видалити категорію, яка не містить записів."""
    try:
        repository.delete_category(category_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Категорія містить записи",
        ) from error

    return Response(status_code=204)