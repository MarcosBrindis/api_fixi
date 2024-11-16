from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database import get_db
from schemas import Historial, HistorialCreate
from crud import create_historial, get_historial, get_historiales, update_historial, delete_historial

router = APIRouter()

@router.post("/", response_model=Historial, status_code=status.HTTP_201_CREATED)
async def create_historial_endpoint(historial: HistorialCreate, db: AsyncSession = Depends(get_db)):
    return await create_historial(db, historial)

@router.get("/{historial_id}", response_model=Historial)
async def read_historial(historial_id: int, db: AsyncSession = Depends(get_db)):
    db_historial = await get_historial(db, historial_id)
    if not db_historial:
        raise HTTPException(status_code=404, detail="Historial not found")
    return db_historial

@router.get("/", response_model=List[Historial])
async def read_historiales(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    return await get_historiales(db, skip=skip, limit=limit)

@router.put("/{historial_id}", response_model=Historial)
async def update_historial_endpoint(historial_id: int, historial_data: HistorialCreate, db: AsyncSession = Depends(get_db)):
    db_historial = await update_historial(db, historial_id, historial_data)
    if not db_historial:
        raise HTTPException(status_code=404, detail="Historial not found")
    return db_historial

@router.delete("/{historial_id}", response_model=Historial)
async def delete_historial_endpoint(historial_id: int, db: AsyncSession = Depends(get_db)):
    db_historial = await delete_historial(db, historial_id)
    if not db_historial:
        raise HTTPException(status_code=404, detail="Historial not found")
    return db_historial