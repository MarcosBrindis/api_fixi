from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "postgresql+asyncpg://postgres@localhost:5432/fixi"

# Crear el motor de base de datos asíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Crear una clase base para la declaración de modelos
Base = declarative_base()

# Crear una sesión de base de datos
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Función para obtener una sesión de base de datos
async def get_db():
    async with SessionLocal() as session:
        yield session
