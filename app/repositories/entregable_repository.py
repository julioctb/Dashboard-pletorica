"""
Repositorio para Entregables.

Maneja queries complejos que requieren JOINs entre entregables,
contratos, empresas y categorías. Usado por EntregableService.

Patrón de manejo de errores (igual que otros repositorios):
- NotFoundError: Cuando no se encuentra un recurso
- DatabaseError: Errores de conexión/infraestructura
- Las excepciones se propagan, NO se capturan aquí
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.database import db_manager
from app.core.exceptions import DatabaseError, NotFoundError
from app.core.enums import EstatusEntregable, EstatusContrato
from app.entities.entregable import (
    Entregable,
    EntregableResumen,
    EntregableDetallePersonal,
    EntregableDetallePersonalResumen,
    ResumenEntregablesContrato,
    AlertaEntregables,
)

logger = logging.getLogger(__name__)


class SupabaseEntregableRepository:
    """
    Repositorio de Entregables usando Supabase.
    
    Sigue el mismo patrón de otros repositorios del proyecto:
    - Singleton de db_manager para conexión
    - Excepciones tipadas (NotFoundError, DatabaseError)
    - Logging para debugging
    """
    
    def __init__(self, db_manager_override=None):
        if db_manager_override is None:
            self.supabase = db_manager.get_client()
        else:
            self.supabase = db_manager_override.get_client()
        
        self.tabla = "entregables"
        self.tabla_detalle = "entregable_detalle_personal"
        self.tabla_config = "contrato_tipo_entregable"
    
    # =========================================================================
    # CRUD BÁSICO: ENTREGABLES
    # =========================================================================
    
    async def obtener_por_id(self, entregable_id: int) -> Entregable:
        """
        Obtiene un entregable por su ID.
        
        Raises:
            NotFoundError: Si no existe
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('id', entregable_id)\
                .execute()
            
            if not result.data:
                raise NotFoundError(f"Entregable con ID {entregable_id} no encontrado")
            
            return Entregable(**result.data[0])
        
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo entregable {entregable_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def obtener_por_contrato(
        self,
        contrato_id: int,
        incluir_todos: bool = False,
    ) -> List[Entregable]:
        """
        Obtiene todos los entregables de un contrato.
        
        Args:
            contrato_id: ID del contrato
            incluir_todos: Si False, excluye aprobados antiguos
        
        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_id', contrato_id)\
                .order('numero_periodo', desc=False)
            
            result = query.execute()
            return [Entregable(**data) for data in result.data]
        
        except Exception as e:
            logger.error(f"Error obteniendo entregables del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def obtener_por_contrato_y_periodo(
        self,
        contrato_id: int,
        numero_periodo: int,
    ) -> Optional[Entregable]:
        """
        Obtiene un entregable específico por contrato y número de período.
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('*')\
                .eq('contrato_id', contrato_id)\
                .eq('numero_periodo', numero_periodo)\
                .execute()
            
            if not result.data:
                return None
            
            return Entregable(**result.data[0])
        
        except Exception as e:
            logger.error(f"Error obteniendo entregable {contrato_id}/{numero_periodo}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def crear(self, entregable: Entregable) -> Entregable:
        """
        Crea un nuevo entregable.
        
        Raises:
            DatabaseError: Si hay error de BD
        """
        try:
            datos = entregable.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'}
            )
            
            result = self.supabase.table(self.tabla)\
                .insert(datos)\
                .execute()
            
            if not result.data:
                raise DatabaseError("No se pudo crear el entregable")
            
            return Entregable(**result.data[0])
        
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error creando entregable: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def actualizar(self, entregable: Entregable) -> Entregable:
        """
        Actualiza un entregable existente.
        
        Raises:
            NotFoundError: Si no existe
            DatabaseError: Si hay error de BD
        """
        try:
            datos = entregable.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion', 'fecha_actualizacion'}
            )
            
            result = self.supabase.table(self.tabla)\
                .update(datos)\
                .eq('id', entregable.id)\
                .execute()
            
            if not result.data:
                raise NotFoundError(f"Entregable con ID {entregable.id} no encontrado")
            
            return Entregable(**result.data[0])
        
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error actualizando entregable {entregable.id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def eliminar(self, entregable_id: int) -> bool:
        """
        Elimina un entregable.
        
        Raises:
            NotFoundError: Si no existe
            DatabaseError: Si hay error de BD
        """
        try:
            result = self.supabase.table(self.tabla)\
                .delete()\
                .eq('id', entregable_id)\
                .execute()
            
            if not result.data:
                raise NotFoundError(f"Entregable con ID {entregable_id} no encontrado")
            
            return True
        
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando entregable {entregable_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    # =========================================================================
    # QUERIES CON JOINS
    # =========================================================================
    
    async def obtener_resumen_por_contrato(
        self,
        contrato_id: int,
    ) -> List[EntregableResumen]:
        """
        Obtiene resumen de entregables con datos del contrato y empresa.
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select(
                    '*, '
                    'contratos!inner(codigo, empresa_id, empresas!inner(nombre_comercial))'
                )\
                .eq('contrato_id', contrato_id)\
                .order('numero_periodo', desc=False)\
                .execute()
            
            resumenes = []
            for data in result.data:
                contrato = data.pop('contratos', {})
                empresa = contrato.pop('empresas', {}) if contrato else {}
                
                resumen = EntregableResumen(
                    id=data['id'],
                    contrato_id=data['contrato_id'],
                    numero_periodo=data['numero_periodo'],
                    periodo_inicio=data['periodo_inicio'],
                    periodo_fin=data['periodo_fin'],
                    estatus=data['estatus'],
                    fecha_entrega=data.get('fecha_entrega'),
                    monto_aprobado=data.get('monto_aprobado'),
                    contrato_codigo=contrato.get('codigo', ''),
                    empresa_id=contrato.get('empresa_id'),
                    empresa_nombre=empresa.get('nombre_comercial', ''),
                )
                resumenes.append(resumen)
            
            return resumenes
        
        except Exception as e:
            logger.error(f"Error obteniendo resumen de entregables: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def obtener_en_revision(
        self,
        empresa_id: Optional[int] = None,
        limite: int = 50,
    ) -> List[EntregableResumen]:
        """
        Obtiene entregables en estado EN_REVISION para dashboard de alertas.
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select(
                    '*, '
                    'contratos!inner(codigo, empresa_id, empresas!inner(nombre_comercial))'
                )\
                .eq('estatus', EstatusEntregable.EN_REVISION.value)

            if empresa_id:
                query = query.eq('contratos.empresa_id', empresa_id)

            query = query.order('fecha_entrega', desc=True).limit(limite)
            result = query.execute()

            resumenes = []
            for data in result.data:
                contrato = data.pop('contratos', {})
                empresa = contrato.pop('empresas', {}) if contrato else {}

                resumen = EntregableResumen(
                    id=data['id'],
                    contrato_id=data['contrato_id'],
                    numero_periodo=data['numero_periodo'],
                    periodo_inicio=data['periodo_inicio'],
                    periodo_fin=data['periodo_fin'],
                    estatus=data['estatus'],
                    fecha_entrega=data.get('fecha_entrega'),
                    monto_aprobado=data.get('monto_aprobado'),
                    contrato_codigo=contrato.get('codigo', ''),
                    empresa_id=contrato.get('empresa_id'),
                    empresa_nombre=empresa.get('nombre_comercial', ''),
                )
                resumenes.append(resumen)

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo entregables en revisión: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_todos_global(
        self,
        estatus: Optional[str] = None,
        contrato_id: Optional[int] = None,
        limite: int = 100,
    ) -> List[EntregableResumen]:
        """
        Obtiene todos los entregables con datos de contrato y empresa.
        Usado para la vista global del admin.

        Args:
            estatus: Filtrar por estatus específico (opcional)
            contrato_id: Filtrar por contrato específico (opcional)
            limite: Máximo de resultados

        Returns:
            Lista de EntregableResumen ordenados por fecha_entrega DESC
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select(
                    '*, '
                    'contratos!inner(codigo, empresa_id, empresas!inner(nombre_comercial))'
                )

            if estatus:
                query = query.eq('estatus', estatus)

            if contrato_id:
                query = query.eq('contrato_id', contrato_id)

            # Ordenar por fecha_entrega DESC (más recientes primero),
            # nulos al final usando numero_periodo como fallback
            query = query.order('fecha_entrega', desc=True, nullsfirst=False)\
                .order('numero_periodo', desc=True)\
                .limit(limite)

            result = query.execute()

            resumenes = []
            for data in result.data:
                contrato = data.pop('contratos', {})
                empresa = contrato.pop('empresas', {}) if contrato else {}

                resumen = EntregableResumen(
                    id=data['id'],
                    contrato_id=data['contrato_id'],
                    numero_periodo=data['numero_periodo'],
                    periodo_inicio=data['periodo_inicio'],
                    periodo_fin=data['periodo_fin'],
                    estatus=data['estatus'],
                    fecha_entrega=data.get('fecha_entrega'),
                    monto_aprobado=data.get('monto_aprobado'),
                    contrato_codigo=contrato.get('codigo', ''),
                    empresa_id=contrato.get('empresa_id'),
                    empresa_nombre=empresa.get('nombre_comercial', ''),
                )
                resumenes.append(resumen)

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo entregables global: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_estadisticas_global(self) -> dict:
        """
        Obtiene estadísticas globales de todos los entregables.

        Returns:
            Dict con contadores por estatus
        """
        try:
            result = self.supabase.table(self.tabla)\
                .select('estatus')\
                .execute()

            stats = {
                "total": 0,
                "pendientes": 0,
                "en_revision": 0,
                "aprobados": 0,
                "rechazados": 0,
            }

            for ent in result.data:
                stats["total"] += 1
                estatus = ent['estatus']
                if estatus == EstatusEntregable.PENDIENTE.value:
                    stats["pendientes"] += 1
                elif estatus == EstatusEntregable.EN_REVISION.value:
                    stats["en_revision"] += 1
                elif estatus == EstatusEntregable.APROBADO.value:
                    stats["aprobados"] += 1
                elif estatus == EstatusEntregable.RECHAZADO.value:
                    stats["rechazados"] += 1

            return stats

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas globales: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_por_empresa(
        self,
        empresa_id: int,
        estatus_list: Optional[List[str]] = None,
        contrato_id: Optional[int] = None,
        limite: int = 100,
    ) -> List[EntregableResumen]:
        """
        Obtiene entregables de todos los contratos de una empresa.
        Usado para la vista global del cliente en el portal.

        Args:
            empresa_id: ID de la empresa
            estatus_list: Lista de estatus a filtrar (opcional)
            contrato_id: Filtrar por contrato específico (opcional)
            limite: Máximo de resultados

        Returns:
            Lista de EntregableResumen ordenados: rechazados primero, luego por fecha
        """
        try:
            query = self.supabase.table(self.tabla)\
                .select(
                    '*, '
                    'contratos!inner(codigo, empresa_id, empresas!inner(nombre_comercial))'
                )\
                .eq('contratos.empresa_id', empresa_id)

            if contrato_id:
                query = query.eq('contrato_id', contrato_id)

            if estatus_list:
                query = query.in_('estatus', estatus_list)

            # Ordenar: rechazados primero, luego por periodo_fin desc
            query = query.order('estatus', desc=False)\
                .order('periodo_fin', desc=True)\
                .limit(limite)

            result = query.execute()

            resumenes = []
            for data in result.data:
                contrato = data.pop('contratos', {})
                empresa = contrato.pop('empresas', {}) if contrato else {}

                resumen = EntregableResumen(
                    id=data['id'],
                    contrato_id=data['contrato_id'],
                    numero_periodo=data['numero_periodo'],
                    periodo_inicio=data['periodo_inicio'],
                    periodo_fin=data['periodo_fin'],
                    estatus=data['estatus'],
                    fecha_entrega=data.get('fecha_entrega'),
                    monto_aprobado=data.get('monto_aprobado'),
                    contrato_codigo=contrato.get('codigo', ''),
                    empresa_id=contrato.get('empresa_id'),
                    empresa_nombre=empresa.get('nombre_comercial', ''),
                    observaciones_rechazo=data.get('observaciones_rechazo'),
                )
                resumenes.append(resumen)

            # Ordenar: RECHAZADO primero, luego PENDIENTE, luego el resto
            orden_estatus = {
                EstatusEntregable.RECHAZADO.value: 0,
                EstatusEntregable.PENDIENTE.value: 1,
                EstatusEntregable.EN_REVISION.value: 2,
                EstatusEntregable.APROBADO.value: 3,
            }
            resumenes.sort(key=lambda r: (
                orden_estatus.get(r.estatus.value if hasattr(r.estatus, 'value') else r.estatus, 99),
                str(r.periodo_fin) if r.periodo_fin else ''
            ))

            return resumenes

        except Exception as e:
            logger.error(f"Error obteniendo entregables por empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")

    async def obtener_estadisticas_empresa(self, empresa_id: int) -> dict:
        """
        Obtiene estadísticas de entregables para una empresa.

        Returns:
            Dict con contadores por estatus
        """
        try:
            # Primero obtener los IDs de contratos de la empresa
            contratos_result = self.supabase.table('contratos')\
                .select('id')\
                .eq('empresa_id', empresa_id)\
                .execute()

            contrato_ids = [c['id'] for c in contratos_result.data]

            if not contrato_ids:
                return {
                    "total": 0,
                    "pendientes": 0,
                    "en_revision": 0,
                    "aprobados": 0,
                    "rechazados": 0,
                }

            result = self.supabase.table(self.tabla)\
                .select('estatus')\
                .in_('contrato_id', contrato_ids)\
                .execute()

            stats = {
                "total": 0,
                "pendientes": 0,
                "en_revision": 0,
                "aprobados": 0,
                "rechazados": 0,
            }

            for ent in result.data:
                stats["total"] += 1
                estatus = ent['estatus']
                if estatus == EstatusEntregable.PENDIENTE.value:
                    stats["pendientes"] += 1
                elif estatus == EstatusEntregable.EN_REVISION.value:
                    stats["en_revision"] += 1
                elif estatus == EstatusEntregable.APROBADO.value:
                    stats["aprobados"] += 1
                elif estatus == EstatusEntregable.RECHAZADO.value:
                    stats["rechazados"] += 1

            return stats

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def contar_en_revision(self, empresa_id: Optional[int] = None) -> int:
        """Cuenta entregables en estado EN_REVISION."""
        try:
            query = self.supabase.table(self.tabla)\
                .select('id', count='exact')\
                .eq('estatus', EstatusEntregable.EN_REVISION.value)
            
            if empresa_id:
                contratos_result = self.supabase.table('contratos')\
                    .select('id')\
                    .eq('empresa_id', empresa_id)\
                    .execute()
                
                contrato_ids = [c['id'] for c in contratos_result.data]
                if contrato_ids:
                    query = query.in_('contrato_id', contrato_ids)
                else:
                    return 0
            
            result = query.execute()
            return result.count or 0
        
        except Exception as e:
            logger.error(f"Error contando entregables en revisión: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def obtener_alertas(
        self,
        empresa_id: Optional[int] = None,
        limite: int = 10,
    ) -> AlertaEntregables:
        """Obtiene alertas de entregables para el dashboard."""
        try:
            total = await self.contar_en_revision(empresa_id)
            entregables = await self.obtener_en_revision(empresa_id, limite)
            
            return AlertaEntregables(
                total_en_revision=total,
                entregables=entregables,
            )
        
        except Exception as e:
            logger.error(f"Error obteniendo alertas: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    # =========================================================================
    # ESTADÍSTICAS
    # =========================================================================
    
    async def obtener_estadisticas_contrato(
        self,
        contrato_id: int,
    ) -> ResumenEntregablesContrato:
        """Obtiene estadísticas de entregables para un contrato."""
        try:
            contrato_result = self.supabase.table('contratos')\
                .select('codigo')\
                .eq('id', contrato_id)\
                .execute()
            
            codigo_contrato = contrato_result.data[0]['codigo'] if contrato_result.data else ''
            
            result = self.supabase.table(self.tabla)\
                .select('estatus, monto_aprobado')\
                .eq('contrato_id', contrato_id)\
                .execute()
            
            pendientes = en_revision = aprobados = rechazados = 0
            monto_total = Decimal("0")
            
            for ent in result.data:
                estatus = ent['estatus']
                if estatus == EstatusEntregable.PENDIENTE.value:
                    pendientes += 1
                elif estatus == EstatusEntregable.EN_REVISION.value:
                    en_revision += 1
                elif estatus == EstatusEntregable.APROBADO.value:
                    aprobados += 1
                    if ent['monto_aprobado']:
                        monto_total += Decimal(str(ent['monto_aprobado']))
                elif estatus == EstatusEntregable.RECHAZADO.value:
                    rechazados += 1
            
            pagos_result = self.supabase.table('pagos')\
                .select('monto')\
                .eq('contrato_id', contrato_id)\
                .eq('estatus', 'PAGADO')\
                .execute()
            
            monto_pagado = sum(
                Decimal(str(p['monto'])) for p in pagos_result.data
            ) if pagos_result.data else Decimal("0")
            
            return ResumenEntregablesContrato(
                contrato_id=contrato_id,
                codigo_contrato=codigo_contrato,
                total_periodos=len(result.data),
                pendientes=pendientes,
                en_revision=en_revision,
                aprobados=aprobados,
                rechazados=rechazados,
                monto_total_aprobado=monto_total,
                monto_total_pagado=monto_pagado,
            )
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def obtener_ultimo_numero_periodo(self, contrato_id: int) -> int:
        """Obtiene el último número de período usado para un contrato."""
        try:
            result = self.supabase.table(self.tabla)\
                .select('numero_periodo')\
                .eq('contrato_id', contrato_id)\
                .order('numero_periodo', desc=True)\
                .limit(1)\
                .execute()
            
            if not result.data:
                return 0
            
            return result.data[0]['numero_periodo']
        
        except Exception as e:
            logger.error(f"Error obteniendo último período del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    # =========================================================================
    # DETALLE DE PERSONAL
    # =========================================================================
    
    async def obtener_detalle_personal(
        self,
        entregable_id: int,
    ) -> List[EntregableDetallePersonalResumen]:
        """Obtiene el detalle de personal con datos de categoría."""
        try:
            result = self.supabase.table(self.tabla_detalle)\
                .select(
                    '*, '
                    'contrato_categorias!inner('
                    '   categoria_puesto_id, cantidad_minima, cantidad_maxima, '
                    '   categorias_puesto!inner(clave, nombre)'
                    ')'
                )\
                .eq('entregable_id', entregable_id)\
                .execute()
            
            detalles = []
            for data in result.data:
                cc = data.pop('contrato_categorias', {})
                cat = cc.pop('categorias_puesto', {}) if cc else {}
                
                detalle = EntregableDetallePersonalResumen(
                    id=data['id'],
                    entregable_id=data['entregable_id'],
                    contrato_categoria_id=data['contrato_categoria_id'],
                    cantidad_reportada=data['cantidad_reportada'],
                    cantidad_validada=data['cantidad_validada'],
                    tarifa_unitaria=Decimal(str(data['tarifa_unitaria'])),
                    subtotal=Decimal(str(data['subtotal'])),
                    categoria_clave=cat.get('clave', ''),
                    categoria_nombre=cat.get('nombre', ''),
                    cantidad_minima=cc.get('cantidad_minima', 0),
                    cantidad_maxima=cc.get('cantidad_maxima', 0),
                )
                detalles.append(detalle)
            
            return detalles
        
        except Exception as e:
            logger.error(f"Error obteniendo detalle de personal: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def crear_detalle_personal(
        self,
        detalle: EntregableDetallePersonal,
    ) -> EntregableDetallePersonal:
        """Crea un registro de detalle de personal."""
        try:
            datos = detalle.model_dump(
                mode='json',
                exclude={'id', 'fecha_creacion'}
            )
            
            result = self.supabase.table(self.tabla_detalle)\
                .insert(datos)\
                .execute()
            
            if not result.data:
                raise DatabaseError("No se pudo crear el detalle de personal")
            
            return EntregableDetallePersonal(**result.data[0])
        
        except Exception as e:
            logger.error(f"Error creando detalle de personal: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def eliminar_detalle_personal(self, entregable_id: int) -> int:
        """Elimina todos los detalles de personal de un entregable."""
        try:
            result = self.supabase.table(self.tabla_detalle)\
                .delete()\
                .eq('entregable_id', entregable_id)\
                .execute()
            
            return len(result.data) if result.data else 0
        
        except Exception as e:
            logger.error(f"Error eliminando detalle de personal: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    # =========================================================================
    # CONFIGURACIÓN DE TIPOS
    # =========================================================================
    
    async def obtener_configuracion_contrato(
        self,
        contrato_id: int,
    ) -> List[dict]:
        """Obtiene la configuración de tipos de entregable de un contrato."""
        try:
            result = self.supabase.table(self.tabla_config)\
                .select('*')\
                .eq('contrato_id', contrato_id)\
                .execute()
            
            return result.data or []
        
        except Exception as e:
            logger.error(f"Error obteniendo configuración del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
    
    async def obtener_periodicidad_contrato(
        self,
        contrato_id: int,
    ) -> Optional[str]:
        """Obtiene la periodicidad configurada para un contrato."""
        try:
            result = self.supabase.table(self.tabla_config)\
                .select('periodicidad')\
                .eq('contrato_id', contrato_id)\
                .limit(1)\
                .execute()
            
            if not result.data:
                return None
            
            return result.data[0]['periodicidad']
        
        except Exception as e:
            logger.error(f"Error obteniendo periodicidad del contrato {contrato_id}: {e}")
            raise DatabaseError(f"Error de base de datos: {str(e)}")
