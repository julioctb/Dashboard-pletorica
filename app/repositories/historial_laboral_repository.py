"""
Repositorio de Historial Laboral.

Este repositorio es principalmente de LECTURA.
Los registros se crean automaticamente desde el servicio.
"""
from typing import List, Optional
from datetime import date
import logging

from app.entities.historial_laboral import (
    HistorialLaboral,
    HistorialLaboralInterno,
    HistorialLaboralResumen,
)
from app.core.enums import EstatusHistorial, TipoMovimiento
from app.core.exceptions import NotFoundError, DatabaseError

logger = logging.getLogger(__name__)


class SupabaseHistorialLaboralRepository:
    """Implementacion del repositorio usando Supabase"""

    def __init__(self, db_manager=None):
        if db_manager is None:
            from app.database import db_manager as default_db
            db_manager = default_db

        self.supabase = db_manager.get_client()
        self.tabla = 'historial_laboral'

    # =========================================================================
    # LECTURA
    # =========================================================================

    async def obtener_por_id(self, historial_id: int) -> HistorialLaboral:
        """Obtiene un registro por su ID"""
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('id', historial_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Historial con ID {historial_id} no encontrado")

            return HistorialLaboral(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo historial {historial_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_empleado(
        self,
        empleado_id: int,
        limite: int = 50
    ) -> List[HistorialLaboralResumen]:
        """Obtiene el historial de un empleado con datos enriquecidos"""
        try:
            result = self.supabase.table(self.tabla)\
                .select('''
                    *,
                    empleados!inner(id, clave, nombre, apellido_paterno, apellido_materno)
                ''')\
                .eq('empleado_id', empleado_id)\
                .order('fecha_inicio', desc=True)\
                .limit(limite)\
                .execute()

            resumenes = []
            for data in result.data:
                empleado = data.get('empleados', {})
                nombre_completo = f"{empleado.get('nombre', '')} {empleado.get('apellido_paterno', '')}".strip()
                if empleado.get('apellido_materno'):
                    nombre_completo += f" {empleado.get('apellido_materno')}"

                # Obtener datos de plaza si existe
                plaza_numero = None
                categoria_nombre = None
                contrato_codigo = None
                empresa_nombre = None

                if data.get('plaza_id'):
                    plaza_data = await self._obtener_datos_plaza(data['plaza_id'])
                    if plaza_data:
                        plaza_numero = plaza_data.get('numero_plaza')
                        categoria_nombre = plaza_data.get('categoria_nombre')
                        contrato_codigo = plaza_data.get('contrato_codigo')
                        empresa_nombre = plaza_data.get('empresa_nombre')

                historial = HistorialLaboral(
                    id=data['id'],
                    empleado_id=data['empleado_id'],
                    plaza_id=data.get('plaza_id'),
                    tipo_movimiento=data.get('tipo_movimiento'),
                    fecha_inicio=data['fecha_inicio'],
                    fecha_fin=data.get('fecha_fin'),
                    estatus=data['estatus'],
                    notas=data.get('notas'),
                    fecha_creacion=data.get('fecha_creacion'),
                    fecha_actualizacion=data.get('fecha_actualizacion'),
                )

                resumen = HistorialLaboralResumen.from_historial(
                    historial=historial,
                    empleado_clave=empleado.get('clave', ''),
                    empleado_nombre=nombre_completo,
                    plaza_numero=plaza_numero,
                    categoria_nombre=categoria_nombre,
                    contrato_codigo=contrato_codigo,
                    empresa_nombre=empresa_nombre,
                )
                resumenes.append(resumen)

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo historial de empleado {empleado_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_todos(
        self,
        empleado_id: Optional[int] = None,
        estatus: Optional[str] = None,
        limite: int = 50,
        offset: int = 0
    ) -> List[HistorialLaboralResumen]:
        """Obtiene registros con filtros opcionales"""
        try:
            query = self.supabase.table(self.tabla)\
                .select('''
                    *,
                    empleados!inner(id, clave, nombre, apellido_paterno, apellido_materno)
                ''')

            if empleado_id:
                query = query.eq('empleado_id', empleado_id)
            if estatus and estatus != "TODOS":
                query = query.eq('estatus', estatus)

            query = query.order('fecha_inicio', desc=True)\
                .range(offset, offset + limite - 1)

            result = query.execute()

            resumenes = []
            for data in result.data:
                empleado = data.get('empleados', {})
                nombre_completo = f"{empleado.get('nombre', '')} {empleado.get('apellido_paterno', '')}".strip()
                if empleado.get('apellido_materno'):
                    nombre_completo += f" {empleado.get('apellido_materno')}"

                # Obtener datos de plaza si existe
                plaza_numero = None
                categoria_nombre = None
                contrato_codigo = None
                empresa_nombre = None

                if data.get('plaza_id'):
                    plaza_data = await self._obtener_datos_plaza(data['plaza_id'])
                    if plaza_data:
                        plaza_numero = plaza_data.get('numero_plaza')
                        categoria_nombre = plaza_data.get('categoria_nombre')
                        contrato_codigo = plaza_data.get('contrato_codigo')
                        empresa_nombre = plaza_data.get('empresa_nombre')

                historial = HistorialLaboral(
                    id=data['id'],
                    empleado_id=data['empleado_id'],
                    plaza_id=data.get('plaza_id'),
                    tipo_movimiento=data.get('tipo_movimiento'),
                    fecha_inicio=data['fecha_inicio'],
                    fecha_fin=data.get('fecha_fin'),
                    estatus=data['estatus'],
                    notas=data.get('notas'),
                    fecha_creacion=data.get('fecha_creacion'),
                    fecha_actualizacion=data.get('fecha_actualizacion'),
                )

                resumen = HistorialLaboralResumen.from_historial(
                    historial=historial,
                    empleado_clave=empleado.get('clave', ''),
                    empleado_nombre=nombre_completo,
                    plaza_numero=plaza_numero,
                    categoria_nombre=categoria_nombre,
                    contrato_codigo=contrato_codigo,
                    empresa_nombre=empresa_nombre,
                )
                resumenes.append(resumen)

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_registro_activo(self, empleado_id: int) -> Optional[HistorialLaboral]:
        """Obtiene el registro activo (sin fecha_fin) de un empleado"""
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('empleado_id', empleado_id)\
                .is_('fecha_fin', 'null')\
                .execute()

            if not result.data:
                return None

            return HistorialLaboral(**result.data[0])

        except Exception as e:
            logger.error(f"Error obteniendo registro activo: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # =========================================================================
    # ESCRITURA (usados internamente por el servicio)
    # =========================================================================

    async def crear(self, datos: HistorialLaboralInterno) -> HistorialLaboral:
        """Crea un nuevo registro de historial"""
        try:
            data_dict = datos.model_dump(mode='json')

            result = self.supabase.table(self.tabla)\
                .insert(data_dict)\
                .execute()

            if not result.data:
                raise DatabaseError("No se pudo crear el registro")

            return HistorialLaboral(**result.data[0])

        except Exception as e:
            logger.error(f"Error creando historial: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def cerrar_registro(
        self,
        historial_id: int,
        fecha_fin: date
    ) -> HistorialLaboral:
        """Cierra un registro estableciendo fecha_fin"""
        try:
            result = self.supabase.table(self.tabla)\
                .update({'fecha_fin': fecha_fin.isoformat()})\
                .eq('id', historial_id)\
                .execute()

            if not result.data:
                raise NotFoundError(f"Historial {historial_id} no encontrado")

            return HistorialLaboral(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error cerrando registro: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def cerrar_registro_activo(
        self,
        empleado_id: int,
        fecha_fin: date
    ) -> Optional[HistorialLaboral]:
        """Cierra el registro activo de un empleado (si existe)"""
        try:
            # Buscar registro activo
            registro_activo = await self.obtener_registro_activo(empleado_id)
            if not registro_activo:
                return None

            # Cerrar el registro
            return await self.cerrar_registro(registro_activo.id, fecha_fin)

        except Exception as e:
            logger.error(f"Error cerrando registro activo: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    # =========================================================================
    # HELPERS
    # =========================================================================

    async def _obtener_datos_plaza(self, plaza_id: int) -> Optional[dict]:
        """Obtiene datos enriquecidos de una plaza"""
        try:
            result = self.supabase.table('plazas')\
                .select('''
                    id, numero_plaza,
                    contrato_categorias!inner(
                        id,
                        categorias_puesto!inner(nombre),
                        contratos!inner(codigo, empresas!inner(nombre_comercial))
                    )
                ''')\
                .eq('id', plaza_id)\
                .execute()

            if not result.data:
                return None

            data = result.data[0]
            cc = data.get('contrato_categorias', {})
            cat = cc.get('categorias_puesto', {})
            contrato = cc.get('contratos', {})
            empresa = contrato.get('empresas', {})

            return {
                'numero_plaza': data.get('numero_plaza'),
                'categoria_nombre': cat.get('nombre'),
                'contrato_codigo': contrato.get('codigo'),
                'empresa_nombre': empresa.get('nombre_comercial'),
            }

        except Exception as e:
            logger.error(f"Error obteniendo datos de plaza {plaza_id}: {e}")
            return None

    async def contar(
        self,
        empleado_id: Optional[int] = None,
        estatus: Optional[str] = None
    ) -> int:
        """Cuenta registros con filtros"""
        try:
            query = self.supabase.table(self.tabla)\
                .select('id', count='exact')

            if empleado_id:
                query = query.eq('empleado_id', empleado_id)
            if estatus and estatus != "TODOS":
                query = query.eq('estatus', estatus)

            result = query.execute()
            return result.count or 0

        except Exception as e:
            logger.error(f"Error contando historial: {e}")
            return 0


# Interface para compatibilidad
IHistorialLaboralRepository = SupabaseHistorialLaboralRepository
