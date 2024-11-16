from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from database import get_db
from crud import get_servicio, get_servicios, create_servicio, update_servicio, delete_servicio
from schemas import ServicioSchema, ServicioCreateSchema,ServicioImageUploadSchema
from middlewares.auth import get_current_user
from fastapi.responses import StreamingResponse
import io
from fastapi import File, UploadFile


router = APIRouter()

@router.get("/{servicio_id}", response_model=ServicioSchema)
async def read_servicio(
    servicio_id: int, 
    current_user: dict = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    servicio = await get_servicio(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio not found")
    return servicio

@router.get("/", response_model=List[ServicioSchema])
async def read_servicios(
    skip: int = 0, 
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db:AsyncSession = Depends(get_db)):
    
    servicios = await get_servicios(db, skip=skip, limit=limit)
    if not servicios:
        raise HTTPException(status_code=404, detail="Servicio not found")
    return servicios

@router.post("/", response_model=ServicioSchema)
async def create_new_servicio(
    servicio: ServicioCreateSchema, 
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user["tipo_usuario"] != "Proveedor":
        raise HTTPException(status_code=403, detail="Only providers can create services")
    
    # Pasa proveedor_id al CRUD
    new_servicio = await create_servicio(db, servicio, proveedor_id=current_user["user_id"])
    return new_servicio


@router.put("/{servicio_id}", response_model=ServicioSchema)
async def update_existing_servicio(
    servicio_id: int, 
    servicio_data: ServicioCreateSchema, 
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    servicio = await get_servicio(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio not found")
    if servicio.proveedor_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only update your own services")
    updated_servicio = await update_servicio(db, servicio_id, servicio_data)
    return updated_servicio




@router.delete("/{servicio_id}")
async def delete_existing_servicio(
    servicio_id: int, 
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    servicio = await get_servicio(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio not found")
    
    if current_user["tipo_usuario"] != "Admin" and servicio.proveedor_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own services or must be an Admin")

    await delete_servicio(db, servicio_id)
    return {"message": "Servicio deleted successfully"}


@router.post("/{servicio_id}/upload-images")
async def upload_images(
    servicio_id: int,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    servicio = await get_servicio(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio not found")
    if servicio.proveedor_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only upload images to your own services")

    # Procesar las imágenes
    for file in files:
        content = await file.read()  # Leer los datos binarios de la imagen
        if not servicio.imagenes:
            servicio.imagenes = []
        servicio.imagenes.append(content)  # Guardar en el array de imágenes

    await db.commit()
    await db.refresh(servicio)

    return {"message": "Images uploaded successfully"}




@router.get("/{servicio_id}/images/{image_index}")
async def get_image(
    servicio_id: int,
    image_index: int,
    db: AsyncSession = Depends(get_db)
):
    servicio = await get_servicio(db, servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio not found")
    
    if not servicio.imagenes or len(servicio.imagenes) <= image_index:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Convertir la imagen binaria a un stream para enviarla
    image_data = servicio.imagenes[image_index]
    return StreamingResponse(io.BytesIO(image_data), media_type="image/jpeg")

