"""
Servicio para el módulo Cotizador.

Patrón Direct Access. Gestiona cotizaciones, partidas, categorías,
conceptos y la integración con el motor CalculadoraCostoPatronal.
"""
import logging
from datetime import date
from decimal import Decimal
from typing import Optional, Union
from uuid import UUID

from app.database import db_manager
from app.core.exceptions import (
    DatabaseError, NotFoundError, BusinessRuleError
)
from app.core.enums import (
    EstatusCotizacion, EstatusPartidaCotizacion,
    TipoConceptoCotizacion, TipoValorConcepto,
    EstatusContrato, TipoContrato,
)
from app.entities.cotizacion import (
    Cotizacion, CotizacionCreate, CotizacionUpdate, CotizacionResumen,
)
from app.entities.cotizacion_partida import (
    CotizacionPartida, CotizacionPartidaResumen,
)
from app.entities.cotizacion_partida_categoria import (
    CotizacionPartidaCategoria, CotizacionPartidaCategoriaCreate,
    CotizacionPartidaCategoriaResumen,
)
from app.entities.cotizacion_concepto import CotizacionConcepto, CotizacionConceptoCreate
from app.entities.cotizacion_concepto_valor import (
    CotizacionConceptoValor,
)

logger = logging.getLogger(__name__)

_ESTATUS_COTIZACION_EDITABLE = {EstatusCotizacion.BORRADOR.value}

# Transiciones válidas de estatus
_TRANSICIONES_COTIZACION = {
    EstatusCotizacion.BORRADOR:  {EstatusCotizacion.PREPARADA},
    EstatusCotizacion.PREPARADA: {EstatusCotizacion.ENVIADA, EstatusCotizacion.APROBADA, EstatusCotizacion.RECHAZADA},
    EstatusCotizacion.ENVIADA:   {EstatusCotizacion.APROBADA, EstatusCotizacion.RECHAZADA},
    EstatusCotizacion.APROBADA:  set(),
    EstatusCotizacion.RECHAZADA: set(),
}

class CotizacionService:
    """Servicio principal del módulo Cotizador."""

    def __init__(self):
        self.supabase = db_manager.get_client()

    # =========================================================================
    # COTIZACIONES — CRUD
    # =========================================================================

    async def crear(
        self, datos: CotizacionCreate, user_id: Optional[Union[str, UUID]] = None
    ) -> Cotizacion:
        """
        Crea una nueva cotización.

        Auto-genera código COT-[EMPRESA_CODIGO]-[AÑO][SEQ].
        Pre-llena representante_legal desde configuracion_fiscal_empresa.

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            # Obtener empresa para código
            empresa_result = (
                self.supabase.table('empresas')
                .select('id, codigo_corto, nombre_comercial')
                .eq('id', datos.empresa_id)
                .single()
                .execute()
            )
            if not empresa_result.data:
                raise NotFoundError(f"Empresa {datos.empresa_id} no encontrada")

            empresa = empresa_result.data
            empresa_codigo = (empresa.get('codigo_corto') or '').strip().upper()
            if not empresa_codigo:
                raise BusinessRuleError(
                    "La empresa no tiene codigo_corto configurado para generar cotizaciones"
                )
            codigo = await self._generar_codigo(empresa_codigo)

            # Pre-llenar representante_legal si no viene en datos
            representante_legal = datos.representante_legal
            if not representante_legal:
                config_result = (
                    self.supabase.table('configuracion_fiscal_empresa')
                    .select('representante_legal_nombre')
                    .eq('empresa_id', datos.empresa_id)
                    .execute()
                )
                if config_result.data and config_result.data[0].get('representante_legal_nombre'):
                    representante_legal = config_result.data[0]['representante_legal_nombre']

            payload = {
                'codigo': codigo,
                'empresa_id': datos.empresa_id,
                'fecha_inicio_periodo': datos.fecha_inicio_periodo.isoformat(),
                'fecha_fin_periodo': datos.fecha_fin_periodo.isoformat(),
                'destinatario_nombre': datos.destinatario_nombre,
                'destinatario_cargo': datos.destinatario_cargo,
                'mostrar_desglose': datos.mostrar_desglose,
                'representante_legal': representante_legal,
                'notas': datos.notas,
                'estatus': EstatusCotizacion.BORRADOR.value,
                'version': 1,
                'created_by': str(user_id) if user_id else None,
            }
            result = self.supabase.table('cotizaciones').insert(payload).execute()
            if not result.data:
                raise DatabaseError("No se pudo crear la cotización")
            return Cotizacion(**result.data[0])

        except (DatabaseError, NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error creando cotización: {e}")
            raise DatabaseError(f"Error creando cotización: {e}")

    async def obtener_por_id(self, cotizacion_id: int) -> Cotizacion:
        """
        Obtiene una cotización por ID.

        Raises:
            NotFoundError: Si no existe.
            DatabaseError: Si hay error de BD.
        """
        try:
            result = (
                self.supabase.table('cotizaciones')
                .select('*')
                .eq('id', cotizacion_id)
                .execute()
            )
            if not result.data:
                raise NotFoundError(f"Cotización {cotizacion_id} no encontrada")
            return Cotizacion(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo cotización {cotizacion_id}: {e}")
            raise DatabaseError(f"Error obteniendo cotización: {e}")

    async def obtener_por_empresa(
        self, empresa_id: int, incluir_historicas: bool = False
    ) -> list[CotizacionResumen]:
        """
        Lista cotizaciones de una empresa, enriquecidas con nombre de empresa
        y cantidad de partidas.

        Args:
            empresa_id: ID de la empresa.
            incluir_historicas: Si False, excluye cotizaciones RECHAZADAS antiguas.

        Returns:
            Lista de CotizacionResumen ordenada por fecha_creacion desc.
        """
        try:
            query = (
                self.supabase.table('cotizaciones')
                .select('*, empresas(nombre_comercial), cotizacion_partidas(id)')
                .eq('empresa_id', empresa_id)
                .order('fecha_creacion', desc=True)
            )
            result = query.execute()
            rows = result.data or []
            if not incluir_historicas:
                rows = self._filtrar_cotizaciones_historicas(rows)

            cotizaciones = []
            for row in rows:
                empresa_data = row.pop('empresas', {}) or {}
                nombre_empresa = empresa_data.get('nombre_comercial', '')
                cantidad_partidas = len(row.pop('cotizacion_partidas', []) or [])

                resumen = CotizacionResumen(
                    **row,
                    nombre_empresa=nombre_empresa,
                    cantidad_partidas=cantidad_partidas,
                )
                cotizaciones.append(resumen)

            return cotizaciones

        except Exception as e:
            logger.error(f"Error listando cotizaciones empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error listando cotizaciones: {e}")

    async def actualizar(
        self, cotizacion_id: int, datos: CotizacionUpdate
    ) -> Cotizacion:
        """
        Actualiza una cotización.

        Solo se permite editar cuando estatus == BORRADOR.

        Raises:
            BusinessRuleError: Si la cotización no está en BORRADOR.
            NotFoundError: Si no existe.
            DatabaseError: Si hay error de BD.
        """
        cotizacion = await self.obtener_por_id(cotizacion_id)
        if cotizacion.estatus != EstatusCotizacion.BORRADOR:
            raise BusinessRuleError(
                f"No se puede editar una cotización en estatus '{cotizacion.estatus}'. "
                "Solo se permite editar en estado BORRADOR."
            )

        try:
            payload = datos.model_dump(mode='json', exclude_none=True)
            if not payload:
                return cotizacion

            result = (
                self.supabase.table('cotizaciones')
                .update(payload)
                .eq('id', cotizacion_id)
                .execute()
            )
            if not result.data:
                raise DatabaseError("No se pudo actualizar la cotización")
            return Cotizacion(**result.data[0])

        except (BusinessRuleError, NotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando cotización {cotizacion_id}: {e}")
            raise DatabaseError(f"Error actualizando cotización: {e}")

    async def cambiar_estatus(
        self, cotizacion_id: int, nuevo_estatus: EstatusCotizacion
    ) -> Cotizacion:
        """
        Cambia el estatus de una cotización.

        Valida transiciones permitidas.

        Raises:
            BusinessRuleError: Si la transición no está permitida.
            NotFoundError: Si no existe.
            DatabaseError: Si hay error de BD.
        """
        cotizacion = await self.obtener_por_id(cotizacion_id)
        estatus_actual = EstatusCotizacion(cotizacion.estatus)
        transiciones = _TRANSICIONES_COTIZACION.get(estatus_actual, set())

        if nuevo_estatus not in transiciones:
            raise BusinessRuleError(
                f"Transición no permitida: {estatus_actual.value} → {nuevo_estatus.value}. "
                f"Transiciones válidas: {[t.value for t in transiciones] or 'ninguna'}"
            )

        try:
            result = (
                self.supabase.table('cotizaciones')
                .update({'estatus': nuevo_estatus.value})
                .eq('id', cotizacion_id)
                .execute()
            )
            if not result.data:
                raise DatabaseError("No se pudo cambiar el estatus")
            return Cotizacion(**result.data[0])

        except (BusinessRuleError, NotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error cambiando estatus cotización {cotizacion_id}: {e}")
            raise DatabaseError(f"Error cambiando estatus: {e}")

    # =========================================================================
    # PARTIDAS
    # =========================================================================

    async def agregar_partida(self, cotizacion_id: int) -> CotizacionPartida:
        """
        Agrega una nueva partida a la cotización.

        Auto-asigna numero_partida incremental.

        Raises:
            BusinessRuleError: Si la cotización no es editable.
            NotFoundError: Si la cotización no existe.
            DatabaseError: Si hay error de BD.
        """
        cotizacion = await self.obtener_por_id(cotizacion_id)
        if cotizacion.estatus != EstatusCotizacion.BORRADOR:
            raise BusinessRuleError("Solo se pueden agregar partidas a cotizaciones en BORRADOR")

        try:
            # Calcular siguiente número
            result = (
                self.supabase.table('cotizacion_partidas')
                .select('numero_partida')
                .eq('cotizacion_id', cotizacion_id)
                .order('numero_partida', desc=True)
                .limit(1)
                .execute()
            )
            siguiente = 1
            if result.data:
                siguiente = result.data[0]['numero_partida'] + 1

            payload = {
                'cotizacion_id': cotizacion_id,
                'numero_partida': siguiente,
                'estatus_partida': EstatusPartidaCotizacion.PENDIENTE.value,
            }
            insert_result = (
                self.supabase.table('cotizacion_partidas')
                .insert(payload)
                .execute()
            )
            if not insert_result.data:
                raise DatabaseError("No se pudo agregar la partida")
            return CotizacionPartida(**insert_result.data[0])

        except (BusinessRuleError, NotFoundError, DatabaseError):
            raise
        except Exception as e:
            logger.error(f"Error agregando partida a cotización {cotizacion_id}: {e}")
            raise DatabaseError(f"Error agregando partida: {e}")

    async def obtener_partidas(self, cotizacion_id: int) -> list[CotizacionPartidaResumen]:
        """Lista partidas de una cotización con totales calculados."""
        try:
            result = (
                self.supabase.table('cotizacion_partidas')
                .select('*')
                .eq('cotizacion_id', cotizacion_id)
                .order('numero_partida')
                .execute()
            )
            partidas = []
            for row in (result.data or []):
                totales = await self._calcular_totales_partida_dict(row['id'])
                resumen = CotizacionPartidaResumen(**row, **totales)
                partidas.append(resumen)
            return partidas

        except Exception as e:
            logger.error(f"Error listando partidas cotización {cotizacion_id}: {e}")
            raise DatabaseError(f"Error listando partidas: {e}")

    async def eliminar_partida(self, partida_id: int) -> None:
        """
        Elimina una partida. CASCADE elimina categorías, conceptos y valores.

        Raises:
            BusinessRuleError: Si la partida fue convertida.
            NotFoundError: Si no existe.
            DatabaseError: Si hay error de BD.
        """
        partida = await self._obtener_partida(partida_id)
        if partida['estatus_partida'] == EstatusPartidaCotizacion.CONVERTIDA.value:
            raise BusinessRuleError("No se puede eliminar una partida ya convertida a contrato")

        try:
            self.supabase.table('cotizacion_partidas').delete().eq('id', partida_id).execute()
        except Exception as e:
            logger.error(f"Error eliminando partida {partida_id}: {e}")
            raise DatabaseError(f"Error eliminando partida: {e}")

    async def cambiar_estatus_partida(
        self, partida_id: int, estatus: EstatusPartidaCotizacion
    ) -> CotizacionPartida:
        """Cambia el estatus de una partida."""
        try:
            result = (
                self.supabase.table('cotizacion_partidas')
                .update({'estatus_partida': estatus.value})
                .eq('id', partida_id)
                .execute()
            )
            if not result.data:
                raise NotFoundError(f"Partida {partida_id} no encontrada")
            return CotizacionPartida(**result.data[0])
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error cambiando estatus partida {partida_id}: {e}")
            raise DatabaseError(f"Error cambiando estatus partida: {e}")

    # =========================================================================
    # CATEGORÍAS POR PARTIDA
    # =========================================================================

    async def agregar_categoria(
        self, datos: CotizacionPartidaCategoriaCreate
    ) -> CotizacionPartidaCategoria:
        """
        Agrega una categoría a una partida.

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            await self._asegurar_partida_editable(datos.partida_id)
            payload = datos.model_dump(mode='json')
            result = (
                self.supabase.table('cotizacion_partida_categorias')
                .insert(payload)
                .execute()
            )
            if not result.data:
                raise DatabaseError("No se pudo agregar la categoría")
            return CotizacionPartidaCategoria(**result.data[0])
        except BusinessRuleError:
            raise
        except Exception as e:
            logger.error(f"Error agregando categoría: {e}")
            raise DatabaseError(f"Error agregando categoría: {e}")

    async def eliminar_categoria(self, partida_categoria_id: int) -> None:
        """Elimina una categoría. CASCADE elimina sus valores en la matriz."""
        try:
            await self._asegurar_categoria_editable(partida_categoria_id)
            self.supabase.table('cotizacion_partida_categorias').delete().eq('id', partida_categoria_id).execute()
        except BusinessRuleError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando categoría {partida_categoria_id}: {e}")
            raise DatabaseError(f"Error eliminando categoría: {e}")

    async def actualizar_categoria(
        self, partida_categoria_id: int, datos: dict
    ) -> CotizacionPartidaCategoria:
        """Actualiza campos de una categoría."""
        try:
            await self._asegurar_categoria_editable(partida_categoria_id)
            result = (
                self.supabase.table('cotizacion_partida_categorias')
                .update(datos)
                .eq('id', partida_categoria_id)
                .execute()
            )
            if not result.data:
                raise NotFoundError(f"Categoría {partida_categoria_id} no encontrada")
            return CotizacionPartidaCategoria(**result.data[0])
        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando categoría {partida_categoria_id}: {e}")
            raise DatabaseError(f"Error actualizando categoría: {e}")

    async def obtener_categorias_partida(
        self, partida_id: int
    ) -> list[CotizacionPartidaCategoriaResumen]:
        """Lista categorías de una partida con datos enriquecidos."""
        try:
            result = (
                self.supabase.table('cotizacion_partida_categorias')
                .select('*, categorias_puesto(clave, nombre)')
                .eq('partida_id', partida_id)
                .order('id')
                .execute()
            )
            categorias = []
            for row in (result.data or []):
                cat_data = row.pop('categorias_puesto', {}) or {}
                resumen = CotizacionPartidaCategoriaResumen(
                    **row,
                    categoria_clave=cat_data.get('clave', ''),
                    categoria_nombre=cat_data.get('nombre', ''),
                    costo_patronal_efectivo=(
                        row.get('costo_patronal_editado')
                        if row.get('fue_editado_manualmente')
                        and row.get('costo_patronal_editado') is not None
                        else row.get('costo_patronal_calculado', 0)
                    ),
                )
                categorias.append(resumen)
            return categorias
        except Exception as e:
            logger.error(f"Error listando categorías partida {partida_id}: {e}")
            raise DatabaseError(f"Error listando categorías: {e}")

    # =========================================================================
    # CONCEPTOS
    # =========================================================================

    async def agregar_concepto(
        self, datos: CotizacionConceptoCreate
    ) -> CotizacionConcepto:
        """
        Agrega un concepto (fila) a la matriz de una partida.

        Auto-asigna orden incremental a partir de 10 (PATRONAL ocupa 1-9).

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            await self._asegurar_partida_editable(datos.partida_id)
            # Calcular siguiente orden (solo para INDIRECTO del usuario)
            result = (
                self.supabase.table('cotizacion_conceptos')
                .select('orden')
                .eq('partida_id', datos.partida_id)
                .eq('tipo_concepto', TipoConceptoCotizacion.INDIRECTO.value)
                .order('orden', desc=True)
                .limit(1)
                .execute()
            )
            siguiente_orden = 10
            if result.data:
                siguiente_orden = result.data[0]['orden'] + 1

            payload = {
                'partida_id': datos.partida_id,
                'nombre': datos.nombre,
                'tipo_concepto': datos.tipo_concepto.value if hasattr(datos.tipo_concepto, 'value') else datos.tipo_concepto,
                'tipo_valor': datos.tipo_valor.value if hasattr(datos.tipo_valor, 'value') else datos.tipo_valor,
                'orden': siguiente_orden,
                'es_autogenerado': datos.es_autogenerado,
            }
            insert_result = (
                self.supabase.table('cotizacion_conceptos')
                .insert(payload)
                .execute()
            )
            if not insert_result.data:
                raise DatabaseError("No se pudo agregar el concepto")
            return CotizacionConcepto(**insert_result.data[0])

        except (DatabaseError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error agregando concepto: {e}")
            raise DatabaseError(f"Error agregando concepto: {e}")

    async def eliminar_concepto(self, concepto_id: int) -> None:
        """Elimina un concepto. CASCADE elimina sus valores en la matriz."""
        try:
            await self._asegurar_concepto_editable(concepto_id)
            self.supabase.table('cotizacion_conceptos').delete().eq('id', concepto_id).execute()
        except BusinessRuleError:
            raise
        except Exception as e:
            logger.error(f"Error eliminando concepto {concepto_id}: {e}")
            raise DatabaseError(f"Error eliminando concepto: {e}")

    async def obtener_conceptos_partida(self, partida_id: int) -> list[CotizacionConcepto]:
        """Lista conceptos de una partida ordenados por orden."""
        try:
            result = (
                self.supabase.table('cotizacion_conceptos')
                .select('*')
                .eq('partida_id', partida_id)
                .order('orden')
                .execute()
            )
            return [CotizacionConcepto(**row) for row in (result.data or [])]
        except Exception as e:
            logger.error(f"Error listando conceptos partida {partida_id}: {e}")
            raise DatabaseError(f"Error listando conceptos: {e}")

    # =========================================================================
    # VALORES DE MATRIZ
    # =========================================================================

    async def actualizar_valor_concepto(
        self,
        concepto_id: int,
        partida_categoria_id: int,
        valor_pesos: Decimal,
    ) -> CotizacionConceptoValor:
        """
        Crea o actualiza el valor de una celda en la matriz.

        Raises:
            DatabaseError: Si hay error de BD.
        """
        try:
            await self._asegurar_categoria_editable(partida_categoria_id)
            # Verificar si ya existe
            existing = (
                self.supabase.table('cotizacion_concepto_valores')
                .select('id')
                .eq('concepto_id', concepto_id)
                .eq('partida_categoria_id', partida_categoria_id)
                .execute()
            )

            payload = {
                'concepto_id': concepto_id,
                'partida_categoria_id': partida_categoria_id,
                'valor_pesos': float(valor_pesos),
            }

            if existing.data:
                result = (
                    self.supabase.table('cotizacion_concepto_valores')
                    .update({'valor_pesos': float(valor_pesos)})
                    .eq('concepto_id', concepto_id)
                    .eq('partida_categoria_id', partida_categoria_id)
                    .execute()
                )
            else:
                result = (
                    self.supabase.table('cotizacion_concepto_valores')
                    .insert(payload)
                    .execute()
                )

            if not result.data:
                raise DatabaseError("No se pudo guardar el valor")
            return CotizacionConceptoValor(**result.data[0])

        except (DatabaseError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error actualizando valor concepto {concepto_id}: {e}")
            raise DatabaseError(f"Error actualizando valor: {e}")

    async def obtener_valores_partida(self, partida_id: int) -> list[dict]:
        """
        Retorna la matriz aplanada de valores para una partida.

        Returns:
            Lista de dicts con {concepto_id, partida_categoria_id, valor_pesos}.
        """
        try:
            result = (
                self.supabase.table('cotizacion_concepto_valores')
                .select(
                    'concepto_id, partida_categoria_id, valor_pesos, '
                    'cotizacion_conceptos!inner(partida_id, nombre, tipo_concepto, orden)'
                )
                .eq('cotizacion_conceptos.partida_id', partida_id)
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error(f"Error obteniendo matriz partida {partida_id}: {e}")
            raise DatabaseError(f"Error obteniendo matriz: {e}")

    # =========================================================================
    # CÁLCULO PATRONAL
    # =========================================================================

    async def calcular_costo_patronal(
        self, partida_categoria_id: int, empresa_id: int
    ) -> dict:
        """
        Ejecuta el motor CalculadoraCostoPatronal para una categoría.

        1. Obtiene ConfiguracionFiscalEmpresa de la empresa.
        2. Crea Trabajador con el salario_base_mensual.
        3. Ejecuta CalculadoraCostoPatronal.calcular().
        4. Genera las filas PATRONAL en cotizacion_conceptos (reemplaza existentes).
        5. Guarda costo_patronal_calculado en la categoría.
        6. Llama a recalcular_precio_unitario.

        Returns:
            dict con el ResultadoCuotas serializado.

        Raises:
            NotFoundError: Si la categoría o config no existe.
            DatabaseError: Si hay error de BD.
        """
        from app.core.calculations.simulador_costo_patronal import CalculadoraCostoPatronal
        from app.entities.costo_patronal import Trabajador
        from app.services.configuracion_fiscal_service import configuracion_fiscal_service

        try:
            await self._asegurar_categoria_editable(partida_categoria_id)
            # Obtener categoría con datos
            cat_result = (
                self.supabase.table('cotizacion_partida_categorias')
                .select('*, cotizacion_partidas!inner(cotizacion_id)')
                .eq('id', partida_categoria_id)
                .single()
                .execute()
            )
            if not cat_result.data:
                raise NotFoundError(f"Categoría {partida_categoria_id} no encontrada")

            categoria = cat_result.data
            salario_mensual = float(categoria['salario_base_mensual'])
            salario_diario = salario_mensual / 30.4

            # Obtener nombre empresa
            empresa_result = (
                self.supabase.table('empresas')
                .select('nombre_comercial')
                .eq('id', empresa_id)
                .single()
                .execute()
            )
            nombre_empresa = empresa_result.data.get('nombre_comercial', '') if empresa_result.data else ''

            # Configuración fiscal
            config_fiscal = await configuracion_fiscal_service.obtener_o_crear_default(empresa_id)
            config_empresa = config_fiscal.to_config_empresa(nombre_empresa)

            # Calcular
            calculadora = CalculadoraCostoPatronal(config_empresa)
            trabajador = Trabajador(
                nombre='Trabajador',
                salario_diario=salario_diario,
                antiguedad_anos=1,
            )
            resultado = calculadora.calcular(trabajador)

            # Guardar costo patronal calculado en la categoría
            costo_total = float(resultado.costo_total)
            self.supabase.table('cotizacion_partida_categorias').update({
                'costo_patronal_calculado': costo_total,
                'fue_editado_manualmente': False,
                'costo_patronal_editado': None,
            }).eq('id', partida_categoria_id).execute()

            # Regenerar filas PATRONAL para esta partida
            partida_id = categoria['partida_id']
            await self._regenerar_conceptos_patronales(
                partida_id, partida_categoria_id, resultado
            )

            # Recalcular precio unitario
            await self.recalcular_precio_unitario(partida_categoria_id)

            return {
                'salario_mensual': resultado.salario_mensual,
                'costo_total': resultado.costo_total,
                'factor_costo': resultado.factor_costo,
                'total_imss_patronal': resultado.total_imss_patronal,
                'infonavit': resultado.infonavit,
                'isn': resultado.isn,
                'provision_aguinaldo': resultado.provision_aguinaldo,
                'provision_vacaciones': resultado.provision_vacaciones,
                'provision_prima_vac': resultado.provision_prima_vac,
                'isr_a_retener': resultado.isr_a_retener,
                'imss_obrero_absorbido': resultado.imss_obrero_absorbido,
            }

        except (NotFoundError, DatabaseError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error calculando costo patronal {partida_categoria_id}: {e}")
            raise DatabaseError(f"Error en cálculo patronal: {e}")

    async def recalcular_precio_unitario(self, partida_categoria_id: int) -> Decimal:
        """
        Recalcula precio_unitario_final como la suma de todos los valores
        de esa columna en la matriz.

        Returns:
            Nuevo precio_unitario_final.
        """
        try:
            categoria = await self._obtener_categoria_partida_dict(partida_categoria_id)
            result = (
                self.supabase.table('cotizacion_concepto_valores')
                .select('valor_pesos, cotizacion_conceptos!inner(tipo_concepto)')
                .eq('partida_categoria_id', partida_categoria_id)
                .execute()
            )
            total_indirecto = Decimal('0')
            total_patronal = Decimal('0')
            for row in (result.data or []):
                valor = row.get('valor_pesos')
                if valor is None:
                    continue
                total_valor = Decimal(str(valor))
                concepto = row.get('cotizacion_conceptos') or {}
                if concepto.get('tipo_concepto') == TipoConceptoCotizacion.INDIRECTO.value:
                    total_indirecto += total_valor
                else:
                    total_patronal += total_valor

            if categoria.get('fue_editado_manualmente') and categoria.get('costo_patronal_editado') is not None:
                total_patronal = Decimal(str(categoria['costo_patronal_editado']))

            total = total_patronal + total_indirecto

            self.supabase.table('cotizacion_partida_categorias').update({
                'precio_unitario_final': float(total),
            }).eq('id', partida_categoria_id).execute()

            return total

        except Exception as e:
            logger.error(f"Error recalculando precio unitario {partida_categoria_id}: {e}")
            raise DatabaseError(f"Error recalculando precio unitario: {e}")

    async def recalcular_totales_partida(self, partida_id: int) -> dict:
        """
        Recalcula los totales de una partida: subtotal, IVA (16%), total.

        Los montos son mínimo (cant_min × precio_unitario × meses) y
        máximo (cant_max × precio_unitario × meses).

        Returns:
            dict con subtotal_min, subtotal_max, iva_min, iva_max, total_min, total_max.
        """
        try:
            # Obtener cotizacion para meses
            partida_result = (
                self.supabase.table('cotizacion_partidas')
                .select('cotizacion_id')
                .eq('id', partida_id)
                .single()
                .execute()
            )
            cotizacion_id = partida_result.data['cotizacion_id']
            cotizacion = await self.obtener_por_id(cotizacion_id)
            meses = cotizacion.meses_periodo or 1

            # Obtener categorías
            cats_result = (
                self.supabase.table('cotizacion_partida_categorias')
                .select('cantidad_minima, cantidad_maxima, precio_unitario_final')
                .eq('partida_id', partida_id)
                .execute()
            )

            subtotal_min = Decimal('0')
            subtotal_max = Decimal('0')
            for cat in (cats_result.data or []):
                precio = Decimal(str(cat['precio_unitario_final'] or 0))
                subtotal_min += Decimal(str(cat['cantidad_minima'])) * precio * meses
                subtotal_max += Decimal(str(cat['cantidad_maxima'])) * precio * meses

            iva_rate = Decimal('0.16')
            iva_min = subtotal_min * iva_rate
            iva_max = subtotal_max * iva_rate
            total_min = subtotal_min + iva_min
            total_max = subtotal_max + iva_max

            return {
                'subtotal_minimo': float(subtotal_min),
                'subtotal_maximo': float(subtotal_max),
                'iva_minimo': float(iva_min),
                'iva_maximo': float(iva_max),
                'total_minimo': float(total_min),
                'total_maximo': float(total_max),
                'meses_periodo': meses,
            }

        except Exception as e:
            logger.error(f"Error calculando totales partida {partida_id}: {e}")
            raise DatabaseError(f"Error calculando totales: {e}")

    # =========================================================================
    # VERSIONAMIENTO
    # =========================================================================

    async def crear_version(self, cotizacion_id: int) -> Cotizacion:
        """
        Crea una nueva versión de una cotización duplicando su estructura completa.

        Duplica: cotización → partidas → categorías → conceptos → valores.
        Incrementa version, apunta cotizacion_origen_id.

        Returns:
            Nueva Cotizacion con version + 1.
        """
        cotizacion = await self.obtener_por_id(cotizacion_id)

        try:
            nueva_version = cotizacion.version + 1
            codigo_base = cotizacion.codigo.rsplit('-v', 1)[0] if '-v' in cotizacion.codigo else cotizacion.codigo
            nuevo_codigo = f"{codigo_base}-v{nueva_version}"

            # Crear nueva cotización
            payload = {
                'codigo': nuevo_codigo,
                'empresa_id': cotizacion.empresa_id,
                'version': nueva_version,
                'cotizacion_origen_id': cotizacion_id,
                'destinatario_nombre': cotizacion.destinatario_nombre,
                'destinatario_cargo': cotizacion.destinatario_cargo,
                'fecha_inicio_periodo': cotizacion.fecha_inicio_periodo.isoformat() if isinstance(cotizacion.fecha_inicio_periodo, date) else cotizacion.fecha_inicio_periodo,
                'fecha_fin_periodo': cotizacion.fecha_fin_periodo.isoformat() if isinstance(cotizacion.fecha_fin_periodo, date) else cotizacion.fecha_fin_periodo,
                'mostrar_desglose': cotizacion.mostrar_desglose,
                'representante_legal': cotizacion.representante_legal,
                'notas': cotizacion.notas,
                'estatus': EstatusCotizacion.BORRADOR.value,
            }
            nueva_cot_result = (
                self.supabase.table('cotizaciones').insert(payload).execute()
            )
            if not nueva_cot_result.data:
                raise DatabaseError("No se pudo crear la nueva versión")

            nueva_cot_id = nueva_cot_result.data[0]['id']

            # Duplicar partidas
            partidas_result = (
                self.supabase.table('cotizacion_partidas')
                .select('*')
                .eq('cotizacion_id', cotizacion_id)
                .order('numero_partida')
                .execute()
            )
            for partida in (partidas_result.data or []):
                old_partida_id = partida['id']
                nueva_partida_result = (
                    self.supabase.table('cotizacion_partidas').insert({
                        'cotizacion_id': nueva_cot_id,
                        'numero_partida': partida['numero_partida'],
                        'estatus_partida': EstatusPartidaCotizacion.PENDIENTE.value,
                        'notas': partida.get('notas'),
                    }).execute()
                )
                if not nueva_partida_result.data:
                    continue
                nueva_partida_id = nueva_partida_result.data[0]['id']

                # Duplicar categorías
                cats_result = (
                    self.supabase.table('cotizacion_partida_categorias')
                    .select('*')
                    .eq('partida_id', old_partida_id)
                    .execute()
                )
                cat_id_map = {}  # old_id → new_id
                for cat in (cats_result.data or []):
                    old_cat_id = cat['id']
                    nueva_cat = (
                        self.supabase.table('cotizacion_partida_categorias').insert({
                            'partida_id': nueva_partida_id,
                            'categoria_puesto_id': cat['categoria_puesto_id'],
                            'cantidad_minima': cat['cantidad_minima'],
                            'cantidad_maxima': cat['cantidad_maxima'],
                            'salario_base_mensual': cat['salario_base_mensual'],
                            'costo_patronal_calculado': cat['costo_patronal_calculado'],
                            'precio_unitario_final': cat['precio_unitario_final'],
                        }).execute()
                    )
                    if nueva_cat.data:
                        cat_id_map[old_cat_id] = nueva_cat.data[0]['id']

                # Duplicar conceptos y valores
                conceptos_result = (
                    self.supabase.table('cotizacion_conceptos')
                    .select('*')
                    .eq('partida_id', old_partida_id)
                    .order('orden')
                    .execute()
                )
                for concepto in (conceptos_result.data or []):
                    old_concepto_id = concepto['id']
                    nuevo_concepto = (
                        self.supabase.table('cotizacion_conceptos').insert({
                            'partida_id': nueva_partida_id,
                            'nombre': concepto['nombre'],
                            'tipo_concepto': concepto['tipo_concepto'],
                            'tipo_valor': concepto['tipo_valor'],
                            'orden': concepto['orden'],
                            'es_autogenerado': concepto['es_autogenerado'],
                        }).execute()
                    )
                    if not nuevo_concepto.data:
                        continue
                    nuevo_concepto_id = nuevo_concepto.data[0]['id']

                    # Duplicar valores
                    valores_result = (
                        self.supabase.table('cotizacion_concepto_valores')
                        .select('*')
                        .eq('concepto_id', old_concepto_id)
                        .execute()
                    )
                    for valor in (valores_result.data or []):
                        new_cat_id = cat_id_map.get(valor['partida_categoria_id'])
                        if new_cat_id:
                            self.supabase.table('cotizacion_concepto_valores').insert({
                                'concepto_id': nuevo_concepto_id,
                                'partida_categoria_id': new_cat_id,
                                'valor_pesos': valor['valor_pesos'],
                            }).execute()

            return Cotizacion(**nueva_cot_result.data[0])

        except (DatabaseError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error creando versión de cotización {cotizacion_id}: {e}")
            raise DatabaseError(f"Error creando versión: {e}")

    # =========================================================================
    # CONVERSIÓN A CONTRATO
    # =========================================================================

    async def convertir_partida_a_contrato(self, partida_id: int) -> int:
        """
        Convierte una partida ACEPTADA a un contrato BORRADOR.

        1. Valida estatus_partida == ACEPTADA.
        2. Crea Contrato BORRADOR con datos de la cotización.
        3. Crea ContratoCategoria por cada categoría de la partida.
        4. Actualiza partida: contrato_id y estatus_partida = CONVERTIDA.

        Returns:
            ID del contrato creado.

        Raises:
            BusinessRuleError: Si la partida no está ACEPTADA.
            DatabaseError: Si hay error de BD.
        """
        partida_data = await self._obtener_partida(partida_id)
        if partida_data['estatus_partida'] != EstatusPartidaCotizacion.ACEPTADA.value:
            raise BusinessRuleError(
                f"La partida debe estar en estatus ACEPTADA para convertirse a contrato. "
                f"Estatus actual: {partida_data['estatus_partida']}"
            )

        cotizacion = await self.obtener_por_id(partida_data['cotizacion_id'])

        try:
            # Calcular totales para los montos del contrato
            totales = await self.recalcular_totales_partida(partida_id)

            empresa_result = (
                self.supabase.table('empresas')
                .select('codigo_corto')
                .eq('id', cotizacion.empresa_id)
                .single()
                .execute()
            )
            empresa_codigo = ((empresa_result.data or {}).get('codigo_corto') or '').strip().upper()
            if not empresa_codigo:
                raise BusinessRuleError(
                    "La empresa no tiene codigo_corto configurado para convertir la partida"
                )

            clave_origen = (cotizacion.codigo or '').split('-', 1)[0].strip().upper()
            if not clave_origen:
                raise BusinessRuleError(
                    f"La cotización {cotizacion.id} no tiene un código válido para convertir a contrato"
                )

            from app.services.contrato_service import contrato_service
            codigo_contrato = await contrato_service.generar_codigo_contrato(
                empresa_codigo,
                clave_origen,
                cotizacion.fecha_inicio_periodo.year,
            )

            # Crear contrato
            contrato_payload = {
                'empresa_id': cotizacion.empresa_id,
                'codigo': codigo_contrato,
                'estatus': EstatusContrato.BORRADOR.value,
                'tipo_contrato': TipoContrato.SERVICIOS.value,
                'tipo_duracion': 'TIEMPO_DETERMINADO',
                'fecha_inicio': cotizacion.fecha_inicio_periodo.isoformat() if isinstance(cotizacion.fecha_inicio_periodo, date) else cotizacion.fecha_inicio_periodo,
                'fecha_fin': cotizacion.fecha_fin_periodo.isoformat() if isinstance(cotizacion.fecha_fin_periodo, date) else cotizacion.fecha_fin_periodo,
                'monto_minimo': totales['total_minimo'],
                'monto_maximo': totales['total_maximo'],
                'incluye_iva': True,
                'descripcion_objeto': cotizacion.notas,
                'notas': f"Generado desde cotización {cotizacion.codigo}, partida {partida_data['numero_partida']}",
            }
            contrato_result = (
                self.supabase.table('contratos')
                .insert(contrato_payload)
                .execute()
            )
            if not contrato_result.data:
                raise DatabaseError("No se pudo crear el contrato")

            contrato_id = contrato_result.data[0]['id']

            # Crear ContratoCategoria por cada categoría
            cats = await self.obtener_categorias_partida(partida_id)
            for cat in cats:
                self.supabase.table('contrato_categorias').insert({
                    'contrato_id': contrato_id,
                    'categoria_puesto_id': cat.categoria_puesto_id,
                    'cantidad_minima': cat.cantidad_minima,
                    'cantidad_maxima': cat.cantidad_maxima,
                    'costo_unitario': float(cat.precio_unitario_final),
                }).execute()

            # Actualizar partida
            self.supabase.table('cotizacion_partidas').update({
                'contrato_id': contrato_id,
                'estatus_partida': EstatusPartidaCotizacion.CONVERTIDA.value,
            }).eq('id', partida_id).execute()

            return contrato_id

        except (DatabaseError, BusinessRuleError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error convirtiendo partida {partida_id} a contrato: {e}")
            raise DatabaseError(f"Error en conversión: {e}")

    # =========================================================================
    # HELPERS PRIVADOS
    # =========================================================================

    async def _generar_codigo(self, empresa_codigo: str) -> str:
        """Genera código COT-[EMPRESA]-[AÑO][SEQ]. Ej: COT-MAN-26001."""
        year_suffix = str(date.today().year)[-2:]
        prefix = f"COT-{empresa_codigo.upper()}-{year_suffix}"

        result = (
            self.supabase.table('cotizaciones')
            .select('codigo')
            .ilike('codigo', f"{prefix}%")
            .order('codigo', desc=True)
            .limit(1)
            .execute()
        )

        siguiente = 1
        if result.data:
            last_code = result.data[0]['codigo']
            # Extraer el número del final
            try:
                num_str = last_code.replace(prefix, '').lstrip('-').split('-')[0]
                siguiente = int(num_str) + 1
            except (ValueError, IndexError):
                siguiente = 1

        return f"{prefix}{siguiente:03d}"

    def _filtrar_cotizaciones_historicas(self, rows: list[dict]) -> list[dict]:
        """Oculta versiones rechazadas que no son la más reciente por código base."""
        ultima_por_base: dict[str, int] = {}
        for idx, row in enumerate(rows):
            codigo_base = (row.get('codigo') or '').rsplit('-v', 1)[0]
            ultima_por_base.setdefault(codigo_base, idx)

        filtradas = []
        for idx, row in enumerate(rows):
            codigo_base = (row.get('codigo') or '').rsplit('-v', 1)[0]
            es_rechazada = row.get('estatus') == EstatusCotizacion.RECHAZADA.value
            if es_rechazada and ultima_por_base.get(codigo_base) != idx:
                continue
            filtradas.append(row)
        return filtradas

    async def _obtener_partida(self, partida_id: int) -> dict:
        """Obtiene una partida como dict crudo."""
        result = (
            self.supabase.table('cotizacion_partidas')
            .select('*')
            .eq('id', partida_id)
            .execute()
        )
        if not result.data:
            raise NotFoundError(f"Partida {partida_id} no encontrada")
        return result.data[0]

    async def _obtener_categoria_partida_dict(self, partida_categoria_id: int) -> dict:
        result = (
            self.supabase.table('cotizacion_partida_categorias')
            .select('*')
            .eq('id', partida_categoria_id)
            .single()
            .execute()
        )
        if not result.data:
            raise NotFoundError(f"Categoría {partida_categoria_id} no encontrada")
        return result.data

    async def _calcular_totales_partida_dict(self, partida_id: int) -> dict:
        """Calcula totales de una partida como dict para CotizacionPartidaResumen."""
        try:
            cats_result = (
                self.supabase.table('cotizacion_partida_categorias')
                .select('cantidad_minima, cantidad_maxima, precio_unitario_final')
                .eq('partida_id', partida_id)
                .execute()
            )

            # Obtener meses del período
            partida_result = (
                self.supabase.table('cotizacion_partidas')
                .select('cotizacion_id')
                .eq('id', partida_id)
                .single()
                .execute()
            )
            cotizacion_id = partida_result.data['cotizacion_id'] if partida_result.data else None
            meses = 1
            if cotizacion_id:
                cot = await self.obtener_por_id(cotizacion_id)
                meses = cot.meses_periodo or 1

            cantidad_categorias = len(cats_result.data or [])
            cantidad_min = sum(c['cantidad_minima'] for c in (cats_result.data or []))
            cantidad_max = sum(c['cantidad_maxima'] for c in (cats_result.data or []))

            subtotal_min = Decimal('0')
            subtotal_max = Decimal('0')
            for cat in (cats_result.data or []):
                precio = Decimal(str(cat['precio_unitario_final'] or 0))
                subtotal_min += Decimal(str(cat['cantidad_minima'])) * precio * meses
                subtotal_max += Decimal(str(cat['cantidad_maxima'])) * precio * meses

            iva_rate = Decimal('0.16')
            iva_min = subtotal_min * iva_rate
            iva_max = subtotal_max * iva_rate

            return {
                'cantidad_categorias': cantidad_categorias,
                'cantidad_personal_minima': cantidad_min,
                'cantidad_personal_maxima': cantidad_max,
                'subtotal_minimo': subtotal_min,
                'subtotal_maximo': subtotal_max,
                'iva_minimo': iva_min,
                'iva_maximo': iva_max,
                'total_minimo': subtotal_min + iva_min,
                'total_maximo': subtotal_max + iva_max,
            }
        except Exception:
            return {
                'cantidad_categorias': 0,
                'cantidad_personal_minima': 0,
                'cantidad_personal_maxima': 0,
                'subtotal_minimo': Decimal('0'),
                'subtotal_maximo': Decimal('0'),
                'iva_minimo': Decimal('0'),
                'iva_maximo': Decimal('0'),
                'total_minimo': Decimal('0'),
                'total_maximo': Decimal('0'),
            }

    async def _regenerar_conceptos_patronales(
        self,
        partida_id: int,
        partida_categoria_id: int,
        resultado,
    ) -> None:
        """
        Regenera las filas PATRONAL de la matriz para una categoría.

        Elimina filas autogeneradas existentes de esta categoría y crea nuevas
        con los valores del ResultadoCuotas.
        """
        # Obtener todos los conceptos PATRONAL autogenerados de la partida
        conceptos_result = (
            self.supabase.table('cotizacion_conceptos')
            .select('id, nombre, orden')
            .eq('partida_id', partida_id)
            .eq('tipo_concepto', TipoConceptoCotizacion.PATRONAL.value)
            .eq('es_autogenerado', True)
            .execute()
        )
        existing_conceptos = {c['orden']: c for c in (conceptos_result.data or [])}

        # Calcular valor de provision finiquito (prima_vac + vacaciones)
        provision_finiquito = resultado.provision_prima_vac + resultado.provision_vacaciones

        conceptos_a_crear = [
            (1,  'Sueldo mensual',                    resultado.salario_mensual),
            (2,  'Previsión mensual de aguinaldo',     resultado.provision_aguinaldo),
            (3,  'Previsión mensual de finiquito',     provision_finiquito),
            (4,  'Impuestos federales ISR',            resultado.isr_a_retener),
            (5,  'Cuotas IMSS',                        resultado.total_imss_patronal),
            (6,  'INFONAVIT',                          resultado.infonavit),
            (7,  'Impuesto sobre nómina',              resultado.isn),
        ]
        # Solo agregar Art. 36 si tiene valor
        if resultado.imss_obrero_absorbido > 0:
            conceptos_a_crear.append(
                (8, 'Retención de IMSS (Art. 36 LSS)', resultado.imss_obrero_absorbido)
            )

        ordenes_vigentes = {orden for orden, _, _ in conceptos_a_crear}
        for orden, concepto in existing_conceptos.items():
            if orden in ordenes_vigentes:
                continue
            self.supabase.table('cotizacion_concepto_valores').delete().eq(
                'concepto_id', concepto['id']
            ).eq('partida_categoria_id', partida_categoria_id).execute()
            valores_restantes = (
                self.supabase.table('cotizacion_concepto_valores')
                .select('id', count='exact')
                .eq('concepto_id', concepto['id'])
                .execute()
            )
            if not (valores_restantes.count or 0):
                self.supabase.table('cotizacion_conceptos').delete().eq(
                    'id', concepto['id']
                ).execute()

        for orden, nombre, valor in conceptos_a_crear:
            # Buscar o crear concepto
            if orden in existing_conceptos:
                concepto_id = existing_conceptos[orden]['id']
            else:
                nuevo_concepto = (
                    self.supabase.table('cotizacion_conceptos').insert({
                        'partida_id': partida_id,
                        'nombre': nombre,
                        'tipo_concepto': TipoConceptoCotizacion.PATRONAL.value,
                        'tipo_valor': TipoValorConcepto.FIJO.value,
                        'orden': orden,
                        'es_autogenerado': True,
                    }).execute()
                )
                if not nuevo_concepto.data:
                    continue
                concepto_id = nuevo_concepto.data[0]['id']

            # Upsert valor
            await self.actualizar_valor_concepto(
                concepto_id, partida_categoria_id, Decimal(str(round(valor, 2)))
            )

    async def _asegurar_partida_editable(self, partida_id: int) -> None:
        partida = await self._obtener_partida(partida_id)
        cotizacion = await self.obtener_por_id(partida['cotizacion_id'])
        if cotizacion.estatus not in _ESTATUS_COTIZACION_EDITABLE:
            raise BusinessRuleError(
                f"La cotización {cotizacion.codigo} no permite editar partidas en estatus "
                f"'{cotizacion.estatus}'"
            )

    async def _asegurar_categoria_editable(self, partida_categoria_id: int) -> None:
        categoria = await self._obtener_categoria_partida_dict(partida_categoria_id)
        await self._asegurar_partida_editable(categoria['partida_id'])

    async def _asegurar_concepto_editable(self, concepto_id: int) -> None:
        result = (
            self.supabase.table('cotizacion_conceptos')
            .select('partida_id')
            .eq('id', concepto_id)
            .single()
            .execute()
        )
        if not result.data:
            raise NotFoundError(f"Concepto {concepto_id} no encontrado")
        await self._asegurar_partida_editable(result.data['partida_id'])


cotizacion_service = CotizacionService()
