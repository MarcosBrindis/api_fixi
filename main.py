from fastapi import FastAPI
from database import engine, Base
from routers import pagos, users, servicios, solicitudes, historial, calificacion, chats, auth
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración de CORS para permitir todos los orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=True,  # Permitir credenciales como cookies y cabeceras de autorización
    allow_methods=["*"],  # Permitir todos los métodos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permitir todas las cabeceras (incluyendo cabeceras personalizadas)
)

# Inicializar Base de Datos
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Incluir los Routers
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(servicios.router, prefix="/servicios", tags=["servicios"])
app.include_router(solicitudes.router, prefix="/solicitudes", tags=["solicitudes"])
app.include_router(historial.router, prefix="/historial", tags=["Historial"])
app.include_router(pagos.router, prefix="/pagos", tags=["Pagos"])
app.include_router(calificacion.router, prefix="/calificaciones", tags=["Calificaciones"])
app.include_router(chats.router, prefix="/chats", tags=["Chats"])
app.include_router(auth.router, prefix="/auth")