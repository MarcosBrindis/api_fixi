from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import Users
from schemas import UserSchema, UserCreateSchema
from typing import List  
from crud import get_user, get_users, create_user, update_user, delete_user
from sqlalchemy.exc import SQLAlchemyError
from middlewares.auth import get_current_user


router = APIRouter()

@router.get("/{user_id}", response_model=UserSchema)
async def read_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user["user_id"] != user_id and current_user["tipo_usuario"] != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this user data")
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/", response_model=List[UserSchema])
async def read_users(
    skip: int = 0,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user["tipo_usuario"] != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    users = await get_users(db, skip=skip, limit=limit)
    return users



@router.post("/", response_model=UserSchema)
async def create_new_user(user: UserCreateSchema, db: AsyncSession = Depends(get_db)):
    try:
        user = await create_user(db, user)
        return user  # Asegúrate de que este objeto coincida con UserSchema
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {str(e)}")


@router.put("/{user_id}", response_model=UserSchema)
async def update_existing_user(
    user_id: int,
    user_data: UserCreateSchema,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    updated_user = await update_user(db, user_id, user_data)
    return updated_user


@router.delete("/{user_id}")
async def delete_existing_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user["tipo_usuario"] != "Admin" and current_user["user_id"] != user_id :
        raise HTTPException(status_code=403, detail="Not authorized to delete users")
    await delete_user(db, user_id)
    return {"message": "User deleted successfully"}

