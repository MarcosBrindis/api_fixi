from fastapi import APIRouter, HTTPException,Form
from schemas import PerfilSchema
from crud import create_perfil, get_perfil, get_all_perfiles, update_perfil, delete_perfil,create_perfil_with_image,get_perfil_with_image
from typing import List
from fastapi import File, UploadFile
router = APIRouter()
import json
# Crear perfil


@router.post("/", response_model=dict)
async def create(
    description: str = Form(...),
    habilidades: str = Form(default="[]"),  # Recibe como cadena JSON
    telefono: str = Form(None),
    direccion: str = Form(default="{}"),  # Recibe como cadena JSON
    foto: UploadFile = File(None)
):

    # Parsear habilidades y dirección
    habilidades = json.loads(habilidades)
    direccion = json.loads(direccion)

    # Leer la imagen
    image_data = await foto.read() if foto else None

    # Crear perfil
    perfil_data = {
        "description": description,
        "habilidades": habilidades,
        "telefono": telefono,
        "direccion": direccion,
    }
    perfil_id = await create_perfil_with_image(perfil_data, image_data)
    return {"id": perfil_id}

@router.get("/{perfil_id}", response_model=dict)
async def read_one(perfil_id: str):
    perfil = await get_perfil_with_image(perfil_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return perfil


# Obtener todos los perfiles
@router.get("/", response_model=List[dict])
async def read_all():
    return await get_all_perfiles()


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
