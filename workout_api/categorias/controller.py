from uuid import uuid4
from typing import Iterable
from fastapi import APIRouter, Body, HTTPException, status, Query, Depends
from pydantic import UUID4
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from fastapi_pagination import LimitOffsetPage, LimitOffsetParams
from fastapi_pagination.ext.sqlalchemy_future import paginate

from workout_api.categorias.schemas import CategoriaIn, CategoriaOut
from workout_api.categorias.models import CategoriaModel

from workout_api.contrib.dependencies import DatabaseDependency


router = APIRouter()


@router.post(
    '/',
    summary='Criar uma nova Categoria',
    status_code=status.HTTP_201_CREATED,
    response_model=CategoriaOut,
)
async def post(
    db_session: DatabaseDependency,
    categoria_in: CategoriaIn = Body(...)
) -> CategoriaOut:
    categoria_out = CategoriaOut(id=uuid4(), **categoria_in.model_dump())
    categoria_model = CategoriaModel(**categoria_out.model_dump())
    
    db_session.add(categoria_model)
    await db_session.commit()

    return categoria_out


@router.get(
    '/',
    summary='Consultar todas as Categorias',
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[CategoriaOut],
)
async def query(
    db_session: DatabaseDependency = Depends(),
    nome: str | None = Query(None),
    params: LimitOffsetParams = Depends(),
) -> LimitOffsetPage[CategoriaOut]:
    stmt = select(CategoriaModel)
    
    if nome:
        stmt = stmt.where(CategoriaModel.nome.ilike(f"%{nome}%"))
    
    async def _transform(items: Iterable):
        return [CategoriaOut.model_validate(c) for c in items]
    
    return await paginate(db_session, stmt, params=params, transformer=_transform)


@router.get(
    '/{id}',
    summary='Consulta uma Categoria pelo id',
    status_code=status.HTTP_200_OK,
    response_model=CategoriaOut,
)
async def get(id: UUID4, db_session: DatabaseDependency) -> CategoriaOut:
    categoria = (await db_session.execute(select(CategoriaModel).filter_by(id=id))).scalars().first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Categoria não encontrada no id: {id}',
        )
    
    return CategoriaOut.model_validate(categoria)