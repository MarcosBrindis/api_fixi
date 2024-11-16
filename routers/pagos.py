from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas import PagoSchema, PagoCreateSchema
from crud import create_pago, get_pago, get_pagos, update_pago, delete_pago
from typing import List
router = APIRouter()

@router.post("/", response_model=PagoSchema)
async def create_new_pago(pago: PagoCreateSchema, db: AsyncSession = Depends(get_db)):
    return await create_pago(db, pago)

@router.get("/{pago_id}", response_model=PagoSchema)
async def read_pago(pago_id: int, db: AsyncSession = Depends(get_db)):
    db_pago = await get_pago(db, pago_id)
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago not found")
    return db_pago

@router.get("/", response_model=List[PagoSchema])
async def read_pagos(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    return await get_pagos(db, skip=skip, limit=limit)

@router.put("/{pago_id}", response_model=PagoSchema)
async def update_existing_pago(pago_id: int, pago_data: PagoCreateSchema, db: AsyncSession = Depends(get_db)):
    db_pago = await update_pago(db, pago_id, pago_data)
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago not found")
    return db_pago

@router.delete("/{pago_id}", response_model=PagoSchema)
async def delete_existing_pago(pago_id: int, db: AsyncSession = Depends(get_db)):
    db_pago = await delete_pago(db, pago_id)
    if not db_pago:
        raise HTTPException(status_code=404, detail="Pago not found")
    return db_pago
