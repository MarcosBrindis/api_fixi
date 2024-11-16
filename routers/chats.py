from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from schemas import ChatSchema, ChatCreateSchema
from crud import get_chats, get_chat, create_chat, update_chat, delete_chat
from database import get_db
from typing import List
router = APIRouter()

# Obtener todos los chats
@router.get("/", response_model=List[ChatSchema])
async def read_chats(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    chats = await get_chats(db, skip=skip, limit=limit)
    return chats

# Obtener un chat por ID
@router.get("/{chat_id}", response_model=ChatSchema)
async def read_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    chat = await get_chat(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

# Crear un nuevo chat
@router.post("/", response_model=ChatSchema)
async def create_new_chat(chat: ChatCreateSchema, db: AsyncSession = Depends(get_db)):
    new_chat = await create_chat(db, chat)
    return new_chat

# Actualizar un chat existente
@router.put("/{chat_id}", response_model=ChatSchema)
async def update_existing_chat(chat_id: int, chat_data: ChatCreateSchema, db: AsyncSession = Depends(get_db)):
    updated_chat = await update_chat(db, chat_id, chat_data)
    if not updated_chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return updated_chat

# Eliminar un chat
@router.delete("/{chat_id}")
async def delete_existing_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    deleted_chat = await delete_chat(db, chat_id)
    if not deleted_chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}
