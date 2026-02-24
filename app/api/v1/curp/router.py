"""
Endpoints REST del modulo CURP.

Validacion de CURP: formato + duplicados en el sistema.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Query

from app.services.curp_service import curp_service
from app.api.v1.common import ok, raise_http_from_exc
from app.api.v1.schemas import APIResponse
from app.api.v1.curp.schemas import CurpValidacionSchema

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/curp", tags=["CURP"])


@router.get(
    "/validar/{curp}",
    response_model=APIResponse[CurpValidacionSchema],
    summary="Validar CURP",
    description="Valida formato de CURP y verifica si ya existe en el sistema.",
)
async def validar_curp(
    curp: str,
    excluir_empleado_id: Optional[int] = Query(
        None,
        description="ID de empleado a excluir de busqueda de duplicados"
    ),
):
    """
    Valida un CURP.

    - Verifica formato (18 caracteres, patron oficial)
    - Busca duplicados en la base de datos
    - Informa si el empleado encontrado esta restringido
    """
    try:
        resultado = await curp_service.validar_curp(
            curp=curp,
            excluir_empleado_id=excluir_empleado_id,
        )

        return ok(CurpValidacionSchema.model_validate(resultado.model_dump()))

    except Exception as e:
        raise_http_from_exc(e, logger, f"validando CURP {curp}")
