from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#configuracion mongo
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from motor.motor_asyncio import AsyncIOMotorClient 

# Configuración de MongoDB
uri = "mongodb+srv://233305:12345678a@proymultidiciplinario.04jiu.mongodb.net/?retryWrites=true&w=majority&appName=proymultidiciplinario"
client = AsyncIOMotorClient(uri)
mongo_db =client.proymultidiciplinario
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
    
#base de datos postgresql
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
