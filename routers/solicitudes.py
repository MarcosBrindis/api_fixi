from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas import Solicitud, SolicitudCreate
from crud import (
    create_solicitud, get_solicitud, get_solicitudes, 
    update_solicitud_status, delete_solicitud
)

router = APIRouter()

@router.post("/", response_model=Solicitud)
async def crear_solicitud(solicitud: SolicitudCreate, db: AsyncSession = Depends(get_db)):
    return await create_solicitud(db, solicitud)

@router.get("/{solicitud_id}", response_model=Solicitud)
async def obtener_solicitud(solicitud_id: int, db: AsyncSession = Depends(get_db)):
    db_solicitud = await get_solicitud(db, solicitud_id)
    if db_solicitud is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return db_solicitud

@router.get("/", response_model=list[Solicitud])
async def obtener_solicitudes(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    return await get_solicitudes(db, skip=skip, limit=limit)

@router.put("/{solicitud_id}/status", response_model=Solicitud)
async def actualizar_status_solicitud(solicitud_id: int, status: str, db: AsyncSession = Depends(get_db)):
    db_solicitud = await update_solicitud_status(db, solicitud_id, status)
    if db_solicitud is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return db_solicitud

@router.delete("/{solicitud_id}", response_model=Solicitud)
async def eliminar_solicitud(solicitud_id: int, db: AsyncSession = Depends(get_db)):
    db_solicitud = await delete_solicitud(db, solicitud_id)
    if db_solicitud is None:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return db_solicitud
