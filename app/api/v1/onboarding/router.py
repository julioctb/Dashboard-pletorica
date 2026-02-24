"""
Endpoints REST del modulo Onboarding.

Alta de empleados, gestion de expedientes y documentos.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, UploadFile, File, Form

from app.api.v1.schemas import APIResponse, APIListResponse
from app.api.v1.onboarding.schemas import (
    AltaEmpleadoRequest,
    EmpleadoOnboardingResponse,
    ExpedienteStatusResponse,
    DocumentoResponse,
    RechazoDocumentoRequest,
)
from app.services.onboarding_service import onboarding_service
from app.services.empleado_documento_service import empleado_documento_service
from app.entities.onboarding import AltaEmpleadoBuap
from app.entities.empleado_documento import EmpleadoDocumentoCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])


@router.post(
    "/alta",
    response_model=APIResponse[EmpleadoOnboardingResponse],
    summary="Registrar empleado",
    description="Da de alta un nuevo empleado en el proceso de onboarding.",
)
async def alta_empleado(request: AltaEmpleadoRequest):
    """Registra un nuevo empleado desde RRHH."""
    try:
        datos = AltaEmpleadoBuap(
            empresa_id=request.empresa_id,
            curp=request.curp,
            nombre=request.nombre,
            apellido_paterno=request.apellido_paterno,
            apellido_materno=request.apellido_materno,
            email=request.email,
            sede_id=request.sede_id,
        )

        # TODO: obtener UUID del token JWT cuando auth este implementado
        registrado_por = UUID('00000000-0000-0000-0000-000000000000')

        empleado = await onboarding_service.alta_empleado_buap(datos, registrado_por)

        nombre_completo = f"{empleado.nombre} {empleado.apellido_paterno}".strip()
        if empleado.apellido_materno:
            nombre_completo += f" {empleado.apellido_materno}"

        return APIResponse(
            success=True,
            data=EmpleadoOnboardingResponse(
                id=empleado.id,
                clave=empleado.clave,
                curp=empleado.curp,
                nombre_completo=nombre_completo,
                estatus_onboarding=empleado.estatus_onboarding,
                email=empleado.email,
                fecha_creacion=empleado.fecha_creacion,
            ),
            total=1,
        )
    except Exception as e:
        logger.error(f"Error en alta de empleado: {e}")
        return APIResponse(
            success=False,
            message=str(e),
        )


@router.get(
    "/expediente/{empleado_id}",
    response_model=APIResponse[ExpedienteStatusResponse],
    summary="Estado del expediente",
    description="Obtiene el estado del expediente documental de un empleado.",
)
async def obtener_expediente(empleado_id: int):
    """Obtiene estado del expediente documental."""
    try:
        expediente = await onboarding_service.obtener_expediente(empleado_id)

        return APIResponse(
            success=True,
            data=ExpedienteStatusResponse(
                documentos_requeridos=expediente.documentos_requeridos,
                documentos_subidos=expediente.documentos_subidos,
                documentos_aprobados=expediente.documentos_aprobados,
                documentos_rechazados=expediente.documentos_rechazados,
                porcentaje_completado=expediente.porcentaje_completado,
                esta_completo=expediente.esta_completo,
                tiene_rechazados=expediente.tiene_rechazados,
            ),
            total=1,
        )
    except Exception as e:
        logger.error(f"Error obteniendo expediente empleado {empleado_id}: {e}")
        return APIResponse(
            success=False,
            message=str(e),
        )


@router.post(
    "/documentos",
    response_model=APIResponse[DocumentoResponse],
    summary="Subir documento",
    description="Sube un documento al expediente de un empleado.",
)
async def subir_documento(
    file: UploadFile = File(...),
    empleado_id: int = Form(...),
    tipo_documento: str = Form(...),
):
    """Sube un documento al expediente."""
    try:
        contenido = await file.read()

        datos = EmpleadoDocumentoCreate(
            empleado_id=empleado_id,
            tipo_documento=tipo_documento,
        )

        documento = await empleado_documento_service.subir_documento(
            datos=datos,
            contenido=contenido,
            nombre_archivo=file.filename or "documento",
            tipo_mime=file.content_type or "application/octet-stream",
        )

        return APIResponse(
            success=True,
            data=DocumentoResponse(
                id=documento.id,
                tipo_documento=documento.tipo_documento,
                nombre_archivo=documento.nombre_archivo,
                estatus=documento.estatus,
                version=documento.version,
                fecha_creacion=documento.fecha_creacion,
            ),
            total=1,
        )
    except Exception as e:
        logger.error(f"Error subiendo documento: {e}")
        return APIResponse(
            success=False,
            message=str(e),
        )


@router.put(
    "/documentos/{documento_id}/aprobar",
    response_model=APIResponse[DocumentoResponse],
    summary="Aprobar documento",
    description="Aprueba un documento pendiente de revision.",
)
async def aprobar_documento(documento_id: int):
    """Aprueba un documento."""
    try:
        # TODO: obtener UUID del token JWT cuando auth este implementado
        revisado_por = UUID('00000000-0000-0000-0000-000000000000')

        documento = await empleado_documento_service.aprobar_documento(
            documento_id=documento_id,
            revisado_por=revisado_por,
        )

        return APIResponse(
            success=True,
            data=DocumentoResponse(
                id=documento.id,
                tipo_documento=documento.tipo_documento,
                nombre_archivo=documento.nombre_archivo,
                estatus=documento.estatus,
                version=documento.version,
                fecha_creacion=documento.fecha_creacion,
                fecha_revision=documento.fecha_revision,
            ),
            total=1,
        )
    except Exception as e:
        logger.error(f"Error aprobando documento {documento_id}: {e}")
        return APIResponse(
            success=False,
            message=str(e),
        )


@router.put(
    "/documentos/{documento_id}/rechazar",
    response_model=APIResponse[DocumentoResponse],
    summary="Rechazar documento",
    description="Rechaza un documento pendiente de revision con observacion.",
)
async def rechazar_documento(documento_id: int, request: RechazoDocumentoRequest):
    """Rechaza un documento con observacion."""
    try:
        # TODO: obtener UUID del token JWT cuando auth este implementado
        revisado_por = UUID('00000000-0000-0000-0000-000000000000')

        documento = await empleado_documento_service.rechazar_documento(
            documento_id=documento_id,
            revisado_por=revisado_por,
            observacion=request.observacion,
        )

        return APIResponse(
            success=True,
            data=DocumentoResponse(
                id=documento.id,
                tipo_documento=documento.tipo_documento,
                nombre_archivo=documento.nombre_archivo,
                estatus=documento.estatus,
                observacion_rechazo=documento.observacion_rechazo,
                version=documento.version,
                fecha_creacion=documento.fecha_creacion,
                fecha_revision=documento.fecha_revision,
            ),
            total=1,
        )
    except Exception as e:
        logger.error(f"Error rechazando documento {documento_id}: {e}")
        return APIResponse(
            success=False,
            message=str(e),
        )
