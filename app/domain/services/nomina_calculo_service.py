"""
Motor de cálculo de nómina.

Orquesta el cálculo completo por empleado: percepciones automáticas,
exenciones ISR, retención ISR, cuotas IMSS obreras y subsidio al empleo.

Integra:
- CatalogoConceptosNomina (reglas fiscales + calcular_exencion)
- CatalogoISR (tabla mensual Art. 96 + subsidio al empleo)
- CatalogoUMA (valor UMA vigente para exenciones)
- CalculadoraIMSS (cuotas obreras)

Patrón: Direct Access (sin repository).
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace
from typing import Optional

from app.database import db_manager
from app.domain.enums import (
    ModoCalculoAguinaldo,
    PeriodicidadNomina,
    ReglaCalculoQuincenal,
    TipoPeriodoNomina,
    TipoJornadaPlaza,
)
from app.core.exceptions import DatabaseError, NotFoundError, BusinessRuleError
from app.core.catalogs import (
    CatalogoConceptosNomina,
    CatalogoISR,
    ContextoFiscalNomina,
    PoliticaFiscalResolver,
)
from app.core.catalogs.sistema.tolerancias import Tolerancias
from app.core.calculations.calculadora_imss import CalculadoraIMSS
from app.domain.services.configuracion_operativa_service import configuracion_operativa_service
from app.domain.services.configuracion_fiscal_service import configuracion_fiscal_service

logger = logging.getLogger(__name__)

# Claves de conceptos que este motor genera automáticamente (origen=SISTEMA)
_CLAVES_SISTEMA = {
    'SUELDO', 'HORAS_EXTRA_DOBLES', 'HORAS_EXTRA_TRIPLES',
    'PRIMA_DOMINICAL', 'DESCUENTO_FALTAS', 'DESCUENTO_INCAPACIDAD',
    'ISR', 'IMSS_OBRERO', 'SUBSIDIO_EMPLEO', 'AGUINALDO',
}

# Factor por periodicidad para proyectar base gravable a mensual
_FACTOR_MENSUAL = {
    'SEMANAL': Decimal('4.333'),
    'QUINCENAL': Decimal('2'),
    'MENSUAL': Decimal('1'),
}


def _round2(value: Decimal) -> Decimal:
    """Redondea a 2 decimales (ROUND_HALF_UP = estándar contable)."""
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class NominaCalculoService:
    """
    Motor de cálculo de nómina.

    Calcula automáticamente los conceptos del sistema (sueldo, horas extra,
    prima dominical, faltas, ISR, IMSS obrero, subsidio). Los conceptos
    manuales (INFONAVIT, FONACOT, préstamos, bonos) son capturados por
    RRHH/Contabilidad en módulos separados y se respetan durante el cálculo.

    Regla crítica: solo borra y recalcula movimientos con
    origen='SISTEMA' y es_automatico=True. Los manuales nunca se tocan.
    """

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.calculadora_imss = CalculadoraIMSS()
        self._concepto_ids: dict[str, int] = {}   # cache clave → id en BD

    # =========================================================================
    # PÚBLICO PRINCIPAL
    # =========================================================================

    async def calcular_periodo(self, periodo_id: int) -> dict:
        """
        Orquestador: calcula la nómina completa de todos los empleados del período.

        Requisito: el período debe estar en EN_PROCESO_CONTABILIDAD.
        Calcula cada nómina individual, actualiza sus totales y luego
        actualiza los totales consolidados del período.

        Returns:
            Resumen: {empleados_calculados, total_percepciones,
                      total_deducciones, total_neto, errores: []}
        """
        periodo = await self._obtener_periodo(periodo_id)
        if periodo['estatus'] != 'EN_PROCESO_CONTABILIDAD':
            raise BusinessRuleError(
                f"El período debe estar en 'EN_PROCESO_CONTABILIDAD' para calcular. "
                f"Estatus actual: '{periodo['estatus']}'"
            )

        # Cargar mapa clave→id de conceptos en BD
        await self._cargar_concepto_ids()

        # Obtener todas las nóminas del período
        nominas = await self._obtener_nominas_del_periodo(periodo_id)
        if not nominas:
            raise BusinessRuleError(
                f"El período {periodo_id} no tiene empleados. "
                "Ejecute poblar_empleados primero."
            )

        resumen = {
            'empleados_calculados': 0,
            'total_percepciones': Decimal('0'),
            'total_deducciones': Decimal('0'),
            'total_neto': Decimal('0'),
            'listo_para_timbrar': True,
            'empleados_con_observaciones_fiscales': 0,
            'errores': [],
        }

        for nomina in nominas:
            try:
                totales = await self._calcular_nomina_empleado(nomina, periodo)
                resumen['empleados_calculados'] += 1
                resumen['total_percepciones'] += totales['total_percepciones']
                resumen['total_deducciones'] += totales['total_deducciones']
                resumen['total_neto'] += totales['total_neto']
                if totales.get('tiene_observaciones_fiscales'):
                    resumen['empleados_con_observaciones_fiscales'] += 1
                if not bool(totales.get('listo_para_timbrar', False)):
                    resumen['listo_para_timbrar'] = False
            except Exception as e:
                emp_id = nomina.get('empleado_id', '?')
                logger.error(f"Error calculando nómina empleado {emp_id}: {e}")
                resumen['errores'].append({'empleado_id': emp_id, 'error': str(e)})
                resumen['listo_para_timbrar'] = False

        # Actualizar totales consolidados del período
        try:
            self.supabase.table('periodos_nomina').update({
                'total_percepciones': str(_round2(resumen['total_percepciones'])),
                'total_deducciones': str(_round2(resumen['total_deducciones'])),
                'total_neto': str(_round2(resumen['total_neto'])),
                'total_empleados': resumen['empleados_calculados'],
                'estatus': 'CALCULADO',
                'listo_para_timbrar': resumen['listo_para_timbrar'],
                'total_empleados_con_observaciones_fiscales': (
                    resumen['empleados_con_observaciones_fiscales']
                ),
            }).eq('id', periodo_id).execute()
        except Exception as e:
            logger.error(f"Error actualizando totales período {periodo_id}: {e}")

        await self._reconsolidar_periodo(periodo_id, estatus='CALCULADO')

        # Convertir Decimals a float para serialización
        resumen['total_percepciones'] = float(_round2(resumen['total_percepciones']))
        resumen['total_deducciones'] = float(_round2(resumen['total_deducciones']))
        resumen['total_neto'] = float(_round2(resumen['total_neto']))

        logger.info(
            f"Período {periodo_id} calculado: {resumen['empleados_calculados']} empleados, "
            f"neto={resumen['total_neto']}, errores={len(resumen['errores'])}"
        )
        return resumen

    async def recalcular_empleado(self, nomina_empleado_id: int) -> dict:
        """
        Recalcula la nómina de un empleado específico.

        Borra SOLO los movimientos con origen='SISTEMA' y es_automatico=True,
        luego los recalcula. Los movimientos manuales (RRHH, Contabilidad)
        no se modifican.

        Returns:
            Totales actualizados del empleado.
        """
        await self._cargar_concepto_ids()

        # Obtener nomina_empleado
        nomina = await self._obtener_nomina_empleado(nomina_empleado_id)

        # Obtener período
        periodo = await self._obtener_periodo(nomina['periodo_id'])

        resultado = await self._calcular_nomina_empleado(nomina, periodo)
        await self._reconsolidar_periodo(nomina['periodo_id'], estatus='CALCULADO')
        return resultado

    async def guardar_override_aguinaldo(
        self,
        nomina_empleado_id: int,
        *,
        monto_bruto: Decimal,
        notas: Optional[str] = None,
    ) -> dict:
        """Guarda un ajuste manual de aguinaldo y recalcula el recibo."""
        nomina = await self._obtener_nomina_empleado(nomina_empleado_id)
        periodo = await self._obtener_periodo(nomina['periodo_id'])
        if self._normalizar_tipo_periodo(periodo.get('tipo_periodo')) != TipoPeriodoNomina.AGUINALDO.value:
            raise BusinessRuleError(
                "El ajuste manual solo aplica a corridas especiales de aguinaldo."
            )

        payload = {
            'modo_calculo_aguinaldo': ModoCalculoAguinaldo.MANUAL.value,
            'monto_aguinaldo_override': str(
                Decimal(str(monto_bruto)).quantize(
                    Decimal('0.01'),
                    rounding=ROUND_HALF_UP,
                )
            ),
            'notas_aguinaldo_override': str(notas or "").strip() or None,
        }
        self.supabase.table('nominas_empleado').update(payload).eq(
            'id',
            nomina_empleado_id,
        ).execute()
        return await self.recalcular_empleado(nomina_empleado_id)

    async def obtener_desglose(self, nomina_empleado_id: int) -> list[dict]:
        """
        Retorna el desglose de conceptos del recibo, con JOIN a conceptos_nomina.

        Ordenado por: tipo (PERCEPCION primero, luego OTRO_PAGO, luego DEDUCCION)
        y por orden_default del concepto.
        """
        try:
            result = (
                self.supabase.table('nomina_movimientos')
                .select('*, conceptos_nomina(clave, nombre, orden_default)')
                .eq('nomina_empleado_id', nomina_empleado_id)
                .execute()
            )
            items = []
            for r in (result.data or []):
                concepto = r.pop('conceptos_nomina', {}) or {}
                r['concepto_clave'] = concepto.get('clave', '')
                r['concepto_nombre'] = concepto.get('nombre', '')
                r['_orden'] = concepto.get('orden_default', 99)
                items.append(r)

            # Ordenar: percepciones → otros pagos → deducciones, luego por orden
            _orden_tipo = {'PERCEPCION': 0, 'OTRO_PAGO': 1, 'DEDUCCION': 2}
            items.sort(key=lambda x: (_orden_tipo.get(x['tipo'], 9), x['_orden']))
            for item in items:
                item.pop('_orden', None)
            return items
        except Exception as e:
            logger.error(f"Error obteniendo desglose nómina {nomina_empleado_id}: {e}")
            raise DatabaseError(f"Error obteniendo desglose de nómina: {e}")

    # =========================================================================
    # CÁLCULO INTERNO
    # =========================================================================

    @staticmethod
    def _normalizar_periodicidad(periodicidad: object) -> str:
        if isinstance(periodicidad, PeriodicidadNomina):
            return periodicidad.value
        return str(periodicidad or PeriodicidadNomina.QUINCENAL.value)

    @staticmethod
    def _normalizar_tipo_periodo(valor: object) -> str:
        if isinstance(valor, TipoPeriodoNomina):
            return valor.value
        try:
            return TipoPeriodoNomina(str(valor or "").upper()).value
        except ValueError:
            return TipoPeriodoNomina.ORDINARIA.value

    @staticmethod
    def _normalizar_regla_calculo_quincenal(valor: object) -> str:
        if isinstance(valor, ReglaCalculoQuincenal):
            return valor.value
        try:
            return ReglaCalculoQuincenal(str(valor or "").upper()).value
        except ValueError:
            return ReglaCalculoQuincenal.MIXTA.value

    async def _resolver_regla_calculo_quincenal_periodo(
        self,
        periodo: dict,
    ) -> Optional[str]:
        periodicidad = self._normalizar_periodicidad(periodo.get('periodicidad'))
        if periodicidad != PeriodicidadNomina.QUINCENAL.value:
            return None

        snapshot = periodo.get('regla_calculo_quincenal')
        if snapshot:
            regla = self._normalizar_regla_calculo_quincenal(snapshot)
            periodo['regla_calculo_quincenal'] = regla
            return regla

        empresa_id = periodo.get('empresa_id')
        regla = ReglaCalculoQuincenal.MIXTA.value
        if empresa_id:
            config = await configuracion_operativa_service.obtener_o_crear_default(
                int(empresa_id)
            )
            regla = self._normalizar_regla_calculo_quincenal(
                getattr(config, 'regla_calculo_quincenal', None)
            )

        periodo_id = periodo.get('id')
        if periodo_id:
            try:
                self.supabase.table('periodos_nomina').update({
                    'regla_calculo_quincenal': regla,
                }).eq('id', periodo_id).execute()
            except Exception as e:
                logger.error(
                    "Error persistiendo snapshot de regla quincenal en periodo %s: %s",
                    periodo_id,
                    e,
                )
                raise DatabaseError(
                    f"Error persistiendo regla de cálculo quincenal: {e}"
                )

        periodo['regla_calculo_quincenal'] = regla
        return regla

    @staticmethod
    def _normalizar_tipo_jornada(valor: object) -> str:
        if isinstance(valor, TipoJornadaPlaza):
            return valor.value
        try:
            return TipoJornadaPlaza(str(valor or "").upper()).value
        except ValueError:
            return TipoJornadaPlaza.COMPLETA.value

    @classmethod
    def _normalizar_factor_jornada(
        cls,
        valor: object,
        tipo_jornada: object,
    ) -> Decimal:
        tipo = cls._normalizar_tipo_jornada(tipo_jornada)
        default = Decimal("0.50") if tipo == TipoJornadaPlaza.MEDIA_JORNADA.value else Decimal("1.00")
        if valor in (None, ""):
            return default
        try:
            factor = Decimal(str(valor)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
        except Exception:
            return default
        if factor <= 0 or factor > 1:
            return default
        return factor

    @staticmethod
    def _observacion_fiscal(codigo: str, mensaje: str, severity: str) -> dict[str, str]:
        return {
            "codigo": codigo,
            "mensaje": mensaje,
            "severity": severity,
        }

    async def _resolver_contexto_fiscal_periodo(
        self,
        periodo: dict,
    ) -> tuple[ContextoFiscalNomina, bool]:
        fecha_fiscal = (
            periodo.get("fecha_pago")
            or periodo.get("fecha_fin")
        )
        if not fecha_fiscal:
            fecha_fiscal = self._obtener_periodo_hoy_iso()

        zona_frontera = periodo.get("zona_frontera")
        aplicar_art_36 = periodo.get("aplicar_art_36")
        if zona_frontera is None or aplicar_art_36 is None:
            config_fiscal = await self._obtener_configuracion_fiscal(
                int(periodo["empresa_id"])
            )
            zona_frontera = bool(getattr(config_fiscal, "zona_frontera", False))
            aplicar_art_36 = bool(getattr(config_fiscal, "aplicar_art_36", True))
            try:
                self.supabase.table("periodos_nomina").update(
                    {
                        "zona_frontera": zona_frontera,
                        "aplicar_art_36": aplicar_art_36,
                    }
                ).eq("id", int(periodo["id"])).execute()
            except Exception as exc:
                logger.warning(
                    "No se pudo persistir snapshot fiscal del periodo %s: %s",
                    periodo.get("id"),
                    exc,
                )
            periodo["zona_frontera"] = zona_frontera
            periodo["aplicar_art_36"] = aplicar_art_36

        contexto = PoliticaFiscalResolver.resolver(
            fecha_fiscal,
            zona_frontera=bool(zona_frontera),
        )
        return contexto, bool(aplicar_art_36)

    @staticmethod
    async def _obtener_configuracion_fiscal(empresa_id: int):
        try:
            return await configuracion_fiscal_service.obtener_o_crear_default(empresa_id)
        except Exception as exc:
            logger.warning(
                "Usando fallback de configuración fiscal para empresa %s: %s",
                empresa_id,
                exc,
            )
            return SimpleNamespace(zona_frontera=False, aplicar_art_36=True)

    @staticmethod
    def _calcular_isr_mensual_con_fecha(
        base_mensual: Decimal,
        fecha_referencia,
    ) -> Decimal:
        try:
            return CatalogoISR.calcular_isr_mensual(base_mensual, fecha_referencia)
        except TypeError:
            return CatalogoISR.calcular_isr_mensual(base_mensual)

    @staticmethod
    def _calcular_subsidio_periodo_aplicable(
        base_mensual: Decimal,
        isr_periodo: Decimal,
        fecha_referencia,
        *,
        dias_periodo: int,
        periodicidad: str,
    ) -> Decimal:
        if isr_periodo <= 0:
            return Decimal("0")
        try:
            subsidio_mensual = CatalogoISR.calcular_subsidio(
                base_mensual,
                fecha_referencia,
            )
        except TypeError:
            subsidio_mensual = CatalogoISR.calcular_subsidio(base_mensual)

        subsidio_mensual = Decimal(str(subsidio_mensual or 0))
        if subsidio_mensual <= 0:
            return Decimal("0")

        if periodicidad == PeriodicidadNomina.MENSUAL.value:
            subsidio_periodo = subsidio_mensual
        else:
            subsidio_periodo = (
                subsidio_mensual / Decimal("30.4") * Decimal(str(dias_periodo or 0))
            )

        return _round2(min(subsidio_periodo, subsidio_mensual, isr_periodo))

    @staticmethod
    def _decimal_movimiento(movimiento: dict, campo: str) -> Decimal:
        return Decimal(str(movimiento.get(campo) or 0))

    @classmethod
    def _sumar_base_gravable_isr(cls, *grupos_movimientos: list[dict]) -> Decimal:
        return _round2(
            sum(
                (
                    cls._decimal_movimiento(mov, "monto_gravable")
                    for movimientos in grupos_movimientos
                    for mov in movimientos
                    if mov.get("tipo") == "PERCEPCION"
                ),
                Decimal("0"),
            )
        )

    @classmethod
    def _tiene_percepciones_manuales(cls, movimientos: list[dict]) -> bool:
        return any(
            mov.get("tipo") == "PERCEPCION"
            and cls._decimal_movimiento(mov, "monto") > 0
            for mov in movimientos
        )

    @staticmethod
    def _obtener_periodo_hoy_iso() -> str:
        from datetime import date as _date

        return _date.today().isoformat()

    def _resolver_snapshot_fiscal_nomina(
        self,
        nomina: dict,
        contexto_fiscal: ContextoFiscalNomina,
    ) -> dict[str, object]:
        tipo_jornada = self._normalizar_tipo_jornada(nomina.get("tipo_jornada"))
        factor_jornada = self._normalizar_factor_jornada(
            nomina.get("factor_jornada"),
            tipo_jornada,
        )
        salario_diario = Decimal(str(nomina.get("salario_diario") or 0)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        salario_minimo_diario = Decimal(
            str(
                nomina.get("salario_minimo_diario_aplicable")
                or contexto_fiscal.salario_minimo_diario_aplicable
                or 0
            )
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        salario_minimo_proporcional = (
            salario_minimo_diario * factor_jornada
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        observaciones: list[dict[str, str]] = []
        for item in (nomina.get("observaciones_fiscales") or []):
            if isinstance(item, dict):
                observaciones.append(
                    {
                        "codigo": str(item.get("codigo") or "").strip(),
                        "mensaje": str(item.get("mensaje") or "").strip(),
                        "severity": str(item.get("severity") or "warning").strip().lower(),
                    }
                )

        if contexto_fiscal.mensaje_vigencia and not any(
            obs.get("codigo") == "CATALOGO_FISCAL_NO_VIGENTE" for obs in observaciones
        ):
            observaciones.append(
                self._observacion_fiscal(
                    "CATALOGO_FISCAL_NO_VIGENTE",
                    contexto_fiscal.mensaje_vigencia,
                    "error",
                )
            )

        if salario_diario < salario_minimo_proporcional and not Tolerancias.es_salario_minimo(
            salario_diario,
            salario_minimo_proporcional,
        ):
            if not any(
                obs.get("codigo") == "SALARIO_BAJO_MINIMO_PROPORCIONAL"
                for obs in observaciones
            ):
                observaciones.append(
                    self._observacion_fiscal(
                        "SALARIO_BAJO_MINIMO_PROPORCIONAL",
                        (
                            "El salario diario está por debajo del mínimo proporcional "
                            "para la jornada capturada."
                        ),
                        "warning",
                    )
                )

        es_salario_minimo_art36 = (
            tipo_jornada == TipoJornadaPlaza.COMPLETA.value
            and salario_minimo_diario > 0
            and Tolerancias.es_salario_minimo(salario_diario, salario_minimo_diario)
        )

        return {
            "tipo_jornada": tipo_jornada,
            "factor_jornada": factor_jornada,
            "salario_minimo_diario_aplicable": salario_minimo_diario,
            "es_salario_minimo_art36": es_salario_minimo_art36,
            "observaciones_fiscales": observaciones,
        }

    def _persistir_nomina_calculada(
        self,
        *,
        nomina_id: int,
        percepciones: Decimal,
        deducciones: Decimal,
        otros_pagos: Decimal,
        neto: Decimal,
        snapshot_fiscal: dict[str, object],
        observaciones_fiscales: list[dict[str, str]],
        listo_para_timbrar: bool,
        imss_obrero_absorbido: Decimal = Decimal("0"),
        extras_update: Optional[dict[str, object]] = None,
    ) -> dict:
        payload = {
            'total_percepciones': float(percepciones),
            'total_deducciones': float(deducciones),
            'total_otros_pagos': float(otros_pagos),
            'total_neto': float(max(neto, Decimal('0'))),
            'estatus': 'CALCULADO',
            'tipo_jornada': snapshot_fiscal["tipo_jornada"],
            'factor_jornada': float(snapshot_fiscal["factor_jornada"]),
            'salario_minimo_diario_aplicable': float(
                snapshot_fiscal["salario_minimo_diario_aplicable"]
            ),
            'es_salario_minimo_art36': snapshot_fiscal["es_salario_minimo_art36"],
            'imss_obrero_absorbido': float(_round2(Decimal(str(imss_obrero_absorbido or 0)))),
            'listo_para_timbrar': listo_para_timbrar,
            'observaciones_fiscales': observaciones_fiscales,
        }
        if extras_update:
            payload.update(extras_update)

        self.supabase.table('nominas_empleado').update(payload).eq('id', nomina_id).execute()

        return {
            'nomina_empleado_id': nomina_id,
            'total_percepciones': percepciones,
            'total_deducciones': deducciones,
            'total_otros_pagos': otros_pagos,
            'total_neto': max(neto, Decimal('0')),
            'listo_para_timbrar': listo_para_timbrar,
            'tiene_observaciones_fiscales': bool(observaciones_fiscales),
        }

    def _sumar_totales_con_movimientos(
        self,
        *,
        movimientos_sistema: list[dict],
        manuales: list[dict],
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        percepciones = sum(
            (
                Decimal(str(m['monto_gravable'])) + Decimal(str(m['monto_exento']))
                for m in movimientos_sistema
                if m['tipo'] == 'PERCEPCION'
            ),
            Decimal('0'),
        )
        percepciones += sum(
            (
                Decimal(str(m['monto']))
                for m in manuales
                if m['tipo'] == 'PERCEPCION'
            ),
            Decimal('0'),
        )

        deducciones = sum(
            (
                Decimal(str(m['monto']))
                for m in movimientos_sistema
                if m['tipo'] == 'DEDUCCION'
            ),
            Decimal('0'),
        )
        deducciones += sum(
            (
                Decimal(str(m['monto']))
                for m in manuales
                if m['tipo'] == 'DEDUCCION'
            ),
            Decimal('0'),
        )

        otros_pagos = sum(
            (
                Decimal(str(m['monto']))
                for m in movimientos_sistema
                if m['tipo'] == 'OTRO_PAGO'
            ),
            Decimal('0'),
        )
        otros_pagos += sum(
            (
                Decimal(str(m['monto']))
                for m in manuales
                if m['tipo'] == 'OTRO_PAGO'
            ),
            Decimal('0'),
        )

        percepciones = _round2(percepciones)
        deducciones = _round2(deducciones)
        otros_pagos = _round2(otros_pagos)
        neto = _round2(percepciones - deducciones + otros_pagos)
        return percepciones, deducciones, otros_pagos, neto

    async def _leer_movimientos_manuales(self, nomina_id: int) -> list[dict]:
        res_manual = (
            self.supabase.table('nomina_movimientos')
            .select('tipo, monto, monto_gravable, monto_exento, origen')
            .eq('nomina_empleado_id', nomina_id)
            .neq('origen', 'SISTEMA')
            .execute()
        )
        return res_manual.data or []

    async def _calcular_nomina_aguinaldo(
        self,
        *,
        nomina: dict,
        periodo: dict,
        contexto_fiscal: ContextoFiscalNomina,
        snapshot_fiscal: dict[str, object],
    ) -> dict:
        nomina_id = nomina['id']
        uma_diario = contexto_fiscal.uma_diaria
        try:
            modo = ModoCalculoAguinaldo(
                str(
                    nomina.get('modo_calculo_aguinaldo')
                    or ModoCalculoAguinaldo.AUTO.value
                ).upper()
            ).value
        except ValueError:
            modo = ModoCalculoAguinaldo.AUTO.value
        monto_bruto = Decimal(
            str(
                nomina.get('monto_aguinaldo_override')
                if modo == ModoCalculoAguinaldo.MANUAL.value
                and nomina.get('monto_aguinaldo_override') is not None
                else nomina.get('monto_aguinaldo_bruto') or 0
            )
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        movimientos_sistema: list[dict] = []
        if monto_bruto > 0:
            gravable, exento = self._calcular_exencion('AGUINALDO', monto_bruto, uma_diario)
            movimientos_sistema.append(
                self._mov(
                    nomina_id,
                    'AGUINALDO',
                    'PERCEPCION',
                    monto_bruto,
                    gravable,
                    exento,
                )
            )
        else:
            gravable = Decimal('0')

        # Aguinaldo es una corrida especial y no debe depender de la periodicidad
        # ordinaria configurada para la empresa.
        factor = Decimal('1')
        base_mensual = _round2(gravable * factor)
        isr_mensual = self._calcular_isr_mensual_con_fecha(
            base_mensual,
            contexto_fiscal.fecha_referencia,
        )
        subsidio_mensual_aplicable = Decimal("0")
        isr_periodo = _round2(isr_mensual / factor) if factor else Decimal('0')
        subsidio_periodo = _round2(subsidio_mensual_aplicable / factor) if factor else Decimal('0')

        if isr_periodo > 0:
            movimientos_sistema.append(
                self._mov(
                    nomina_id, 'ISR', 'DEDUCCION',
                    isr_periodo, Decimal('0'), Decimal('0')
                )
            )
        if subsidio_periodo > 0:
            movimientos_sistema.append(
                self._mov(
                    nomina_id, 'SUBSIDIO_EMPLEO', 'OTRO_PAGO',
                    subsidio_periodo, Decimal('0'), Decimal('0')
                )
            )

        if movimientos_sistema:
            registros_bd = [
                {k: float(v) if isinstance(v, Decimal) else v for k, v in m.items()}
                for m in movimientos_sistema
            ]
            self.supabase.table('nomina_movimientos').insert(registros_bd).execute()

        manuales = await self._leer_movimientos_manuales(nomina_id)
        percepciones, deducciones, otros_pagos, neto = self._sumar_totales_con_movimientos(
            movimientos_sistema=movimientos_sistema,
            manuales=manuales,
        )
        observaciones_fiscales = snapshot_fiscal["observaciones_fiscales"]
        listo_para_timbrar = not any(
            str(item.get("severity") or "").lower() == "error"
            for item in observaciones_fiscales
            if isinstance(item, dict)
        )
        return self._persistir_nomina_calculada(
            nomina_id=nomina_id,
            percepciones=percepciones,
            deducciones=deducciones,
            otros_pagos=otros_pagos,
            neto=neto,
            snapshot_fiscal=snapshot_fiscal,
            observaciones_fiscales=observaciones_fiscales,
            listo_para_timbrar=listo_para_timbrar,
            imss_obrero_absorbido=Decimal('0'),
            extras_update={
                'modo_calculo_aguinaldo': modo,
                'monto_aguinaldo_bruto': float(
                    Decimal(str(nomina.get('monto_aguinaldo_bruto') or 0)).quantize(
                        Decimal('0.01'),
                        rounding=ROUND_HALF_UP,
                    )
                ),
            },
        )

    async def _calcular_nomina_empleado(self, nomina: dict, periodo: dict) -> dict:
        """
        Flujo completo de cálculo para un empleado.

        1. Borra movimientos SISTEMA anteriores (si existen)
        2. Calcula: sueldo, horas extra, prima dominical, faltas
        3. Calcula: exenciones ISR de cada percepción
        4. Calcula: ISR proporcional al período
        5. Calcula: subsidio al empleo
        6. Calcula: IMSS obrero
        7. Lee: movimientos manuales existentes (para totales)
        8. Inserta: movimientos SISTEMA
        9. Actualiza: totales en nominas_empleado
        """
        nomina_id = nomina['id']
        salario_diario = Decimal(str(nomina.get('salario_diario') or 0))
        sdi = Decimal(str(nomina.get('salario_diario_integrado') or salario_diario))
        dias_trabajados = int(nomina.get('dias_trabajados') or 0)
        dias_faltas = int(nomina.get('dias_faltas') or 0)
        dias_incapacidad = int(nomina.get('dias_incapacidad') or 0)
        dias_periodo = int(nomina.get('dias_periodo') or 15)
        horas_dobles = Decimal(str(nomina.get('horas_extra_dobles') or 0))
        horas_triples = Decimal(str(nomina.get('horas_extra_triples') or 0))
        domingos = int(nomina.get('domingos_trabajados') or 0)
        periodicidad = self._normalizar_periodicidad(periodo.get('periodicidad'))
        tipo_periodo = self._normalizar_tipo_periodo(periodo.get('tipo_periodo'))
        regla_calculo_quincenal = await self._resolver_regla_calculo_quincenal_periodo(
            periodo
        )
        contexto_fiscal, aplicar_art_36 = await self._resolver_contexto_fiscal_periodo(periodo)
        snapshot_fiscal = self._resolver_snapshot_fiscal_nomina(nomina, contexto_fiscal)
        if not periodo.get("fecha_pago"):
            snapshot_fiscal["observaciones_fiscales"].append(
                self._observacion_fiscal(
                    "FECHA_PAGO_REQUERIDA",
                    (
                        "El período no tiene fecha de pago configurada; se usó fecha_fin "
                        "como referencia fiscal provisional."
                    ),
                    "error",
                )
            )

        if salario_diario <= 0:
            raise BusinessRuleError(
                f"Empleado {nomina.get('empleado_id')} tiene salario_diario=0. "
                "Actualice el salario antes de calcular."
            )

        uma_diario = contexto_fiscal.uma_diaria

        # ── 1. Borrar movimientos SISTEMA anteriores ─────────────────────────
        self.supabase.table('nomina_movimientos').delete().eq(
            'nomina_empleado_id', nomina_id
        ).eq('origen', 'SISTEMA').eq('es_automatico', True).execute()

        if tipo_periodo == TipoPeriodoNomina.AGUINALDO.value:
            return await self._calcular_nomina_aguinaldo(
                nomina=nomina,
                periodo=periodo,
                contexto_fiscal=contexto_fiscal,
                snapshot_fiscal=snapshot_fiscal,
            )

        # ── 2. Calcular percepciones automáticas ─────────────────────────────
        movimientos_sistema: list[dict] = []

        # Sueldo
        if (
            periodicidad == PeriodicidadNomina.QUINCENAL.value
            and regla_calculo_quincenal == ReglaCalculoQuincenal.MIXTA.value
        ):
            sueldo = _round2(salario_diario * Decimal('15'))
        else:
            sueldo = _round2(salario_diario * dias_trabajados)
        if sueldo > 0:
            movimientos_sistema.append(self._mov(
                nomina_id, 'SUELDO', 'PERCEPCION', sueldo, sueldo, Decimal('0')
            ))

        # Horas extra dobles
        if horas_dobles > 0:
            monto_hed = _round2(salario_diario / 8 * 2 * horas_dobles)
            gravable_hed, exento_hed = self._calcular_exencion('HORAS_EXTRA_DOBLES', monto_hed, uma_diario)
            movimientos_sistema.append(self._mov(
                nomina_id, 'HORAS_EXTRA_DOBLES', 'PERCEPCION',
                monto_hed, gravable_hed, exento_hed
            ))

        # Horas extra triples (100% gravable)
        if horas_triples > 0:
            monto_het = _round2(salario_diario / 8 * 3 * horas_triples)
            movimientos_sistema.append(self._mov(
                nomina_id, 'HORAS_EXTRA_TRIPLES', 'PERCEPCION',
                monto_het, monto_het, Decimal('0')
            ))

        # Prima dominical
        if domingos > 0:
            monto_pd = _round2(salario_diario * Decimal('0.25') * domingos)
            gravable_pd, exento_pd = self._calcular_exencion('PRIMA_DOMINICAL', monto_pd, uma_diario)
            movimientos_sistema.append(self._mov(
                nomina_id, 'PRIMA_DOMINICAL', 'PERCEPCION',
                monto_pd, gravable_pd, exento_pd
            ))

        aplica_descuentos_automaticos_quincenales = not (
            periodicidad == PeriodicidadNomina.QUINCENAL.value
            and regla_calculo_quincenal == ReglaCalculoQuincenal.REAL.value
        )

        # Descuento por faltas (deducción automática)
        if dias_faltas > 0 and aplica_descuentos_automaticos_quincenales:
            monto_faltas = _round2(salario_diario * dias_faltas)
            movimientos_sistema.append(self._mov(
                nomina_id, 'DESCUENTO_FALTAS', 'DEDUCCION',
                monto_faltas, Decimal('0'), Decimal('0')
            ))

        # Descuento por incapacidad (IMSS paga días, empresa descuenta)
        if dias_incapacidad > 0 and aplica_descuentos_automaticos_quincenales:
            monto_incap = _round2(salario_diario * dias_incapacidad)
            movimientos_sistema.append(self._mov(
                nomina_id, 'DESCUENTO_INCAPACIDAD', 'DEDUCCION',
                monto_incap, Decimal('0'), Decimal('0')
            ))

        # ── 3. Base gravable ISR ─────────────────────────────────────────────
        # Los movimientos manuales gravables ya existen antes del cálculo; deben
        # participar en ISR aunque sus totales se consoliden al final.
        manuales = await self._leer_movimientos_manuales(nomina_id)
        base_gravable_periodo = self._sumar_base_gravable_isr(
            movimientos_sistema,
            manuales,
        )

        # ── 4. ISR proporcional al período ────────────────────────────────────
        factor = _FACTOR_MENSUAL.get(periodicidad, Decimal('2'))
        base_mensual = _round2(base_gravable_periodo * factor)

        tiene_percepciones_adicionales = (
            horas_dobles > 0
            or horas_triples > 0
            or domingos > 0
            or self._tiene_percepciones_manuales(manuales)
        )
        solo_salario_minimo_art96 = (
            bool(snapshot_fiscal["es_salario_minimo_art36"])
            and not tiene_percepciones_adicionales
        )

        if solo_salario_minimo_art96:
            isr_mensual = Decimal("0")
        else:
            isr_mensual = self._calcular_isr_mensual_con_fecha(
                base_mensual,
                contexto_fiscal.fecha_referencia,
            )
        isr_periodo = _round2(isr_mensual / factor)

        if isr_periodo > 0:
            movimientos_sistema.append(self._mov(
                nomina_id, 'ISR', 'DEDUCCION',
                isr_periodo, Decimal('0'), Decimal('0')
            ))

        # ── 5. Subsidio al empleo ─────────────────────────────────────────────
        subsidio_periodo = (
            Decimal("0")
            if solo_salario_minimo_art96
            else self._calcular_subsidio_periodo_aplicable(
                base_mensual,
                isr_periodo,
                contexto_fiscal.fecha_referencia,
                dias_periodo=dias_periodo,
                periodicidad=periodicidad,
            )
        )

        if subsidio_periodo > 0:
            movimientos_sistema.append(self._mov(
                nomina_id, 'SUBSIDIO_EMPLEO', 'OTRO_PAGO',
                subsidio_periodo, Decimal('0'), Decimal('0')
            ))

        # ── 6. IMSS obrero ────────────────────────────────────────────────────
        # `dias_trabajados` en nómina ya representa los días pagables del período.
        dias_cotizables = dias_trabajados
        sdi_float = float(sdi)
        cuotas_obreras, imss_obrero_absorbido = self.calculadora_imss.calcular_obrero(
            sbc_diario=sdi_float,
            dias=dias_cotizables,
            es_salario_minimo=bool(snapshot_fiscal["es_salario_minimo_art36"]),
            aplicar_art_36=aplicar_art_36,
            uma_diaria=float(contexto_fiscal.uma_diaria),
        )

        imss_obrero = _round2(Decimal(str(sum(cuotas_obreras.values()))))
        if imss_obrero > 0:
            movimientos_sistema.append(self._mov(
                nomina_id, 'IMSS_OBRERO', 'DEDUCCION',
                imss_obrero, Decimal('0'), Decimal('0')
            ))

        # ── 7. Insertar movimientos SISTEMA ───────────────────────────────────
        if movimientos_sistema:
            # Convertir Decimals a float para Supabase
            registros_bd = [
                {k: float(v) if isinstance(v, Decimal) else v for k, v in m.items()}
                for m in movimientos_sistema
            ]
            self.supabase.table('nomina_movimientos').insert(registros_bd).execute()

        # ── 9. Calcular totales consolidados ──────────────────────────────────
        percepciones, deducciones, otros_pagos, neto = self._sumar_totales_con_movimientos(
            movimientos_sistema=movimientos_sistema,
            manuales=manuales,
        )

        observaciones_fiscales = snapshot_fiscal["observaciones_fiscales"]
        listo_para_timbrar = not any(
            str(item.get("severity") or "").lower() == "error"
            for item in observaciones_fiscales
            if isinstance(item, dict)
        )

        # ── 10. Actualizar nominas_empleado ────────────────────────────────────
        return self._persistir_nomina_calculada(
            nomina_id=nomina_id,
            percepciones=percepciones,
            deducciones=deducciones,
            otros_pagos=otros_pagos,
            neto=neto,
            snapshot_fiscal=snapshot_fiscal,
            observaciones_fiscales=observaciones_fiscales,
            listo_para_timbrar=listo_para_timbrar,
            imss_obrero_absorbido=Decimal(str(imss_obrero_absorbido or 0)),
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _mov(
        self,
        nomina_empleado_id: int,
        clave: str,
        tipo: str,
        monto: Decimal,
        monto_gravable: Decimal,
        monto_exento: Decimal,
    ) -> dict:
        """Construye el dict de un movimiento SISTEMA."""
        concepto_id = self._concepto_ids.get(clave)
        if concepto_id is None:
            raise BusinessRuleError(
                f"Concepto '{clave}' no encontrado en BD. "
                "Ejecute sincronizar_catalogo() primero."
            )
        return {
            'nomina_empleado_id': nomina_empleado_id,
            'concepto_id': concepto_id,
            'tipo': tipo,
            'origen': 'SISTEMA',
            'monto': monto,
            'monto_gravable': monto_gravable,
            'monto_exento': monto_exento,
            'es_automatico': True,
        }

    def _calcular_exencion(
        self, clave: str, monto: Decimal, uma_diario: Decimal
    ) -> tuple[Decimal, Decimal]:
        """Delega a CatalogoConceptosNomina. Returns (gravable, exento)."""
        try:
            return CatalogoConceptosNomina.calcular_exencion(clave, monto, uma_diario)
        except KeyError:
            # Si el concepto no está en el catálogo, 100% gravable
            return (monto, Decimal('0'))

    async def _cargar_concepto_ids(self) -> None:
        """
        Carga el mapa clave→id desde la tabla conceptos_nomina (lazy, cached).
        Solo consulta BD si el caché está vacío.
        """
        if self._concepto_ids:
            return
        try:
            def _consultar_ids() -> dict[str, int]:
                result = (
                    self.supabase.table('conceptos_nomina')
                    .select('id, clave')
                    .in_('clave', list(_CLAVES_SISTEMA))
                    .execute()
                )
                return {
                    row['clave']: row['id']
                    for row in (result.data or [])
                    if row.get('clave') and row.get('id') is not None
                }

            self._concepto_ids = _consultar_ids()
            missing = _CLAVES_SISTEMA - set(self._concepto_ids.keys())
            if missing:
                logger.warning(
                    "Conceptos no encontrados en BD. Se intentará sincronizar catálogo: %s",
                    missing,
                )
                from app.domain.services.concepto_nomina_service import concepto_nomina_service

                await concepto_nomina_service.sincronizar_catalogo()
                self._concepto_ids = _consultar_ids()
                missing = _CLAVES_SISTEMA - set(self._concepto_ids.keys())

            if missing:
                raise BusinessRuleError(
                    "Faltan conceptos automáticos de nómina en BD: "
                    f"{', '.join(sorted(missing))}."
                )
        except BusinessRuleError:
            raise
        except Exception as e:
            logger.error(f"Error cargando IDs de conceptos: {e}")
            raise DatabaseError(f"Error cargando catálogo de conceptos: {e}")

    async def _reconsolidar_periodo(
        self,
        periodo_id: int,
        *,
        estatus: Optional[str] = None,
    ) -> None:
        """Recalcula agregados del período desde las nóminas persistidas."""
        result = (
            self.supabase.table('nominas_empleado')
            .select(
                'total_percepciones, total_deducciones, total_neto, '
                'listo_para_timbrar, observaciones_fiscales'
            )
            .eq('periodo_id', periodo_id)
            .execute()
        )
        filas = result.data or []
        total_percepciones = sum(
            (Decimal(str(item.get('total_percepciones') or 0)) for item in filas),
            Decimal('0'),
        )
        total_deducciones = sum(
            (Decimal(str(item.get('total_deducciones') or 0)) for item in filas),
            Decimal('0'),
        )
        total_neto = sum(
            (Decimal(str(item.get('total_neto') or 0)) for item in filas),
            Decimal('0'),
        )
        total_observaciones = sum(
            1 for item in filas if bool(item.get('observaciones_fiscales'))
        )
        listo_para_timbrar = bool(filas) and all(
            bool(item.get('listo_para_timbrar', False)) for item in filas
        )

        payload = {
            'total_percepciones': str(_round2(total_percepciones)),
            'total_deducciones': str(_round2(total_deducciones)),
            'total_neto': str(_round2(total_neto)),
            'total_empleados': len(filas),
            'listo_para_timbrar': listo_para_timbrar,
            'total_empleados_con_observaciones_fiscales': total_observaciones,
        }
        if estatus:
            payload['estatus'] = estatus

        self.supabase.table('periodos_nomina').update(payload).eq('id', periodo_id).execute()

    async def _obtener_periodo(self, periodo_id: int) -> dict:
        """Obtiene período o lanza NotFoundError."""
        result = (
            self.supabase.table('periodos_nomina')
            .select('*')
            .eq('id', periodo_id)
            .execute()
        )
        if not result.data:
            raise NotFoundError(f"Período de nómina {periodo_id} no encontrado")
        return result.data[0]

    async def _obtener_nomina_empleado(self, nomina_empleado_id: int) -> dict:
        result = (
            self.supabase.table('nominas_empleado')
            .select('*')
            .eq('id', nomina_empleado_id)
            .execute()
        )
        if not result.data:
            raise NotFoundError(f"NominaEmpleado {nomina_empleado_id} no encontrada")
        return result.data[0]

    async def _obtener_nominas_del_periodo(self, periodo_id: int) -> list[dict]:
        """Obtiene todas las nominas_empleado de un período."""
        result = (
            self.supabase.table('nominas_empleado')
            .select('*')
            .eq('periodo_id', periodo_id)
            .execute()
        )
        return result.data or []


# Singleton
nomina_calculo_service = NominaCalculoService()
