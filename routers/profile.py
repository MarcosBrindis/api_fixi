from fastapi import APIRouter, HTTPException
from schemas import PerfilSchema
from crud import create_perfil, get_perfil, get_all_perfiles, update_perfil, delete_perfil
from typing import List

router = APIRouter()

# Crear perfil
@router.post("/", response_model=dict)
async def create(data: PerfilSchema):
    perfil_data = data.dict(exclude_unset=True)
    perfil_id = await create_perfil(perfil_data)
    return {"id": perfil_id}

# Obtener todos los perfiles
@router.get("/", response_model=List[dict])
async def read_all():
    return await get_all_perfiles()

# Obtener un perfil por ID
@router.get("/{perfil_id}", response_model=dict)
async def read_one(perfil_id: str):
    perfil = await get_perfil(perfil_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return perfil

# Actualizar perfil
@router.put("/{perfil_id}", response_model=bool)
async def update(perfil_id: str, data: PerfilSchema):
    perfil_data = data.dict(exclude_unset=True)
    updated = await update_perfil(perfil_id, perfil_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return updated

# Eliminar perfil
@router.delete("/{perfil_id}", response_model=bool)
async def delete(perfil_id: str):
    deleted = await delete_perfil(perfil_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return deleted
