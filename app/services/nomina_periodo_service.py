"""
Servicio de ciclo de vida de períodos de nómina.

Gestiona la creación, poblado con empleados y transiciones de
estatus del período (workflow RRHH → Contabilidad).

Patrón: Direct Access (sin repository).
"""
import logging
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.database import db_manager
from app.core.exceptions import DatabaseError, NotFoundError, BusinessRuleError
from app.entities.periodo_nomina import PeriodoNomina

logger = logging.getLogger(__name__)

# Tipos de registro que impactan nómina
_TIPOS_INCAPACIDAD = ('INCAPACIDAD_ENFERMEDAD', 'INCAPACIDAD_RIESGO_TRABAJO', 'INCAPACIDAD_MATERNIDAD')
_ESTATUS_REPOBLABLES = (
    'BORRADOR',
    'EN_PREPARACION_RRHH',
    'ENVIADO_A_CONTABILIDAD',
    'EN_PROCESO_CONTABILIDAD',
)


class NominaPeriodoService:
    """
    Gestiona el ciclo de vida de los períodos de nómina.

    Responsabilidades:
    - Crear y configurar períodos de nómina
    - Poblar con empleados activos (snapshot de salario + asistencias)
    - Controlar transiciones de workflow (BORRADOR → … → CERRADO)
    - Consultas de períodos y sus empleados
    """

    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'periodos_nomina'
        self.tabla_nom_emp = 'nominas_empleado'

    def _salario_diario_desde_mensual(self, salario_mensual: object) -> float:
        """
        Convierte salario mensual de plaza a salario diario con base 30.

        La nómina opera con salario diario snapshot en `nominas_empleado`,
        mientras que la fuente vigente del sueldo está en `plazas.salario_mensual`.
        """
        if salario_mensual in (None, ""):
            return 0.0

        diario = (
            Decimal(str(salario_mensual)) / Decimal("30")
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return float(diario)

    def _mapear_salario_diario_por_empleado(self, empleado_ids: list[int]) -> dict[int, float]:
        """
        Resuelve salario diario vigente por empleado desde su asignación activa.

        Fuente de verdad:
        - `historial_laboral` determina la asignación ACTIVA del empleado.
        - `plazas.salario_mensual` define el salario vigente de esa asignación.
        """
        if not empleado_ids:
            return {}

        res_historial = (
            self.supabase.table("historial_laboral")
            .select("empleado_id, plaza_id")
            .in_("empleado_id", empleado_ids)
            .eq("estatus", "ACTIVA")
            .is_("fecha_fin", "null")
            .execute()
        )

        historial_activo = res_historial.data or []
        plaza_ids = list({
            item["plaza_id"]
            for item in historial_activo
            if item.get("plaza_id") is not None
        })
        if not plaza_ids:
            return {}

        res_plazas = (
            self.supabase.table("plazas")
            .select("id, salario_mensual")
            .in_("id", plaza_ids)
            .execute()
        )
        salario_mensual_por_plaza = {
            item["id"]: item.get("salario_mensual")
            for item in (res_plazas.data or [])
            if item.get("id") is not None
        }

        salario_diario_por_empleado: dict[int, float] = {}
        for item in historial_activo:
            empleado_id = item.get("empleado_id")
            plaza_id = item.get("plaza_id")
            if empleado_id is None or plaza_id is None:
                continue
            salario_mensual = salario_mensual_por_plaza.get(plaza_id)
            salario_diario_por_empleado[empleado_id] = self._salario_diario_desde_mensual(
                salario_mensual
            )

        return salario_diario_por_empleado

    def _actualizar_total_empleados_periodo(self, periodo_id: int, total_empleados: int) -> None:
        """Mantiene sincronizado el snapshot agregado del período."""
        self.supabase.table(self.tabla).update({
            'total_empleados': total_empleados,
        }).eq('id', periodo_id).execute()

    def _consultar_empleados_periodo(self, periodo_id: int) -> list[dict]:
        """Consulta los recibos del período con nombre y clave del empleado."""
        result = (
            self.supabase.table(self.tabla_nom_emp)
            .select('*, empleados(nombre, apellido_paterno, clave)')
            .eq('periodo_id', periodo_id)
            .order('id')
            .execute()
        )
        items = []
        for r in (result.data or []):
            emp = r.pop('empleados', {}) or {}
            nombre = emp.get('nombre', '')
            apellido = emp.get('apellido_paterno', '')
            r['nombre_empleado'] = f"{nombre} {apellido}".strip()
            r['clave_empleado'] = emp.get('clave', '')
            items.append(r)
        return items

    # =========================================================================
    # CREACIÓN
    # =========================================================================

    async def crear_periodo(
        self,
        empresa_id: int,
        nombre: str,
        fecha_inicio: date,
        fecha_fin: date,
        periodicidad: str = 'QUINCENAL',
        contrato_id: Optional[int] = None,
        fecha_pago: Optional[date] = None,
        notas: Optional[str] = None,
    ) -> dict:
        """
        Crea un nuevo período de nómina en estatus BORRADOR.

        Raises:
            BusinessRuleError: Si las fechas son inválidas.
            DatabaseError: Si hay error de BD.
        """
        if fecha_fin < fecha_inicio:
            raise BusinessRuleError("fecha_fin debe ser mayor o igual a fecha_inicio")
        if fecha_pago is not None and fecha_pago < fecha_inicio:
            raise BusinessRuleError("fecha_pago debe ser mayor o igual a fecha_inicio")

        datos = {
            'empresa_id': empresa_id,
            'nombre': nombre,
            'periodicidad': periodicidad,
            'fecha_inicio': fecha_inicio.isoformat(),
            'fecha_fin': fecha_fin.isoformat(),
            'estatus': 'BORRADOR',
        }
        if contrato_id is not None:
            datos['contrato_id'] = contrato_id
        if fecha_pago is not None:
            datos['fecha_pago'] = fecha_pago.isoformat()
        if notas is not None:
            datos['notas'] = notas

        try:
            result = self.supabase.table(self.tabla).insert(datos).execute()
            logger.info(f"Período '{nombre}' creado (empresa {empresa_id})")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error creando período '{nombre}': {e}")
            raise DatabaseError(f"Error creando período de nómina: {e}")

    # =========================================================================
    # POBLAR EMPLEADOS
    # =========================================================================

    async def poblar_empleados(self, periodo_id: int) -> int:
        """
        Crea registros en nominas_empleado para todos los empleados ACTIVOS.

        Para cada empleado:
        - Toma snapshot de salario_diario, banco y CLABE.
        - Consulta registros_asistencia del rango de fechas del período.
        - Pre-carga: dias_trabajados, dias_faltas, dias_incapacidad,
          dias_vacaciones, horas_extra (dobles/triples), domingos_trabajados.

        Returns:
            Número de empleados poblados.

        Raises:
            NotFoundError: Si el período no existe.
            DatabaseError: Si hay error de BD.
        """
        periodo = await self.obtener_periodo(periodo_id)
        empresa_id = periodo['empresa_id']
        fecha_inicio = periodo['fecha_inicio']
        fecha_fin = periodo['fecha_fin']

        try:
            # 1. Empleados ACTIVOS de la empresa
            res_emp = (
                self.supabase.table('empleados')
                .select('id, nombre, apellido_paterno, banco, clabe_interbancaria')
                .eq('empresa_id', empresa_id)
                .eq('estatus', 'ACTIVO')
                .execute()
            )
            empleados = res_emp.data or []
            if not empleados:
                logger.warning(f"No hay empleados ACTIVOS para empresa {empresa_id}")
                return 0

            empleado_ids = [emp['id'] for emp in empleados if emp.get('id') is not None]
            salario_diario_por_empleado = self._mapear_salario_diario_por_empleado(empleado_ids)
            empleados_sin_salario = [
                emp_id for emp_id in empleado_ids if salario_diario_por_empleado.get(emp_id, 0.0) <= 0
            ]
            if empleados_sin_salario:
                logger.warning(
                    "Período %s: %s empleado(s) activos sin plaza/salario vigente: %s",
                    periodo_id,
                    len(empleados_sin_salario),
                    empleados_sin_salario,
                )

            # 2. Registros de asistencia del período (batch)
            res_asist = (
                self.supabase.table('registros_asistencia')
                .select('empleado_id, fecha, tipo_registro, horas_extra')
                .eq('empresa_id', empresa_id)
                .gte('fecha', fecha_inicio)
                .lte('fecha', fecha_fin)
                .execute()
            )
            asistencias_raw = res_asist.data or []

            # 3. Agrupar asistencias por empleado
            por_empleado: dict[int, list[dict]] = defaultdict(list)
            for reg in asistencias_raw:
                por_empleado[reg['empleado_id']].append(reg)

            # 4. Construir registros nominas_empleado
            dias_periodo = (
                date.fromisoformat(fecha_fin) - date.fromisoformat(fecha_inicio)
            ).days + 1

            registros = []
            empleados_omitidos: list[int] = []
            for emp in empleados:
                emp_id = emp['id']
                asistencias = por_empleado.get(emp_id, [])

                dias_trabajados = sum(
                    1 for a in asistencias if a['tipo_registro'] == 'ASISTENCIA'
                )
                dias_faltas = sum(
                    1 for a in asistencias if a['tipo_registro'] == 'FALTA'
                )
                dias_incapacidad = sum(
                    1 for a in asistencias if a['tipo_registro'] in _TIPOS_INCAPACIDAD
                )
                dias_vacaciones = sum(
                    1 for a in asistencias if a['tipo_registro'] == 'VACACIONES'
                )
                total_horas_extra = sum(
                    float(a['horas_extra'] or 0)
                    for a in asistencias
                    if a['tipo_registro'] == 'ASISTENCIA'
                )
                domingos = sum(
                    1 for a in asistencias
                    if a['tipo_registro'] == 'ASISTENCIA'
                    and date.fromisoformat(a['fecha']).weekday() == 6
                )

                # Distribución simple: primeras 9 horas = dobles, resto = triples
                horas_dobles = min(total_horas_extra, 9.0)
                horas_triples = max(0.0, total_horas_extra - 9.0)

                salario_diario = salario_diario_por_empleado.get(emp_id, 0.0)
                if salario_diario <= 0:
                    empleados_omitidos.append(emp_id)
                    continue

                registros.append({
                    'periodo_id': periodo_id,
                    'empleado_id': emp_id,
                    'empresa_id': empresa_id,
                    'estatus': 'PENDIENTE',
                    'salario_diario': salario_diario,
                    'salario_diario_integrado': salario_diario,  # SDI ≈ SD como default
                    'dias_periodo': dias_periodo,
                    'dias_trabajados': dias_trabajados,
                    'dias_faltas': dias_faltas,
                    'dias_incapacidad': dias_incapacidad,
                    'dias_vacaciones': dias_vacaciones,
                    'horas_extra_dobles': horas_dobles,
                    'horas_extra_triples': horas_triples,
                    'domingos_trabajados': domingos,
                    'banco_destino': emp.get('banco'),
                    'clabe_destino': emp.get('clabe_interbancaria'),
                })

            if empleados_omitidos:
                logger.warning(
                    "Período %s: se omitieron %s empleado(s) sin salario diario vigente: %s",
                    periodo_id,
                    len(empleados_omitidos),
                    empleados_omitidos,
                )

            if not registros:
                self._actualizar_total_empleados_periodo(periodo_id, 0)
                return 0

            # 5. Upsert por (periodo_id, empleado_id) — idempotente
            result = (
                self.supabase.table(self.tabla_nom_emp)
                .upsert(registros, on_conflict='periodo_id,empleado_id')
                .execute()
            )
            total = len(result.data) if result.data else len(registros)
            self._actualizar_total_empleados_periodo(periodo_id, total)
            logger.info(f"Período {periodo_id}: {total} empleados poblados")
            return total

        except (NotFoundError, BusinessRuleError):
            raise
        except Exception as e:
            logger.error(f"Error poblando empleados del período {periodo_id}: {e}")
            raise DatabaseError(f"Error poblando empleados del período: {e}")

    # =========================================================================
    # WORKFLOW
    # =========================================================================

    async def transicionar_estatus(
        self,
        periodo_id: int,
        nuevo_estatus: str,
        usuario_id: Optional[str] = None,
    ) -> dict:
        """
        Transiciona el período al nuevo estatus si la transición es válida.

        Registra el usuario responsable cuando aplica:
        - ENVIADO_A_CONTABILIDAD: guarda enviado_contabilidad_por y _fecha
        - CERRADO: guarda cerrado_por y fecha_cierre

        Raises:
            NotFoundError: Si el período no existe.
            BusinessRuleError: Si la transición no es válida.
            DatabaseError: Si hay error de BD.
        """
        periodo = await self.obtener_periodo(periodo_id)
        estatus_actual = periodo['estatus']

        if not PeriodoNomina.es_transicion_valida(estatus_actual, nuevo_estatus):
            raise BusinessRuleError(
                f"No se puede pasar de '{estatus_actual}' a '{nuevo_estatus}'. "
                f"Transiciones válidas desde '{estatus_actual}': "
                f"{PeriodoNomina.TRANSICIONES_VALIDAS.get(estatus_actual, [])}"
            )

        from datetime import datetime, timezone
        ahora = datetime.now(timezone.utc).isoformat()

        datos: dict = {'estatus': nuevo_estatus}

        if nuevo_estatus == 'ENVIADO_A_CONTABILIDAD':
            datos['enviado_contabilidad_fecha'] = ahora
            if usuario_id:
                datos['enviado_contabilidad_por'] = usuario_id

        elif nuevo_estatus == 'CERRADO':
            datos['fecha_cierre'] = ahora
            if usuario_id:
                datos['cerrado_por'] = usuario_id

        try:
            result = (
                self.supabase.table(self.tabla)
                .update(datos)
                .eq('id', periodo_id)
                .execute()
            )
            logger.info(f"Período {periodo_id}: {estatus_actual} → {nuevo_estatus}")
            return result.data[0]
        except Exception as e:
            logger.error(f"Error transicionando período {periodo_id}: {e}")
            raise DatabaseError(f"Error transicionando estatus del período: {e}")

    # =========================================================================
    # CONSULTAS
    # =========================================================================

    async def obtener_periodo(self, periodo_id: int) -> dict:
        """
        Obtiene un período por ID.

        Raises:
            NotFoundError: Si no existe.
        """
        try:
            result = (
                self.supabase.table(self.tabla)
                .select('*')
                .eq('id', periodo_id)
                .execute()
            )
            if not result.data:
                raise NotFoundError(f"Período de nómina con ID {periodo_id} no encontrado")
            return result.data[0]
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo período {periodo_id}: {e}")
            raise DatabaseError(f"Error obteniendo período de nómina: {e}")

    async def listar_periodos(
        self,
        empresa_id: int,
        estatus: Optional[str] = None,
    ) -> list[dict]:
        """Lista períodos de una empresa, opcionalmente filtrados por estatus."""
        try:
            query = (
                self.supabase.table(self.tabla)
                .select('*')
                .eq('empresa_id', empresa_id)
                .order('fecha_inicio', desc=True)
            )
            if estatus:
                query = query.eq('estatus', estatus)
            result = query.execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error listando períodos empresa {empresa_id}: {e}")
            raise DatabaseError(f"Error listando períodos de nómina: {e}")

    async def obtener_empleados_periodo(self, periodo_id: int) -> list[dict]:
        """
        Retorna los registros de nominas_empleado con datos del empleado (JOIN).

        Incluye: nombre_empleado, clave_empleado para display en UI.
        """
        try:
            items = self._consultar_empleados_periodo(periodo_id)
            if items:
                return items

            periodo = await self.obtener_periodo(periodo_id)
            if periodo.get('estatus') in _ESTATUS_REPOBLABLES:
                total = await self.poblar_empleados(periodo_id)
                if total > 0:
                    return self._consultar_empleados_periodo(periodo_id)

            return []
        except Exception as e:
            logger.error(f"Error obteniendo empleados del período {periodo_id}: {e}")
            raise DatabaseError(f"Error obteniendo empleados del período: {e}")


# Singleton
nomina_periodo_service = NominaPeriodoService()
