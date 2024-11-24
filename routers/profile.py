from fastapi import APIRouter, HTTPException,Form,Depends
from schemas import PerfilSchema
from crud import  get_all_perfiles, update_perfil_in_db, delete_perfil,create_perfil_with_image,get_perfil_with_image,get_user,assign_perfil_to_user
from typing import List
from fastapi import File, UploadFile
router = APIRouter()
import json
from middlewares.auth import get_current_user
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image
from io import BytesIO
from bson import ObjectId

# Crear perfil


@router.post("/", response_model=dict)
async def create(
    description: str = Form(...),
    habilidades: str = Form(default="[]"),
    telefono: str = Form(None),
    direccion: str = Form(default="{}"),
    foto: UploadFile = File(None),
    imagenes: List[UploadFile] = File([]),
    current_user: dict = Depends(get_current_user),  # Obtener usuario logueado
    db: AsyncSession = Depends(get_db)  # Sesión de base de datos
):
    user_id = current_user["user_id"]  # Obtener ID del usuario desde el token
    # Obtener usuario desde la base de datos
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.perfil_id:
        raise HTTPException(
            status_code=400, detail="El usuario ya tiene un perfil asociado"
        )
    # Parsear habilidades y dirección
    try:
        habilidades = json.loads(habilidades)
        direccion = json.loads(direccion)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Habilidades o dirección no tienen el formato JSON correcto")

    # Leer la imagen si se proporcionó
    images_data = [await img.read() for img in imagenes] if imagenes else []
    image_data = await foto.read() if foto else None
    if image_data:
        try:
            Image.open(BytesIO(image_data))  # Verifica si es una imagen válida
        except Exception:
            raise HTTPException(status_code=400, detail="El archivo no es una imagen válida")
    # Crear perfil en MongoDB
    perfil_data = {
        "description": description,
        "habilidades": habilidades,
        "telefono": telefono,
        "direccion": direccion,
    }
    try:
        perfil_id = await create_perfil_with_image(perfil_data, image_data,images_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el perfil: {str(e)}")
    # Asociar perfil al usuario en PostgreSQL
    try:
        await assign_perfil_to_user(db, user_id, perfil_id)
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Error al asociar el perfil al usuario: {str(e)}")
    return {"id": perfil_id}
      
        
        
        
        
# Obtener perfil por ID, solo el usuario logueado o un admin puede acceder
@router.get("/{perfil_id}", response_model=dict)
async def read_one(
    perfil_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validar ID de perfil
    if not ObjectId.is_valid(perfil_id):
        raise HTTPException(status_code=400, detail="ID de perfil no válido")
    # Obtener el perfil desde MongoDB
    perfil = await get_perfil_with_image(perfil_id)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    # Obtener usuario logueado
    user_id = current_user.get("user_id")
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    # Verificar permisos
    user_perfil_id = user.perfil_id if hasattr(user, 'perfil_id') else None
    if not user_perfil_id or (str(perfil["_id"]) != user_perfil_id and user.tipo_usuario != "Admin"):
        raise HTTPException(status_code=403, detail="No autorizado para ver este perfil")
    return perfil



@router.put("/", response_model=bool)
async def update_perfil(
    perfil_id: str = Form(...),
    description: str = Form(None),
    habilidades: str = Form(default="[]"),
    telefono: str = Form(None),
    direccion: str = Form(default="{}"),
    foto: UploadFile = File(None),  # Debe ser UploadFile
    imagenes: List[UploadFile] = File([]),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # Obtener usuario logueado
):  
    print(f"Decoded Token: {get_current_user}")
    # Validar que el perfil_id corresponde al usuario logueado o que el usuario es admin
    if perfil_id != str(current_user["perfil_id"]):
        raise HTTPException(status_code=403, detail="No autorizado para actualizar este perfil")
    # Validar habilidades y dirección como JSON
    try:
        habilidades = json.loads(habilidades) if habilidades else []
        direccion = json.loads(direccion) if direccion else {}
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Habilidades o dirección no tienen el formato JSON correcto"
        )
    # Leer la imagen si se proporciona
    new_images = [await img.read() for img in imagenes] if imagenes else []
    image_data = None
    if foto:
        try:
            image_data = await foto.read()
            Image.open(BytesIO(image_data))  # Verificar si es una imagen válida
        except Exception:
            raise HTTPException(
                status_code=400, detail="El archivo no es una imagen válida"
            )
    # Preparar datos para actualizar el perfil
    perfil_data = {
        "description": description,
        "habilidades": habilidades,
        "telefono": telefono,
        "direccion": direccion,
    }
    if image_data:
        perfil_data["foto"] = image_data  # Agregar la imagen binaria
    
    # Filtrar claves nulas
    perfil_data = {k: v for k, v in perfil_data.items() if v is not None}
    # Actualizar el perfil en MongoDB
    updated = await update_perfil_in_db(perfil_id, perfil_data, new_images)
    if not updated:
        raise HTTPException(status_code=500, detail="Error al actualizar el perfil")
    return updated



# Obtener todos los perfiles
@router.get("/", response_model=List[dict])
async def read_all():
    return await get_all_perfiles()


# Eliminar perfil
@router.delete("/{perfil_id}", response_model=bool)
async def delete(
    perfil_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user) 
    ):
     # Validar que el perfil_id corresponde al usuario logueado o que el usuario es admin
    if perfil_id != str(current_user["perfil_id"]):
        raise HTTPException(status_code=403, detail="No autorizado para actualizar este perfil")
    
    deleted = await delete_perfil(perfil_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")
    return deleted