"""
Router principal de la API v1.

Agrupa todos los routers de modulos bajo /api/v1.
Para agregar un nuevo modulo, importar su router e incluirlo aqui.
"""
from fastapi import APIRouter

from app.api.v1.empresas.router import router as empresas_router
from app.api.v1.curp.router import router as curp_router

api_v1_router = APIRouter()

# Registrar routers de modulos
api_v1_router.include_router(empresas_router)
api_v1_router.include_router(curp_router)

# Para agregar nuevos modulos:
# from app.api.v1.empleados.router import router as empleados_router
# api_v1_router.include_router(empleados_router)
