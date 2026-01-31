"""
Endpoints REST del modulo Empresas.

Todos los endpoints llaman a empresa_service (singleton).
No duplican logica de negocio.
"""
import logging

from fastapi import APIRouter, Query

from app.services import empresa_service
from app.api.v1.schemas import APIListResponse, APIResponse
from app.api.v1.empresas.schemas import EmpresaResponse
from app.core.exceptions import NotFoundError, DatabaseError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/empresas", tags=["Empresas"])


@router.get(
    "",
    response_model=APIListResponse[EmpresaResponse],
    summary="Listar empresas",
    description="Obtiene la lista de empresas con filtros opcionales.",
)
async def listar_empresas(
    incluir_inactivas: bool = Query(False, description="Incluir empresas inactivas"),
    busqueda: str = Query("", description="Buscar por nombre o razon social (min 2 chars)"),
):
    """
    Obtiene empresas del sistema.

    - Sin parametros: devuelve empresas activas
    - Con busqueda: filtra por nombre comercial o razon social
    - Con incluir_inactivas=true: incluye todas
    """
    try:
        if busqueda and len(busqueda) >= 2:
            empresas = await empresa_service.buscar_por_nombre(busqueda, limite=50)
        else:
            empresas = await empresa_service.obtener_todas(
                incluir_inactivas=incluir_inactivas,
                limite=100,
            )

        data = [
            EmpresaResponse.model_validate(e.model_dump())
            for e in empresas
        ]

        return APIListResponse(
            success=True,
            data=data,
            total=len(data),
        )

    except DatabaseError as e:
        logger.error(f"Error de BD listando empresas: {e}")
        return APIListResponse(
            success=False,
            message=f"Error de base de datos: {e}",
        )
    except Exception as e:
        logger.error(f"Error inesperado listando empresas: {e}")
        return APIListResponse(
            success=False,
            message="Error interno del servidor",
        )


@router.get(
    "/{empresa_id}",
    response_model=APIResponse[EmpresaResponse],
    summary="Obtener empresa por ID",
    description="Obtiene los detalles de una empresa especifica.",
)
async def obtener_empresa(empresa_id: int):
    """Obtiene una empresa por su ID."""
    try:
        empresa = await empresa_service.obtener_por_id(empresa_id)

        return APIResponse(
            success=True,
            data=EmpresaResponse.model_validate(empresa.model_dump()),
            total=1,
        )

    except NotFoundError:
        return APIResponse(
            success=False,
            message=f"Empresa con ID {empresa_id} no encontrada",
        )
    except DatabaseError as e:
        logger.error(f"Error de BD obteniendo empresa {empresa_id}: {e}")
        return APIResponse(
            success=False,
            message=f"Error de base de datos: {e}",
        )
    except Exception as e:
        logger.error(f"Error inesperado obteniendo empresa {empresa_id}: {e}")
        return APIResponse(
            success=False,
            message="Error interno del servidor",
        )
