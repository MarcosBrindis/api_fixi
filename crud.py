from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import (
    Users, perfil, Cliente, Proveedor, Admin,Servicio,Solicitud,Historial,Pago,Calificacion,Chat,PerfilModel
)
from schemas import (
    UserCreateSchema, ClienteCreateSchema, ProveedorCreateSchema,
    AdminCreateSchema,ServicioCreateSchema,SolicitudCreate,HistorialCreate,PagoCreateSchema,PagoSchema,DireccionSchema,TarjetaSchema,
    CalificacionCreateSchema, ChatCreateSchema
)
from typing import List, Optional
from utils.security import hash_password 
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import joinedload,aliased
from database import mongo_db
from bson import ObjectId


#perfil

async def create_perfil(perfil_data: dict):
    result = await mongo_db.perfil.insert_one(perfil_data)
    return str(result.inserted_id)

# Obtener perfil por ID
async def get_perfil(perfil_id: str) -> dict:
    perfil = await mongo_db.perfil.find_one({"_id": ObjectId(perfil_id)})
    if perfil:
        perfil["_id"] = str(perfil["_id"])  # Convertir ObjectId a string
    return perfil

# Obtener todos los perfiles
async def get_all_perfiles():
    perfiles_cursor = mongo_db.perfil.find()
    perfiles = await perfiles_cursor.to_list(length=100)
    for perfil in perfiles:
        perfil["_id"] = str(perfil["_id"])
    return perfiles

# Actualizar un perfil
async def update_perfil(perfil_id: str, perfil_data: dict):
    result = await mongo_db.perfil.update_one(
        {"_id": ObjectId(perfil_id)},
        {"$set": perfil_data}
    )
    return result.modified_count > 0

# Eliminar un perfil
async def delete_perfil(perfil_id: str):
    result = await mongo_db.perfil.delete_one({"_id": ObjectId(perfil_id)})
    return result.deleted_count > 0

#-------------------------------------------------------------------------------

# CRUD for Users
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(Users).filter(Users.user_id == user_id))
    return result.scalars().first()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(Users).offset(skip).limit(limit))
    return result.scalars().all()

async def create_user(db: AsyncSession, user: UserCreateSchema):
    hashed_password = hash_password(user.password)  # Encripta la contraseña
    db_user = Users(
        name=user.name,
        email=user.email,
        password=hashed_password,  # Almacena la contraseña encriptada
        tipo_usuario=user.tipo_usuario,
        perfil_id=user.perfil_id,
        fechacreate=datetime.utcnow()
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_id: int, user_data: UserCreateSchema):
    db_user = await get_user(db, user_id)
    if db_user:
        for key, value in user_data.dict(exclude_unset=True).items():
            if key == "password":  # Si se actualiza la contraseña, encripta antes de asignar
                value = hash_password(value)
            setattr(db_user, key, value)
        
        db_user.fechacreate = datetime.utcnow()

        await db.commit()
        await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, user_id: int):
    db_user = await get_user(db, user_id)
    if db_user:
        await db.delete(db_user)
        await db.commit()
    return db_user

#------------------------------------------------------------------------------------------

async def get_servicio(db: AsyncSession, servicio_id: int):
    result = await db.execute(select(Servicio).filter(Servicio.servicio_id == servicio_id))
    return result.scalars().first()

async def get_servicios(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(Servicio).offset(skip).limit(limit))
    return result.scalars().all()

async def create_servicio(db: AsyncSession, servicio_data: ServicioCreateSchema, proveedor_id: int):
    # Agrega proveedor_id al modelo
    db_servicio = Servicio(**servicio_data.dict(), proveedor_id=proveedor_id)
    db.add(db_servicio)
    await db.commit()
    await db.refresh(db_servicio)
    return db_servicio


async def update_servicio(db: AsyncSession, servicio_id: int, servicio_data: ServicioCreateSchema):
    db_servicio = await get_servicio(db, servicio_id)
    if db_servicio:
        for key, value in servicio_data.dict(exclude_unset=True).items():
            setattr(db_servicio, key, value)
        await db.commit()
        await db.refresh(db_servicio)
    return db_servicio

async def delete_servicio(db: AsyncSession, servicio_id: int):
    db_servicio = await get_servicio(db, servicio_id)
    if db_servicio:
        await db.delete(db_servicio)
        await db.commit()
    return db_servicio

#------------------------------------------------------------------

# Crear Solicitud
async def create_solicitud(db: AsyncSession, solicitud: SolicitudCreate, current_user: dict):
    servicio = await get_servicio(db, solicitud.servicio_id)
    if not servicio:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    db_solicitud = Solicitud(
        hora=solicitud.hora,
        costo=servicio.costo, 
        cliente_id=current_user["user_id"], 
        servicio_id=solicitud.servicio_id,
        fecha_servicio=solicitud.fecha_servicio
    )
    db.add(db_solicitud)
    await db.commit()
    await db.refresh(db_solicitud)
    return db_solicitud

# Obtener una Solicitud por ID
async def get_solicitud(db: AsyncSession, solicitud_id: int, current_user: dict):
    # Consulta solicitud junto con servicio y proveedor
    result = await db.execute(
        select(Solicitud)
        .options(joinedload(Solicitud.servicio))
        .filter(Solicitud.solicitud_id == solicitud_id)
    )
    db_solicitud = result.scalars().first()

    if not db_solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Verifica si el usuario es cliente o proveedor autorizado
    if (db_solicitud.cliente_id != current_user["user_id"] and
        db_solicitud.servicio.proveedor_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="No tienes permiso para ver esta solicitud")
    
    return db_solicitud

# Obtener todas las Solicitudes
async def get_solicitudes(db: AsyncSession, current_user: dict, skip: int = 0, limit: int = 10):
    # Alias para el modelo Servicio
    ServicioAlias = aliased(Servicio)

    # Consulta inicial con join a Servicio
    query = select(Solicitud).join(Solicitud.servicio)

    # Filtra según el rol del usuario
    if current_user["tipo_usuario"] == "Cliente":
        query = query.filter(Solicitud.cliente_id == current_user["user_id"])
    elif current_user["tipo_usuario"] == "Proveedor":
        # Asegúrate de filtrar correctamente usando el alias
        query = query.filter(Solicitud.servicio.has(Servicio.proveedor_id == current_user["user_id"]))
    else:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver solicitudes")

    # Paginación y ejecución
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)

    return result.scalars().all()


# Actualizar el estado de una Solicitud
async def update_solicitud_status(db: AsyncSession, solicitud_id: int, status: str, current_user: dict):
    # Consultar la solicitud junto con el servicio
    result = await db.execute(
        select(Solicitud).options(joinedload(Solicitud.servicio)).filter(Solicitud.solicitud_id == solicitud_id)
    )
    db_solicitud = result.scalars().first()
    # Verificar que la solicitud exista
    if not db_solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    # Verificar que el usuario actual sea el proveedor del servicio
    if db_solicitud.servicio.proveedor_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar esta solicitud")
    # Actualizar el estado
    db_solicitud.status = status
    await db.commit()
    await db.refresh(db_solicitud)
    return db_solicitud


async def update_solicitud_cancelado(
    db: AsyncSession, 
    solicitud_id: int, 
    cancelado: bool, 
    current_user: dict
):
    # Consultar la solicitud con la relación al servicio
    result = await db.execute(
        select(Solicitud)
        .options(joinedload(Solicitud.servicio))
        .filter(Solicitud.solicitud_id == solicitud_id)
    )
    db_solicitud = result.scalars().first()
    # Verificar si la solicitud existe
    if not db_solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    # Verificar si el usuario actual tiene permiso para modificar la solicitud
    if (db_solicitud.cliente_id != current_user["user_id"] and 
        db_solicitud.servicio.proveedor_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta solicitud")
    # Realizar el borrado lógico
    db_solicitud.cancelado = cancelado
    await db.commit()
    await db.refresh(db_solicitud)
    return db_solicitud


# Eliminar Solicitud
async def delete_solicitud(db: AsyncSession, solicitud_id: int):
    result = await db.execute(select(Solicitud).filter(Solicitud.solicitud_id == solicitud_id))
    db_solicitud = result.scalars().first()
    if db_solicitud:
        await db.delete(db_solicitud)
        await db.commit()
    return db_solicitud


#----------------------------------------------------------------


async def create_historial(db: AsyncSession, historial: HistorialCreate):
    db_historial = Historial(**historial.dict())
    db.add(db_historial)
    await db.commit()
    await db.refresh(db_historial)
    return db_historial

async def get_historial(db: AsyncSession, historial_id: int):
    result = await db.execute(select(Historial).filter(Historial.historial_id == historial_id))
    return result.scalars().first()

async def get_historiales(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(Historial).offset(skip).limit(limit))
    return result.scalars().all()

async def update_historial(db: AsyncSession, historial_id: int, historial_data: HistorialCreate):
    db_historial = await get_historial(db, historial_id)
    if db_historial:
        for key, value in historial_data.dict(exclude_unset=True).items():
            setattr(db_historial, key, value)
        await db.commit()
        await db.refresh(db_historial)
    return db_historial

async def delete_historial(db: AsyncSession, historial_id: int):
    db_historial = await get_historial(db, historial_id)
    if db_historial:
        await db.delete(db_historial)
        await db.commit()
    return db_historial

#-----------------------------------------------------------------------

# Crear Pago
async def create_pago(db: AsyncSession, pago: PagoCreateSchema):
    # Convertir los campos de direccion y tarjeta desde el modelo Pydantic
    db_pago = Pago(
        monto=pago.monto,
        cliente_id=pago.cliente_id,
        solicitud_id=pago.solicitud_id,
        direccion=pago.direccion.dict(),  # Convertir el modelo Pydantic a dict
        tarjeta=pago.tarjeta.dict()  # Convertir el modelo Pydantic a dict
    )
    db.add(db_pago)
    await db.commit()
    await db.refresh(db_pago)
    # Convertir la entidad creada de nuevo a un esquema Pydantic
    return PagoSchema(
        pago_id=db_pago.pago_id,
        monto=db_pago.monto,
        cliente_id=db_pago.cliente_id,
        solicitud_id=db_pago.solicitud_id,
        direccion=DireccionSchema(**db_pago.direccion),
        tarjeta=TarjetaSchema(**db_pago.tarjeta)
    )


# Obtener Pago por ID
async def get_pago(db: AsyncSession, pago_id: int):
    result = await db.execute(select(Pago).filter(Pago.pago_id == pago_id))
    db_pago = result.scalars().first()
    if db_pago:
        # Convertir los campos JSON a objetos Pydantic
        return PagoSchema(
            pago_id=db_pago.pago_id,
            monto=db_pago.monto,
            cliente_id=db_pago.cliente_id,
            solicitud_id=db_pago.solicitud_id,
            direccion=DireccionSchema(**db_pago.direccion),  # Convertir a Pydantic
            tarjeta=TarjetaSchema(**db_pago.tarjeta)  # Convertir a Pydantic
        )
    return None


async def get_pagos(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(Pago).offset(skip).limit(limit))
    pagos = result.scalars().all()
    
    # Deserializar los campos JSON en instancias de Pydantic
    return [
        PagoSchema(
            pago_id=pago.pago_id,
            monto=pago.monto,
            cliente_id=pago.cliente_id,
            solicitud_id=pago.solicitud_id,
            direccion=DireccionSchema(**pago.direccion),  # Convertir el JSON a objeto Pydantic
            tarjeta=TarjetaSchema(**pago.tarjeta)  # Convertir el JSON a objeto Pydantic
        )
        for pago in pagos
    ]
    
    
async def update_pago(db: AsyncSession, pago_id: int, pago_data: PagoCreateSchema):
    result = await db.execute(select(Pago).filter(Pago.pago_id == pago_id))
    db_pago = result.scalars().first()
    
    if db_pago:
        # Actualizar los campos de la entidad de SQLAlchemy
        db_pago.monto = pago_data.monto
        db_pago.cliente_id = pago_data.cliente_id
        db_pago.solicitud_id = pago_data.solicitud_id
        db_pago.direccion = pago_data.direccion.dict()  # Convertir de Pydantic a dict
        db_pago.tarjeta = pago_data.tarjeta.dict()  # Convertir de Pydantic a dict
        
        await db.commit()
        await db.refresh(db_pago)
        
        # Convertir el modelo de SQLAlchemy de nuevo a un esquema Pydantic
        return PagoSchema(
            pago_id=db_pago.pago_id,
            monto=db_pago.monto,
            cliente_id=db_pago.cliente_id,
            solicitud_id=db_pago.solicitud_id,
            direccion=DireccionSchema(**db_pago.direccion),
            tarjeta=TarjetaSchema(**db_pago.tarjeta)
        )
    return None


async def delete_pago(db: AsyncSession, pago_id: int):
    # Cambiar para obtener el modelo SQLAlchemy, no el esquema Pydantic
    result = await db.execute(select(Pago).filter(Pago.pago_id == pago_id))
    db_pago = result.scalars().first()  # Aquí obtienes la instancia de SQLAlchemy
    
    if db_pago:
        await db.delete(db_pago)  # Eliminar el objeto del modelo SQLAlchemy
        await db.commit()  # Confirmar los cambios en la base de datos
    return db_pago


#------------------------------------------------------------------------------

# Obtener una calificación por ID
async def get_calificacion(db: AsyncSession, calificacion_id: int):
    result = await db.execute(select(Calificacion).filter(Calificacion.calificacion_id == calificacion_id))
    return result.scalars().first()

# Obtener todas las calificaciones con paginación
async def get_calificaciones(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(Calificacion).offset(skip).limit(limit))
    return result.scalars().all()

# Crear una nueva calificación
async def create_calificacion(db: AsyncSession, calificacion: CalificacionCreateSchema):
    db_calificacion = Calificacion(**calificacion.dict())
    db.add(db_calificacion)
    await db.commit()
    await db.refresh(db_calificacion)
    return db_calificacion

# Actualizar una calificación existente
async def update_calificacion(db: AsyncSession, calificacion_id: int, calificacion_data: CalificacionCreateSchema):
    db_calificacion = await get_calificacion(db, calificacion_id)
    if db_calificacion:
        for key, value in calificacion_data.dict(exclude_unset=True).items():
            setattr(db_calificacion, key, value)
        await db.commit()
        await db.refresh(db_calificacion)
    return db_calificacion

# Eliminar una calificación
async def delete_calificacion(db: AsyncSession, calificacion_id: int):
    db_calificacion = await get_calificacion(db, calificacion_id)
    if db_calificacion:
        await db.delete(db_calificacion)
        await db.commit()
    return db_calificacion


#-----------------------------------------------------------
async def get_chats(db: AsyncSession, skip: int = 0, limit: int = 10) -> List[Chat]:
    result = await db.execute(select(Chat).offset(skip).limit(limit))
    return result.scalars().all()

# Obtener un chat por su ID
async def get_chat(db: AsyncSession, chat_id: int) -> Optional[Chat]:
    result = await db.execute(select(Chat).filter(Chat.chat_id == chat_id))
    return result.scalars().first()

# Crear un nuevo chat
async def create_chat(db: AsyncSession, chat: ChatCreateSchema) -> Chat:
    db_chat = Chat(**chat.dict())
    db.add(db_chat)
    await db.commit()
    await db.refresh(db_chat)
    return db_chat

# Actualizar un chat existente
async def update_chat(db: AsyncSession, chat_id: int, chat_data: ChatCreateSchema) -> Optional[Chat]:
    db_chat = await get_chat(db, chat_id)
    if db_chat:
        for key, value in chat_data.dict(exclude_unset=True).items():
            setattr(db_chat, key, value)
        await db.commit()
        await db.refresh(db_chat)
    return db_chat

# Eliminar un chat
async def delete_chat(db: AsyncSession, chat_id: int) -> Optional[Chat]:
    db_chat = await get_chat(db, chat_id)
    if db_chat:
        await db.delete(db_chat)
        await db.commit()
    return db_chat

#-------------------------------------------------------------------------------------
