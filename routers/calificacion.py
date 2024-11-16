from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from crud import get_calificacion, get_calificaciones, create_calificacion, update_calificacion, delete_calificacion
from schemas import CalificacionSchema, CalificacionCreateSchema
from database import get_db
from typing import List

router = APIRouter()

@router.get("/{calificacion_id}", response_model=CalificacionSchema)
async def read_calificacion(calificacion_id: int, db: AsyncSession = Depends(get_db)):
    calificacion = await get_calificacion(db, calificacion_id)
    if not calificacion:
        raise HTTPException(status_code=404, detail="Calificación no encontrada")
    return calificacion

@router.get("/", response_model=List[CalificacionSchema])
async def read_calificaciones(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    calificaciones = await get_calificaciones(db, skip=skip, limit=limit)
    return calificaciones

@router.post("/", response_model=CalificacionSchema)
async def create_new_calificacion(calificacion: CalificacionCreateSchema, db: AsyncSession = Depends(get_db)):
    new_calificacion = await create_calificacion(db, calificacion)
    return new_calificacion

@router.put("/{calificacion_id}", response_model=CalificacionSchema)
async def update_existing_calificacion(calificacion_id: int, calificacion_data: CalificacionCreateSchema, db: AsyncSession = Depends(get_db)):
    updated_calificacion = await update_calificacion(db, calificacion_id, calificacion_data)
    return updated_calificacion

@router.delete("/{calificacion_id}")
async def delete_existing_calificacion(calificacion_id: int, db: AsyncSession = Depends(get_db)):
    await delete_calificacion(db, calificacion_id)
    return {"message": "Calificación eliminada exitosamente"}
