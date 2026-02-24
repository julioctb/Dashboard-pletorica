"""
Servicio para gestion de documentos del expediente de empleados.

Patron Direct Access. Usa archivo_service para subir archivos fisicos.
Soporta versionamiento (un documento vigente por tipo por empleado)
y flujo de validacion (PENDIENTE_REVISION -> APROBADO / RECHAZADO).
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from app.database import db_manager
from app.core.exceptions import (
    DatabaseError,
    NotFoundError,
    BusinessRuleError,
    ValidationError,
)
from app.core.enums import EstatusDocumento, TipoDocumentoEmpleado
from app.entities.empleado_documento import (
    EmpleadoDocumento,
    EmpleadoDocumentoCreate,
    EmpleadoDocumentoResumen,
)
from app.entities.archivo import EntidadArchivo, TipoArchivo

logger = logging.getLogger(__name__)


class EmpleadoDocumentoService:
    """Servicio de documentos del expediente de empleados."""

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'empleado_documentos'

    async def subir_documento(
        self,
        datos: EmpleadoDocumentoCreate,
        contenido: bytes,
        nombre_archivo: str,
        tipo_mime: str,
    ) -> EmpleadoDocumento:
        """
        Sube un documento al expediente del empleado.

        1. Sube archivo fisico via archivo_service
        2. Marca version anterior como no vigente
        3. Calcula nueva version
        4. Inserta registro con archivo_id, version, es_vigente=True

        Returns:
            EmpleadoDocumento creado.

        Raises:
            DatabaseError: Si hay error de BD/Storage.
        """
        from app.services.archivo_service import archivo_service

        try:
            # 1. Subir archivo fisico
            archivo_resp = await archivo_service.subir_archivo(
                contenido=contenido,
                nombre_original=nombre_archivo,
                tipo_mime=tipo_mime,
                entidad_tipo=EntidadArchivo.EMPLEADO,
                entidad_id=datos.empleado_id,
                identificador_ruta=f"documentos/{datos.tipo_documento}",
                tipo_archivo=TipoArchivo.DOCUMENTO,
                descripcion=f"Documento {datos.tipo_documento} del empleado",
            )

            # 2. Marcar versiones anteriores como no vigentes
            self.supabase.table(self.tabla).update(
                {'es_vigente': False}
            ).eq(
                'empleado_id', datos.empleado_id
            ).eq(
                'tipo_documento', datos.tipo_documento
            ).eq(
                'es_vigente', True
            ).execute()

            # 3. Calcular nueva version
            version_result = (
                self.supabase.table(self.tabla)
                .select('version')
                .eq('empleado_id', datos.empleado_id)
                .eq('tipo_documento', datos.tipo_documento)
                .order('version', desc=True)
                .limit(1)
                .execute()
            )
            nueva_version = 1
            if version_result.data:
                nueva_version = version_result.data[0]['version'] + 1

            # 4. Insertar nuevo documento
            payload = {
                'empleado_id': datos.empleado_id,
                'tipo_documento': datos.tipo_documento,
                'archivo_id': archivo_resp.archivo_id,
                'nombre_archivo': nombre_archivo,
                'estatus': EstatusDocumento.PENDIENTE_REVISION.value,
                'version': nueva_version,
                'es_vigente': True,
                'subido_por': str(datos.subido_por) if datos.subido_por else None,
            }
            result = self.supabase.table(self.tabla).insert(payload).execute()

            if not result.data:
                raise DatabaseError("No se pudo registrar el documento")

            return EmpleadoDocumento(**result.data[0])

        except (DatabaseError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error subiendo documento: {e}")
            raise DatabaseError(f"Error subiendo documento: {e}")

    async def obtener_documentos_empleado(
        self, empleado_id: int, solo_vigentes: bool = True
    ) -> List[EmpleadoDocumentoResumen]:
        """
        Obtiene los documentos del expediente de un empleado.

        Args:
            empleado_id: ID del empleado.
            solo_vigentes: Si True, solo retorna documentos vigentes.

        Returns:
            Lista de documentos resumidos.
        """
        try:
            query = (
                self.supabase.table(self.tabla)
                .select('*')
                .eq('empleado_id', empleado_id)
                .order('tipo_documento')
                .order('version', desc=True)
            )

            if solo_vigentes:
                query = query.eq('es_vigente', True)

            result = query.execute()

            return [EmpleadoDocumentoResumen(**r) for r in (result.data or [])]

        except Exception as e:
            logger.error(f"Error obteniendo documentos empleado {empleado_id}: {e}")
            raise DatabaseError(f"Error obteniendo documentos: {e}")

    async def obtener_por_id(self, documento_id: int) -> EmpleadoDocumento:
        """
        Obtiene un documento por su ID.

        Raises:
            NotFoundError: Si no existe.
            DatabaseError: Si hay error de BD.
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .select('*')
                .eq('id', documento_id)
                .execute()
            )

            if not result.data:
                raise NotFoundError(f"Documento con ID {documento_id} no encontrado")

            return EmpleadoDocumento(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo documento {documento_id}: {e}")
            raise DatabaseError(f"Error obteniendo documento: {e}")

    async def aprobar_documento(
        self, documento_id: int, revisado_por: UUID
    ) -> EmpleadoDocumento:
        """
        Aprueba un documento pendiente de revision.

        Raises:
            NotFoundError: Si no existe.
            BusinessRuleError: Si no esta en PENDIENTE_REVISION.
        """
        documento = await self.obtener_por_id(documento_id)

        if documento.estatus != EstatusDocumento.PENDIENTE_REVISION.value:
            raise BusinessRuleError(
                f"Solo se pueden aprobar documentos en revision "
                f"(estatus actual: {documento.estatus})"
            )

        try:
            result = (
                self.supabase.table(self.tabla)
                .update({
                    'estatus': EstatusDocumento.APROBADO.value,
                    'revisado_por': str(revisado_por),
                    'fecha_revision': datetime.now().isoformat(),
                    'observacion_rechazo': None,
                })
                .eq('id', documento_id)
                .execute()
            )

            if not result.data:
                raise DatabaseError("No se pudo aprobar el documento")

            return EmpleadoDocumento(**result.data[0])

        except (DatabaseError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error aprobando documento {documento_id}: {e}")
            raise DatabaseError(f"Error aprobando documento: {e}")

    async def rechazar_documento(
        self, documento_id: int, revisado_por: UUID, observacion: str
    ) -> EmpleadoDocumento:
        """
        Rechaza un documento pendiente de revision.

        Args:
            documento_id: ID del documento.
            revisado_por: UUID del revisor.
            observacion: Motivo del rechazo (min 5 caracteres).

        Raises:
            NotFoundError: Si no existe.
            BusinessRuleError: Si no esta en PENDIENTE_REVISION.
            ValidationError: Si la observacion esta vacia o muy corta.
        """
        if not observacion or len(observacion.strip()) < 5:
            raise ValidationError("La observacion de rechazo debe tener al menos 5 caracteres")

        documento = await self.obtener_por_id(documento_id)

        if documento.estatus != EstatusDocumento.PENDIENTE_REVISION.value:
            raise BusinessRuleError(
                f"Solo se pueden rechazar documentos en revision "
                f"(estatus actual: {documento.estatus})"
            )

        try:
            result = (
                self.supabase.table(self.tabla)
                .update({
                    'estatus': EstatusDocumento.RECHAZADO.value,
                    'revisado_por': str(revisado_por),
                    'fecha_revision': datetime.now().isoformat(),
                    'observacion_rechazo': observacion.strip(),
                })
                .eq('id', documento_id)
                .execute()
            )

            if not result.data:
                raise DatabaseError("No se pudo rechazar el documento")

            return EmpleadoDocumento(**result.data[0])

        except (DatabaseError, BusinessRuleError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error rechazando documento {documento_id}: {e}")
            raise DatabaseError(f"Error rechazando documento: {e}")

    async def obtener_documentos_pendientes(
        self, empresa_id: int
    ) -> List[EmpleadoDocumentoResumen]:
        """
        Obtiene documentos pendientes de revision para una empresa.

        Hace JOIN con empleados para filtrar por empresa_id.

        Returns:
            Lista de documentos pendientes con datos del empleado.
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .select(
                    '*, empleados!inner(id, nombre, apellido_paterno, '
                    'apellido_materno, empresa_id)'
                )
                .eq('empleados.empresa_id', empresa_id)
                .eq('estatus', EstatusDocumento.PENDIENTE_REVISION.value)
                .eq('es_vigente', True)
                .order('fecha_creacion', desc=True)
                .execute()
            )

            documentos = []
            for r in (result.data or []):
                emp = r.pop('empleados', {})
                nombre_completo = f"{emp.get('nombre', '')} {emp.get('apellido_paterno', '')}".strip()
                if emp.get('apellido_materno'):
                    nombre_completo += f" {emp['apellido_materno']}"
                r['empleado_nombre'] = nombre_completo
                documentos.append(EmpleadoDocumentoResumen(**r))

            return documentos

        except Exception as e:
            logger.error(f"Error obteniendo documentos pendientes empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error obteniendo documentos pendientes: {e}")

    async def contar_por_estatus(self, empleado_id: int) -> dict:
        """
        Cuenta documentos vigentes por estatus para un empleado.

        Returns:
            Dict con: total_requeridos, subidos, aprobados, rechazados, pendientes
        """
        try:
            # Documentos obligatorios definidos en el enum
            total_requeridos = sum(
                1 for t in TipoDocumentoEmpleado
                if t.es_obligatorio
            )

            # Documentos vigentes del empleado
            result = (
                self.supabase.table(self.tabla)
                .select('estatus, tipo_documento')
                .eq('empleado_id', empleado_id)
                .eq('es_vigente', True)
                .execute()
            )

            docs = result.data or []
            subidos = len(docs)
            aprobados = sum(1 for d in docs if d['estatus'] == EstatusDocumento.APROBADO.value)
            rechazados = sum(1 for d in docs if d['estatus'] == EstatusDocumento.RECHAZADO.value)
            pendientes = sum(
                1 for d in docs
                if d['estatus'] == EstatusDocumento.PENDIENTE_REVISION.value
            )

            return {
                'total_requeridos': total_requeridos,
                'subidos': subidos,
                'aprobados': aprobados,
                'rechazados': rechazados,
                'pendientes': pendientes,
            }

        except Exception as e:
            logger.error(f"Error contando documentos empleado {empleado_id}: {e}")
            raise DatabaseError(f"Error contando documentos: {e}")


empleado_documento_service = EmpleadoDocumentoService()
