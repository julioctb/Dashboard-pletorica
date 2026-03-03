"""
Servicio para el catálogo de conceptos de nómina.

Patrón Direct Access (sin repository). Gestiona dos tablas:
- conceptos_nomina: catálogo global sincronizado desde CatalogoConceptosNomina
- conceptos_nomina_empresa: configuración por empresa (qué conceptos están activos)
"""
import logging
from typing import Optional
from uuid import UUID

from app.database import db_manager
from app.core.exceptions import DatabaseError, NotFoundError, BusinessRuleError
from app.core.catalogs import CatalogoConceptosNomina
from app.core.enums import TipoConcepto
from app.entities.concepto_nomina import (
    ConceptoNomina,
    ConceptoNominaResumen,
    ConceptoNominaEmpresa,
    ConceptoNominaEmpresaCreate,
    ConceptoNominaEmpresaResumen,
)

logger = logging.getLogger(__name__)


class ConceptoNominaService:
    """
    Servicio de conceptos de nómina.

    Responsabilidades:
    - Sincronizar el catálogo Python → BD (conceptos_nomina)
    - Gestionar la configuración por empresa (conceptos_nomina_empresa)
    """

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'conceptos_nomina'
        self.tabla_empresa = 'conceptos_nomina_empresa'

    # =========================================================================
    # SINCRONIZACIÓN DEL CATÁLOGO
    # =========================================================================

    async def sincronizar_catalogo(self) -> dict:
        """
        Sincroniza el catálogo Python (CatalogoConceptosNomina) con la BD.

        Hace UPSERT por clave: actualiza campos fiscales si cambiaron, inserta
        nuevos conceptos. No elimina conceptos existentes (preserva histórico).

        Returns:
            Dict con conteos: {'insertados': n, 'actualizados': n, 'total': n}

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            conceptos = CatalogoConceptosNomina.todos()
            registros = []
            for c in conceptos:
                registros.append({
                    'clave': c.clave,
                    'nombre': c.nombre,
                    'descripcion': c.descripcion,
                    'tipo': c.tipo.value if hasattr(c.tipo, 'value') else c.tipo,
                    'clave_sat': c.clave_sat,
                    'nombre_sat': c.nombre_sat,
                    'categoria': c.categoria.value if hasattr(c.categoria, 'value') else c.categoria,
                    'tratamiento_isr': (
                        c.tratamiento_isr.value
                        if hasattr(c.tratamiento_isr, 'value')
                        else c.tratamiento_isr
                    ),
                    'integra_sbc': c.integra_sbc,
                    'origen_captura': (
                        c.origen_captura.value
                        if hasattr(c.origen_captura, 'value')
                        else c.origen_captura
                    ),
                    'es_obligatorio': c.es_obligatorio,
                    'es_legal': True,
                    'orden_default': c.orden_default,
                    'activo': True,
                })

            result = (
                self.supabase.table(self.tabla)
                .upsert(registros, on_conflict='clave')
                .execute()
            )

            total = len(result.data) if result.data else 0
            logger.info(f"Catálogo nómina sincronizado: {total} conceptos")
            return {'total': total}

        except Exception as e:
            logger.error(f"Error sincronizando catálogo nómina: {e}")
            raise DatabaseError(f"Error sincronizando catálogo de conceptos: {e}")

    # =========================================================================
    # CONSULTAS DEL CATÁLOGO GLOBAL
    # =========================================================================

    async def obtener_todos(self, solo_activos: bool = True) -> list[ConceptoNominaResumen]:
        """
        Obtiene todos los conceptos del catálogo global.

        Args:
            solo_activos: Si True, filtra por activo=True.

        Returns:
            Lista de ConceptoNominaResumen ordenada por orden_default.
        """
        try:
            query = self.supabase.table(self.tabla).select('*').order('orden_default')
            if solo_activos:
                query = query.eq('activo', True)
            result = query.execute()
            return [ConceptoNominaResumen(**r) for r in (result.data or [])]

        except Exception as e:
            logger.error(f"Error obteniendo conceptos nómina: {e}")
            raise DatabaseError(f"Error obteniendo conceptos de nómina: {e}")

    async def obtener_por_clave(self, clave: str) -> ConceptoNomina:
        """
        Obtiene un concepto por su clave interna.

        Raises:
            NotFoundError: Si la clave no existe en BD.
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .select('*')
                .eq('clave', clave)
                .execute()
            )
            if not result.data:
                raise NotFoundError(f"Concepto de nómina '{clave}' no encontrado")
            return ConceptoNomina(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo concepto nómina '{clave}': {e}")
            raise DatabaseError(f"Error obteniendo concepto de nómina: {e}")

    async def obtener_por_tipo(self, tipo: TipoConcepto) -> list[ConceptoNominaResumen]:
        """Filtra conceptos por tipo (PERCEPCION, DEDUCCION, OTRO_PAGO)."""
        try:
            tipo_val = tipo.value if hasattr(tipo, 'value') else tipo
            result = (
                self.supabase.table(self.tabla)
                .select('*')
                .eq('tipo', tipo_val)
                .eq('activo', True)
                .order('orden_default')
                .execute()
            )
            return [ConceptoNominaResumen(**r) for r in (result.data or [])]

        except Exception as e:
            logger.error(f"Error filtrando conceptos por tipo '{tipo}': {e}")
            raise DatabaseError(f"Error filtrando conceptos de nómina: {e}")

    # =========================================================================
    # CONFIGURACIÓN POR EMPRESA
    # =========================================================================

    async def inicializar_empresa(self, empresa_id: int) -> int:
        """
        Activa los conceptos obligatorios para una empresa nueva.

        Inserta en conceptos_nomina_empresa todos los conceptos con
        es_obligatorio=True del catálogo, usando ON CONFLICT DO NOTHING
        para ser idempotente.

        Returns:
            Número de registros creados.

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            # Obtener IDs de conceptos obligatorios
            result_conceptos = (
                self.supabase.table(self.tabla)
                .select('id')
                .eq('es_obligatorio', True)
                .eq('activo', True)
                .execute()
            )
            if not result_conceptos.data:
                logger.warning(f"No se encontraron conceptos obligatorios para empresa {empresa_id}")
                return 0

            registros = [
                {
                    'empresa_id': empresa_id,
                    'concepto_id': r['id'],
                    'activo': True,
                    'orden_recibo': 0,
                }
                for r in result_conceptos.data
            ]

            result = (
                self.supabase.table(self.tabla_empresa)
                .upsert(registros, on_conflict='empresa_id,concepto_id')
                .execute()
            )
            total = len(result.data) if result.data else 0
            logger.info(f"Empresa {empresa_id} inicializada con {total} conceptos obligatorios")
            return total

        except Exception as e:
            logger.error(f"Error inicializando conceptos empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error inicializando conceptos de empresa: {e}")

    async def obtener_conceptos_empresa(
        self,
        empresa_id: int,
        solo_activos: bool = True,
    ) -> list[ConceptoNominaEmpresaResumen]:
        """
        Obtiene los conceptos configurados para una empresa con datos del catálogo.

        Hace JOIN con conceptos_nomina para incluir clave, nombre, tipo, etc.

        Args:
            empresa_id: ID de la empresa.
            solo_activos: Si True, filtra por activo=True en la relación empresa.

        Returns:
            Lista de ConceptoNominaEmpresaResumen ordenada por orden_recibo.
        """
        try:
            query = (
                self.supabase.table(self.tabla_empresa)
                .select('*, conceptos_nomina(clave, nombre, tipo, clave_sat, categoria, es_legal)')
                .eq('empresa_id', empresa_id)
                .order('orden_recibo')
            )
            if solo_activos:
                query = query.eq('activo', True)

            result = query.execute()
            items = []
            for r in (result.data or []):
                concepto = r.pop('conceptos_nomina', {}) or {}
                items.append(ConceptoNominaEmpresaResumen(
                    **r,
                    concepto_clave=concepto.get('clave', ''),
                    concepto_nombre=concepto.get('nombre', ''),
                    concepto_tipo=concepto.get('tipo', ''),
                    concepto_clave_sat=concepto.get('clave_sat', ''),
                    concepto_categoria=concepto.get('categoria', ''),
                    concepto_es_legal=concepto.get('es_legal', True),
                ))
            return items

        except Exception as e:
            logger.error(f"Error obteniendo conceptos empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error obteniendo conceptos de empresa: {e}")

    async def activar_concepto(
        self,
        empresa_id: int,
        concepto_id: int,
        nombre_personalizado: Optional[str] = None,
        orden_recibo: int = 0,
    ) -> ConceptoNominaEmpresa:
        """
        Activa un concepto para una empresa (crea o re-activa).

        Si ya existe la relación empresa-concepto, la re-activa (activo=True).
        Si no existe, la crea.

        Raises:
            NotFoundError: Si el concepto no existe en el catálogo.
            DatabaseError: Si hay error de BD.
        """
        try:
            # Verificar que el concepto existe
            res_concepto = (
                self.supabase.table(self.tabla)
                .select('id')
                .eq('id', concepto_id)
                .execute()
            )
            if not res_concepto.data:
                raise NotFoundError(f"Concepto de nómina con ID {concepto_id} no encontrado")

            datos = {
                'empresa_id': empresa_id,
                'concepto_id': concepto_id,
                'activo': True,
                'orden_recibo': orden_recibo,
            }
            if nombre_personalizado is not None:
                datos['nombre_personalizado'] = nombre_personalizado

            result = (
                self.supabase.table(self.tabla_empresa)
                .upsert(datos, on_conflict='empresa_id,concepto_id')
                .execute()
            )
            return ConceptoNominaEmpresa(**result.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error activando concepto {concepto_id} empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error activando concepto de empresa: {e}")

    async def desactivar_concepto(self, empresa_id: int, concepto_id: int) -> None:
        """
        Desactiva un concepto para una empresa (activo=False).

        No elimina el registro para preservar el histórico.

        Raises:
            NotFoundError: Si la relación empresa-concepto no existe.
            BusinessRuleError: Si el concepto es obligatorio.
            DatabaseError: Si hay error de BD.
        """
        try:
            # Verificar que existe la relación
            res = (
                self.supabase.table(self.tabla_empresa)
                .select('id, concepto_id')
                .eq('empresa_id', empresa_id)
                .eq('concepto_id', concepto_id)
                .execute()
            )
            if not res.data:
                raise NotFoundError(
                    f"Concepto {concepto_id} no asignado a empresa {empresa_id}"
                )

            # Verificar que no es obligatorio
            res_cat = (
                self.supabase.table(self.tabla)
                .select('es_obligatorio, nombre')
                .eq('id', concepto_id)
                .execute()
            )
            if res_cat.data and res_cat.data[0].get('es_obligatorio'):
                nombre = res_cat.data[0].get('nombre', str(concepto_id))
                raise BusinessRuleError(
                    f"No se puede desactivar '{nombre}': es un concepto obligatorio"
                )

            self.supabase.table(self.tabla_empresa).update({'activo': False}).eq(
                'empresa_id', empresa_id
            ).eq('concepto_id', concepto_id).execute()

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error desactivando concepto {concepto_id} empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error desactivando concepto de empresa: {e}")

    async def actualizar_nombre_personalizado(
        self,
        empresa_id: int,
        concepto_id: int,
        nombre_personalizado: Optional[str],
    ) -> ConceptoNominaEmpresa:
        """
        Actualiza el nombre personalizado de un concepto en una empresa.

        Pasar None para borrar el nombre personalizado (usará el nombre del catálogo).

        Raises:
            NotFoundError: Si la relación empresa-concepto no existe.
        """
        try:
            res = (
                self.supabase.table(self.tabla_empresa)
                .update({'nombre_personalizado': nombre_personalizado})
                .eq('empresa_id', empresa_id)
                .eq('concepto_id', concepto_id)
                .execute()
            )
            if not res.data:
                raise NotFoundError(
                    f"Concepto {concepto_id} no asignado a empresa {empresa_id}"
                )
            return ConceptoNominaEmpresa(**res.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando nombre personalizado concepto {concepto_id}: {e}")
            raise DatabaseError(f"Error actualizando nombre personalizado: {e}")

    async def actualizar_orden_recibo(
        self,
        empresa_id: int,
        concepto_id: int,
        orden_recibo: int,
    ) -> ConceptoNominaEmpresa:
        """
        Actualiza el orden de aparición en el recibo de nómina.

        Raises:
            NotFoundError: Si la relación empresa-concepto no existe.
        """
        try:
            res = (
                self.supabase.table(self.tabla_empresa)
                .update({'orden_recibo': orden_recibo})
                .eq('empresa_id', empresa_id)
                .eq('concepto_id', concepto_id)
                .execute()
            )
            if not res.data:
                raise NotFoundError(
                    f"Concepto {concepto_id} no asignado a empresa {empresa_id}"
                )
            return ConceptoNominaEmpresa(**res.data[0])

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando orden recibo concepto {concepto_id}: {e}")
            raise DatabaseError(f"Error actualizando orden de recibo: {e}")


# Singleton
concepto_nomina_service = ConceptoNominaService()
