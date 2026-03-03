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
from typing import Optional

from app.database import db_manager
from app.core.exceptions import DatabaseError, NotFoundError, BusinessRuleError
from app.core.catalogs import CatalogoConceptosNomina, CatalogoUMA
from app.core.catalogs.fiscal.isr import CatalogoISR
from app.core.calculations.calculadora_imss import CalculadoraIMSS

logger = logging.getLogger(__name__)

# Claves de conceptos que este motor genera automáticamente (origen=SISTEMA)
_CLAVES_SISTEMA = {
    'SUELDO', 'HORAS_EXTRA_DOBLES', 'HORAS_EXTRA_TRIPLES',
    'PRIMA_DOMINICAL', 'DESCUENTO_FALTAS', 'DESCUENTO_INCAPACIDAD',
    'ISR', 'IMSS_OBRERO', 'SUBSIDIO_EMPLEO',
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
            'errores': [],
        }

        for nomina in nominas:
            try:
                totales = await self._calcular_nomina_empleado(nomina, periodo)
                resumen['empleados_calculados'] += 1
                resumen['total_percepciones'] += totales['total_percepciones']
                resumen['total_deducciones'] += totales['total_deducciones']
                resumen['total_neto'] += totales['total_neto']
            except Exception as e:
                emp_id = nomina.get('empleado_id', '?')
                logger.error(f"Error calculando nómina empleado {emp_id}: {e}")
                resumen['errores'].append({'empleado_id': emp_id, 'error': str(e)})

        # Actualizar totales consolidados del período
        try:
            self.supabase.table('periodos_nomina').update({
                'total_percepciones': str(_round2(resumen['total_percepciones'])),
                'total_deducciones': str(_round2(resumen['total_deducciones'])),
                'total_neto': str(_round2(resumen['total_neto'])),
                'total_empleados': resumen['empleados_calculados'],
            }).eq('id', periodo_id).execute()
        except Exception as e:
            logger.error(f"Error actualizando totales período {periodo_id}: {e}")

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
        res = (
            self.supabase.table('nominas_empleado')
            .select('*')
            .eq('id', nomina_empleado_id)
            .execute()
        )
        if not res.data:
            raise NotFoundError(f"NominaEmpleado {nomina_empleado_id} no encontrada")
        nomina = res.data[0]

        # Obtener período
        periodo = await self._obtener_periodo(nomina['periodo_id'])

        return await self._calcular_nomina_empleado(nomina, periodo)

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
        periodicidad = periodo.get('periodicidad', 'QUINCENAL')

        if salario_diario <= 0:
            raise BusinessRuleError(
                f"Empleado {nomina.get('empleado_id')} tiene salario_diario=0. "
                "Actualice el salario antes de calcular."
            )

        uma_diario = CatalogoUMA.DIARIO

        # ── 1. Borrar movimientos SISTEMA anteriores ─────────────────────────
        self.supabase.table('nomina_movimientos').delete().eq(
            'nomina_empleado_id', nomina_id
        ).eq('origen', 'SISTEMA').eq('es_automatico', True).execute()

        # ── 2. Calcular percepciones automáticas ─────────────────────────────
        movimientos_sistema: list[dict] = []

        # Sueldo
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

        # Descuento por faltas (deducción automática)
        if dias_faltas > 0:
            monto_faltas = _round2(salario_diario * dias_faltas)
            movimientos_sistema.append(self._mov(
                nomina_id, 'DESCUENTO_FALTAS', 'DEDUCCION',
                monto_faltas, Decimal('0'), Decimal('0')
            ))

        # Descuento por incapacidad (IMSS paga días, empresa descuenta)
        if dias_incapacidad > 0:
            monto_incap = _round2(salario_diario * dias_incapacidad)
            movimientos_sistema.append(self._mov(
                nomina_id, 'DESCUENTO_INCAPACIDAD', 'DEDUCCION',
                monto_incap, Decimal('0'), Decimal('0')
            ))

        # ── 3. Base gravable ISR (suma de monto_gravable de percepciones) ────
        base_gravable_periodo = sum(
            m['monto_gravable'] for m in movimientos_sistema
            if m['tipo'] == 'PERCEPCION'
        )

        # ── 4. ISR proporcional al período ────────────────────────────────────
        factor = _FACTOR_MENSUAL.get(periodicidad, Decimal('2'))
        base_mensual = _round2(base_gravable_periodo * factor)

        isr_mensual = CatalogoISR.calcular_isr_mensual(base_mensual)
        isr_periodo = _round2(isr_mensual / factor)

        if isr_periodo > 0:
            movimientos_sistema.append(self._mov(
                nomina_id, 'ISR', 'DEDUCCION',
                isr_periodo, Decimal('0'), Decimal('0')
            ))

        # ── 5. Subsidio al empleo ─────────────────────────────────────────────
        subsidio_mensual = CatalogoISR.calcular_subsidio(base_mensual)
        subsidio_periodo = _round2(subsidio_mensual / factor)

        if subsidio_periodo > 0:
            movimientos_sistema.append(self._mov(
                nomina_id, 'SUBSIDIO_EMPLEO', 'OTRO_PAGO',
                subsidio_periodo, Decimal('0'), Decimal('0')
            ))

        # ── 6. IMSS obrero ────────────────────────────────────────────────────
        # Días cotizables = trabajados + vacaciones (incapacidad los paga IMSS)
        dias_cotizables = dias_trabajados + int(nomina.get('dias_vacaciones') or 0)
        sdi_float = float(sdi)
        es_sm = sdi_float <= float(CatalogoUMA.DIARIO) * 1.5  # proxy salario mínimo

        cuotas_obreras, _ = self.calculadora_imss.calcular_obrero(
            sbc_diario=sdi_float,
            dias=dias_cotizables,
            es_salario_minimo=es_sm,
            aplicar_art_36=False,  # Spring 4 podría hacer configurable por empresa
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

        # ── 8. Leer movimientos manuales existentes (RRHH y Contabilidad) ────
        res_manual = (
            self.supabase.table('nomina_movimientos')
            .select('tipo, monto, origen')
            .eq('nomina_empleado_id', nomina_id)
            .neq('origen', 'SISTEMA')
            .execute()
        )
        manuales = res_manual.data or []

        # ── 9. Calcular totales consolidados ──────────────────────────────────
        percepciones = sum(
            Decimal(str(m['monto_gravable'])) + Decimal(str(m['monto_exento']))
            for m in movimientos_sistema if m['tipo'] == 'PERCEPCION'
        )
        percepciones += sum(
            Decimal(str(m['monto'])) for m in manuales if m['tipo'] == 'PERCEPCION'
        )

        deducciones = sum(
            Decimal(str(m['monto'])) for m in movimientos_sistema if m['tipo'] == 'DEDUCCION'
        )
        deducciones += sum(
            Decimal(str(m['monto'])) for m in manuales if m['tipo'] == 'DEDUCCION'
        )

        otros_pagos = sum(
            Decimal(str(m['monto'])) for m in movimientos_sistema if m['tipo'] == 'OTRO_PAGO'
        )
        otros_pagos += sum(
            Decimal(str(m['monto'])) for m in manuales if m['tipo'] == 'OTRO_PAGO'
        )

        neto = _round2(percepciones - deducciones + otros_pagos)
        percepciones = _round2(percepciones)
        deducciones = _round2(deducciones)
        otros_pagos = _round2(otros_pagos)

        # ── 10. Actualizar nominas_empleado ────────────────────────────────────
        self.supabase.table('nominas_empleado').update({
            'total_percepciones': float(percepciones),
            'total_deducciones': float(deducciones),
            'total_otros_pagos': float(otros_pagos),
            'total_neto': float(max(neto, Decimal('0'))),
            'estatus': 'CALCULADO',
        }).eq('id', nomina_id).execute()

        return {
            'nomina_empleado_id': nomina_id,
            'total_percepciones': percepciones,
            'total_deducciones': deducciones,
            'total_otros_pagos': otros_pagos,
            'total_neto': max(neto, Decimal('0')),
        }

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
            result = (
                self.supabase.table('conceptos_nomina')
                .select('id, clave')
                .in_('clave', list(_CLAVES_SISTEMA))
                .execute()
            )
            for row in (result.data or []):
                self._concepto_ids[row['clave']] = row['id']
            missing = _CLAVES_SISTEMA - set(self._concepto_ids.keys())
            if missing:
                logger.warning(
                    f"Conceptos no encontrados en BD: {missing}. "
                    "Ejecute concepto_nomina_service.sincronizar_catalogo()."
                )
        except Exception as e:
            logger.error(f"Error cargando IDs de conceptos: {e}")
            raise DatabaseError(f"Error cargando catálogo de conceptos: {e}")

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
