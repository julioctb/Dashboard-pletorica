"""
Servicio de ciclo de vida de períodos de nómina.

Gestiona la creación, poblado con empleados y transiciones de
estatus del período (workflow RRHH → Contabilidad).

Patrón: Direct Access (sin repository).
"""
import logging
from calendar import monthrange
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace
from typing import Optional

from app.core.catalogs.nomina import (
    detectar_periodo_actual,
    generar_catalogo_periodos,
    resolver_periodo_por_key,
    resolver_quincena_por_key,
)
from app.core.catalogs.fiscal import PoliticaFiscalResolver
from app.core.enums import (
    EstatusPlaza,
    PeriodicidadNomina,
    ReglaCalculoQuincenal,
    TipoJornadaPlaza,
)
from app.core.exceptions import (
    BusinessRuleError,
    DatabaseError,
    DuplicateError,
    NotFoundError,
)
from app.core.text_utils import formatear_moneda, normalizar_mayusculas
from app.core.catalogs.sistema.tolerancias import Tolerancias
from app.database import db_manager
from app.entities.empleado_descuento_recurrente import (
    DESCUENTOS_RECURRENTES_CLAVES,
    DESCUENTOS_RECURRENTES_POR_CLAVE,
)
from app.entities.configuracion_operativa_empresa import (
    ConfiguracionOperativaEmpresaUpdate,
)
from app.entities.periodo_nomina import PeriodoNomina
from app.services.configuracion_operativa_service import configuracion_operativa_service
from app.services.configuracion_fiscal_service import configuracion_fiscal_service

logger = logging.getLogger(__name__)

# Tipos de registro que impactan nómina
_TIPOS_INASISTENCIA_NO_PAGADA = ('FALTA', 'PERMISO_SIN_GOCE')
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

    async def _obtener_configuracion_fiscal(self, empresa_id: int):
        try:
            return await configuracion_fiscal_service.obtener_o_crear_default(empresa_id)
        except Exception as exc:
            logger.warning(
                "Usando fallback de configuración fiscal para empresa %s: %s",
                empresa_id,
                exc,
            )
            return SimpleNamespace(zona_frontera=False, aplicar_art_36=True)

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

    def _normalizar_tipo_jornada(self, valor: object) -> str:
        if isinstance(valor, TipoJornadaPlaza):
            return valor.value
        try:
            return TipoJornadaPlaza(str(valor or "").upper()).value
        except ValueError:
            return TipoJornadaPlaza.COMPLETA.value

    def _factor_default_tipo_jornada(self, tipo_jornada: object) -> Decimal:
        tipo = self._normalizar_tipo_jornada(tipo_jornada)
        if tipo == TipoJornadaPlaza.MEDIA_JORNADA.value:
            return Decimal("0.50")
        return Decimal("1.00")

    def _normalizar_factor_jornada(
        self,
        valor: object,
        tipo_jornada: object,
    ) -> float:
        if valor in (None, ""):
            return float(self._factor_default_tipo_jornada(tipo_jornada))
        try:
            factor = Decimal(str(valor)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
        except Exception:
            return float(self._factor_default_tipo_jornada(tipo_jornada))
        if factor <= 0 or factor > 1:
            return float(self._factor_default_tipo_jornada(tipo_jornada))
        return float(factor)

    def _salario_minimo_proporcional_diario(
        self,
        salario_minimo_diario: object,
        factor_jornada: object,
    ) -> Decimal:
        return (
            Decimal(str(salario_minimo_diario or 0))
            * Decimal(str(factor_jornada or 0))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _observacion_fiscal(
        self,
        *,
        codigo: str,
        mensaje: str,
        severidad: str,
    ) -> dict[str, str]:
        return {
            "codigo": codigo,
            "mensaje": mensaje,
            "severity": severidad,
        }

    async def _resolver_contexto_fiscal_periodo(
        self,
        periodo: dict,
    ):
        fecha_fiscal = (
            periodo.get("fecha_pago")
            or periodo.get("fecha_fin")
            or date.today().isoformat()
        )
        zona_frontera = periodo.get("zona_frontera")
        aplicar_art_36 = periodo.get("aplicar_art_36")

        if zona_frontera is None or aplicar_art_36 is None:
            config_fiscal = await self._obtener_configuracion_fiscal(
                int(periodo["empresa_id"])
            )
            zona_frontera = bool(getattr(config_fiscal, "zona_frontera", False))
            aplicar_art_36 = bool(getattr(config_fiscal, "aplicar_art_36", True))

            try:
                self.supabase.table(self.tabla).update(
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
        return {
            "fecha_fiscal": contexto.fecha_referencia.isoformat(),
            "zona_frontera": bool(zona_frontera),
            "aplicar_art_36": bool(aplicar_art_36),
            "contexto": contexto,
        }

    def _calcular_dias_trabajados_nomina(
        self,
        dias_periodo: int,
        dias_faltas: int,
        dias_incapacidad: int,
    ) -> int:
        """
        Calcula los días pagables del período.

        La nómina base parte del período completo. Solo se descuentan
        inasistencias no pagadas e incapacidades; vacaciones siguen siendo días pagados.
        """
        return max(dias_periodo - dias_faltas - dias_incapacidad, 0)

    def _mapear_salario_diario_por_empleado(
        self,
        empresa_id: int,
        fecha_referencia: object,
        contrato_id: Optional[int] = None,
    ) -> dict[int, float]:
        """
        Resuelve salario diario vigente por empleado desde plazas ocupadas vigentes.

        Fuente de verdad:
        - `plazas` define la relación empleado-plaza vigente para nómina.
        - Solo cuentan plazas `OCUPADA` con `empleado_id` asignado.
        - `plazas.salario_mensual` define el salario vigente de esa asignación.
        """
        snapshot_por_empleado = self._mapear_plaza_vigente_por_empleado(
            empresa_id=empresa_id,
            fecha_referencia=fecha_referencia,
            contrato_id=contrato_id,
        )
        return {
            empleado_id: float(snapshot.get("salario_diario") or 0.0)
            for empleado_id, snapshot in snapshot_por_empleado.items()
        }

    def _consultar_plazas_ocupadas_vigentes(
        self,
        empresa_id: int,
        fecha_referencia: object,
        contrato_id: Optional[int] = None,
    ) -> list[dict]:
        """Obtiene plazas ocupadas vigentes al corte, ordenadas por inicio más reciente."""
        fecha_corte = (
            fecha_referencia.isoformat()
            if isinstance(fecha_referencia, date)
            else str(fecha_referencia)
        )

        if contrato_id is not None:
            contrato_ids = [contrato_id]
        else:
            res_contratos = (
                self.supabase.table("contratos")
                .select("id")
                .eq("empresa_id", empresa_id)
                .execute()
            )
            contrato_ids = [
                item["id"]
                for item in (res_contratos.data or [])
                if item.get("id") is not None
            ]
        if not contrato_ids:
            return []

        res_plazas = (
            self.supabase.table("plazas")
            .select(
                "id, empleado_id, salario_mensual, fecha_inicio, sede_id, "
                "tipo_jornada, factor_jornada"
            )
            .in_("contrato_id", contrato_ids)
            .eq("estatus", EstatusPlaza.OCUPADA.value)
            .lte("fecha_inicio", fecha_corte)
            .or_(f"fecha_fin.is.null,fecha_fin.gte.{fecha_corte}")
            .order("fecha_inicio", desc=True)
            .execute()
        )
        return res_plazas.data or []

    def _mapear_plaza_vigente_por_empleado(
        self,
        empresa_id: int,
        fecha_referencia: object,
        contrato_id: Optional[int] = None,
    ) -> dict[int, dict[str, object]]:
        """
        Resuelve el snapshot de plaza vigente por empleado al corte del período.

        Una sola fuente de verdad para:
        - salario diario usado por nómina
        - sede asociada a la plaza vigente
        """
        plazas_ocupadas = self._consultar_plazas_ocupadas_vigentes(
            empresa_id=empresa_id,
            fecha_referencia=fecha_referencia,
            contrato_id=contrato_id,
        )

        snapshot_por_empleado: dict[int, dict[str, object]] = {}
        for item in plazas_ocupadas:
            empleado_id = item.get("empleado_id")
            if empleado_id is None:
                continue
            if empleado_id in snapshot_por_empleado:
                continue
            snapshot_por_empleado[int(empleado_id)] = {
                "plaza_id": item.get("id"),
                "sede_id": item.get("sede_id"),
                "salario_diario": self._salario_diario_desde_mensual(
                    item.get("salario_mensual")
                ),
                "tipo_jornada": self._normalizar_tipo_jornada(
                    item.get("tipo_jornada")
                ),
                "factor_jornada": self._normalizar_factor_jornada(
                    item.get("factor_jornada"),
                    item.get("tipo_jornada"),
                ),
            }

        return snapshot_por_empleado

    def _actualizar_total_empleados_periodo(self, periodo_id: int, total_empleados: int) -> None:
        """Mantiene sincronizado el snapshot agregado del período."""
        self.supabase.table(self.tabla).update({
            'total_empleados': total_empleados,
        }).eq('id', periodo_id).execute()

    def _consultar_empleados_periodo(self, periodo_id: int) -> list[dict]:
        """Consulta los recibos del período con nombre y clave del empleado."""
        periodo_result = (
            self.supabase.table(self.tabla)
            .select(
                "empresa_id, contrato_id, fecha_fin, fecha_pago, periodicidad, "
                "regla_calculo_quincenal, listo_para_timbrar, "
                "total_empleados_con_observaciones_fiscales"
            )
            .eq("id", periodo_id)
            .limit(1)
            .execute()
        )
        periodo = (periodo_result.data or [{}])[0]
        plaza_por_empleado = self._mapear_plaza_vigente_por_empleado(
            empresa_id=int(periodo.get("empresa_id") or 0),
            fecha_referencia=periodo.get("fecha_fin") or date.today().isoformat(),
            contrato_id=periodo.get("contrato_id"),
        ) if periodo.get("empresa_id") else {}

        sede_ids = {
            int(snapshot.get("sede_id"))
            for snapshot in plaza_por_empleado.values()
            if snapshot.get("sede_id") is not None
        }
        sedes_map: dict[int, str] = {}
        if sede_ids:
            try:
                sedes_result = (
                    self.supabase.table("sedes")
                    .select("id, nombre, nombre_corto")
                    .in_("id", list(sede_ids))
                    .execute()
                )
                sedes_map = {
                    int(sede.get("id")): normalizar_mayusculas(
                        str(sede.get("nombre_corto") or "").strip()
                        or str(sede.get("nombre") or "").strip()
                        or "Sin sede"
                    )
                    for sede in (sedes_result.data or [])
                    if sede.get("id") is not None
                }
            except Exception as exc:
                logger.warning(
                    "No se pudo resolver la sede de plazas del período %s: %s",
                    periodo_id,
                    exc,
                )

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
            snapshot_plaza = plaza_por_empleado.get(int(r.get("empleado_id") or 0), {})
            sede_id = snapshot_plaza.get("sede_id")
            r["sede_nombre"] = (
                sedes_map.get(int(sede_id), "SIN SEDE")
                if sede_id is not None
                else "SIN SEDE"
            )
            r["dias_trabajados_ui"] = self._dias_trabajados_ui_periodo(
                periodo.get("periodicidad"),
                periodo.get("regla_calculo_quincenal"),
                r.get("dias_trabajados"),
            )
            observaciones = r.get("observaciones_fiscales") or []
            r["observaciones_fiscales"] = observaciones
            r["tiene_observaciones_fiscales"] = bool(observaciones)
            r["tiene_errores_fiscales"] = any(
                str(item.get("severity") or "").lower() == "error"
                for item in observaciones
                if isinstance(item, dict)
            )
            r["observaciones_fiscales_resumen"] = " · ".join(
                str(item.get("mensaje") or "").strip()
                for item in observaciones
                if isinstance(item, dict) and str(item.get("mensaje") or "").strip()
            )
            r["tipo_jornada"] = self._normalizar_tipo_jornada(r.get("tipo_jornada"))
            r["tipo_jornada_label"] = TipoJornadaPlaza(r["tipo_jornada"]).descripcion
            items.append(r)
        return items

    def _adjuntar_descuentos_rrhh_periodo(self, items: list[dict]) -> list[dict]:
        """Anexa badges de descuentos RRHH capturados para el período."""
        nomina_empleado_ids = [item.get("id") for item in items if item.get("id") is not None]
        if not nomina_empleado_ids:
            return items

        try:
            result = (
                self.supabase.table("nomina_movimientos")
                .select(
                    "nomina_empleado_id, monto, es_automatico, "
                    "conceptos_nomina(clave, nombre)"
                )
                .in_("nomina_empleado_id", nomina_empleado_ids)
                .eq("origen", "RRHH")
                .execute()
            )
        except Exception as exc:
            logger.warning(
                "No se pudieron adjuntar descuentos RRHH del período: %s",
                exc,
            )
            for item in items:
                item["descuentos_rrhh"] = []
            return items

        descuentos_por_nomina: dict[int, list[dict]] = defaultdict(list)
        for row in (result.data or []):
            concepto = row.get("conceptos_nomina", {}) or {}
            clave = str(concepto.get("clave") or "").strip().upper()
            meta = DESCUENTOS_RECURRENTES_POR_CLAVE.get(clave)
            if meta is None:
                continue

            nomina_empleado_id = row.get("nomina_empleado_id")
            if nomina_empleado_id is None:
                continue

            monto_fmt = formatear_moneda(str(row.get("monto") or 0))
            origen_label = "Perfil empleado" if row.get("es_automatico") else "RRHH manual"
            descuentos_por_nomina[int(nomina_empleado_id)].append(
                {
                    "concepto_clave": clave,
                    "concepto_nombre": concepto.get("nombre") or meta["nombre"],
                    "badge": meta["badge"],
                    "color_scheme": meta["color_scheme"],
                    "monto_fmt": monto_fmt,
                    "es_automatico": bool(row.get("es_automatico")),
                    "origen_label": origen_label,
                    "tooltip": f'{meta["nombre"]} · {monto_fmt} · {origen_label}',
                }
            )

        for item in items:
            descuentos = descuentos_por_nomina.get(int(item.get("id") or 0), [])
            descuentos.sort(
                key=lambda descuento: int(
                    DESCUENTOS_RECURRENTES_POR_CLAVE.get(
                        descuento["concepto_clave"],
                        {},
                    ).get("orden", 999)
                )
            )
            item["descuentos_rrhh"] = descuentos

        return items

    def _rango_catalogo_periodos(self) -> tuple[date, date]:
        """Ventana del select: solo el mes actual."""
        hoy = date.today()
        return date(hoy.year, hoy.month, 1), date(
            hoy.year,
            hoy.month,
            monthrange(hoy.year, hoy.month)[1],
        )

    def _duplicated_period_error(self, nombre: Optional[str] = None) -> DuplicateError:
        """Mensaje canónico para colisión de períodos."""
        return DuplicateError(
            "Ya existe una nómina para ese período en la empresa.",
            field="periodo_key",
            value=nombre,
        )

    @staticmethod
    def _leer_config(config: object, campo: str, default):
        valor = getattr(config, campo, default)
        return default if valor is None else valor

    def _periodicidad_configurada(self, config: object) -> str:
        tipo_nomina = self._leer_config(
            config,
            "tipo_nomina",
            PeriodicidadNomina.QUINCENAL.value,
        )
        if isinstance(tipo_nomina, PeriodicidadNomina):
            return tipo_nomina.value
        return str(tipo_nomina or PeriodicidadNomina.QUINCENAL.value)

    def _contexto_politica_nomina(self, config: object) -> tuple[str, dict[str, int]]:
        """Normaliza periodicidad y defaults de pago para helpers de periodos."""
        return self._periodicidad_configurada(config), {
            "dia_pago_primera_quincena": self._leer_config(
                config,
                "dia_pago_primera_quincena",
                15,
            ),
            "dia_pago_segunda_quincena": self._leer_config(
                config,
                "dia_pago_segunda_quincena",
                0,
            ),
            "dia_pago_semanal": self._leer_config(config, "dia_pago_semanal", 5),
            "dia_pago_mensual": self._leer_config(config, "dia_pago_mensual", 0),
        }

    def _regla_calculo_quincenal_configurada(self, config: object) -> str:
        valor = self._leer_config(
            config,
            "regla_calculo_quincenal",
            ReglaCalculoQuincenal.MIXTA.value,
        )
        if isinstance(valor, ReglaCalculoQuincenal):
            return valor.value
        try:
            return ReglaCalculoQuincenal(str(valor or "").upper()).value
        except ValueError:
            logger.warning(
                "Regla de cálculo quincenal inválida en configuración: %s. Se usa MIXTA.",
                valor,
            )
            return ReglaCalculoQuincenal.MIXTA.value

    def _snapshot_regla_calculo_quincenal(
        self,
        periodicidad: str | PeriodicidadNomina,
        config: object,
    ) -> Optional[str]:
        periodicidad_value = (
            periodicidad.value if isinstance(periodicidad, PeriodicidadNomina)
            else str(periodicidad or PeriodicidadNomina.QUINCENAL.value)
        )
        if periodicidad_value != PeriodicidadNomina.QUINCENAL.value:
            return None
        return self._regla_calculo_quincenal_configurada(config)

    def _dias_trabajados_ui_periodo(
        self,
        periodicidad: object,
        regla_calculo_quincenal: object,
        dias_trabajados: object,
    ) -> int:
        """Topa a 15 solo la vista de preparación quincenal con regla MIXTA."""
        try:
            dias = max(int(dias_trabajados or 0), 0)
        except (TypeError, ValueError):
            return 0

        periodicidad_value = (
            periodicidad.value
            if isinstance(periodicidad, PeriodicidadNomina)
            else str(periodicidad or "")
        )
        if periodicidad_value != PeriodicidadNomina.QUINCENAL.value:
            return dias

        regla = (
            regla_calculo_quincenal.value
            if isinstance(regla_calculo_quincenal, ReglaCalculoQuincenal)
            else str(
                regla_calculo_quincenal or ReglaCalculoQuincenal.MIXTA.value
            ).upper()
        )
        if regla == ReglaCalculoQuincenal.MIXTA.value:
            return min(dias, 15)
        return dias

    async def _asegurar_modulo_nomina_activo(self, empresa_id: int) -> None:
        from app.services import empresa_service

        empresa = await empresa_service.obtener_por_id(empresa_id)
        if not bool(getattr(empresa, "gestion_nomina_activa", False)):
            raise BusinessRuleError(
                "La gestión de nómina no está activa para la empresa seleccionada."
            )

    async def _obtener_configuracion_nomina(
        self,
        empresa_id: int,
        *,
        validar_modulo: bool = True,
    ):
        if validar_modulo:
            await self._asegurar_modulo_nomina_activo(empresa_id)
        return await configuracion_operativa_service.obtener_o_crear_default(empresa_id)

    async def _obtener_contrato_nomina_id_configurado(
        self,
        empresa_id: int,
        *,
        requerido: bool = False,
    ) -> Optional[int]:
        config = await self._obtener_configuracion_nomina(empresa_id)
        contrato_id = self._leer_config(config, "contrato_nomina_id", None)
        if contrato_id is None:
            if requerido:
                raise BusinessRuleError(
                    "Configura un contrato base de nómina antes de generar periodos."
                )
            return None

        await configuracion_operativa_service.validar_contrato_nomina(
            empresa_id,
            int(contrato_id),
        )
        return int(contrato_id)

    async def _resolver_contrato_nomina_id_periodo(
        self,
        empresa_id: int,
        contrato_id: Optional[int],
    ) -> int:
        if contrato_id is not None:
            await configuracion_operativa_service.validar_contrato_nomina(
                empresa_id,
                int(contrato_id),
            )
            return int(contrato_id)

        contrato_configurado = await self._obtener_contrato_nomina_id_configurado(
            empresa_id,
            requerido=True,
        )
        if contrato_configurado is None:
            raise BusinessRuleError(
                "Selecciona un contrato base de nómina antes de generar periodos."
            )
        return int(contrato_configurado)

    async def _sincronizar_contrato_nomina_configurado(
        self,
        empresa_id: int,
        contrato_id: Optional[int],
    ) -> None:
        if contrato_id is None:
            return

        await configuracion_operativa_service.crear_o_actualizar(
            empresa_id,
            ConfiguracionOperativaEmpresaUpdate(
                contrato_nomina_id=int(contrato_id),
            ),
        )

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
        regla_calculo_quincenal: Optional[str] = None,
        contrato_id: Optional[int] = None,
        fecha_pago: Optional[date] = None,
        notas: Optional[str] = None,
        creado_por: Optional[str] = None,
        creado_por_nombre: Optional[str] = None,
        zona_frontera: Optional[bool] = None,
        aplicar_art_36: Optional[bool] = None,
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
        if regla_calculo_quincenal is not None:
            datos['regla_calculo_quincenal'] = regla_calculo_quincenal
        if contrato_id is not None:
            datos['contrato_id'] = contrato_id
        if fecha_pago is not None:
            datos['fecha_pago'] = fecha_pago.isoformat()
        if notas is not None:
            datos['notas'] = notas
        if creado_por:
            datos['creado_por'] = creado_por
        if creado_por_nombre:
            datos['creado_por_nombre'] = creado_por_nombre
        if zona_frontera is not None:
            datos['zona_frontera'] = zona_frontera
        if aplicar_art_36 is not None:
            datos['aplicar_art_36'] = aplicar_art_36

        try:
            result = self.supabase.table(self.tabla).insert(datos).execute()
            logger.info(f"Período '{nombre}' creado (empresa {empresa_id})")
            return result.data[0]
        except DuplicateError:
            raise
        except Exception as e:
            error_text = str(e).lower()
            if "duplicate" in error_text or "unique" in error_text:
                logger.warning(
                    "Período duplicado para empresa %s [%s - %s]",
                    empresa_id,
                    fecha_inicio,
                    fecha_fin,
                )
                raise self._duplicated_period_error(nombre)
            logger.error(f"Error creando período '{nombre}': {e}")
            raise DatabaseError(f"Error creando período de nómina: {e}")

    async def listar_periodos_disponibles(self, empresa_id: int) -> list[dict]:
        """Retorna catálogo de periodos disponibles según la política activa."""
        try:
            config = await self._obtener_configuracion_nomina(empresa_id)
            periodicidad, politica_kwargs = self._contexto_politica_nomina(config)
            fecha_inicio_catalogo, fecha_fin_catalogo = self._rango_catalogo_periodos()

            result = (
                self.supabase.table(self.tabla)
                .select('fecha_inicio, fecha_fin')
                .eq('empresa_id', empresa_id)
                .gte('fecha_inicio', fecha_inicio_catalogo.isoformat())
                .lte('fecha_fin', fecha_fin_catalogo.isoformat())
                .execute()
            )
            rangos_existentes = {
                (
                    item.get('fecha_inicio'),
                    item.get('fecha_fin'),
                )
                for item in (result.data or [])
                if item.get('fecha_inicio') and item.get('fecha_fin')
            }

            catalogo = generar_catalogo_periodos(
                periodicidad,
                fecha_inicio_catalogo=fecha_inicio_catalogo,
                fecha_fin_catalogo=fecha_fin_catalogo,
                **politica_kwargs,
            )

            return [
                periodo.to_option()
                for periodo in catalogo
                if (
                    periodo.fecha_inicio.isoformat(),
                    periodo.fecha_fin.isoformat(),
                ) not in rangos_existentes
            ]
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(
                "Error listando periodos disponibles para empresa %s: %s",
                empresa_id,
                e,
            )
            raise DatabaseError(f"Error listando periodos disponibles: {e}")

    async def listar_quincenas_disponibles(self, empresa_id: int) -> list[dict]:
        """Compatibilidad: devuelve el catálogo configurado de periodos."""
        return await self.listar_periodos_disponibles(empresa_id)

    async def crear_periodo_configurado(
        self,
        empresa_id: int,
        periodo_key: str,
        contrato_id: Optional[int] = None,
        fecha_pago_override: Optional[date] = None,
        usuario_id: Optional[str] = None,
        usuario_nombre: Optional[str] = None,
        notas: Optional[str] = None,
    ) -> dict:
        """Crea un periodo usando la política activa de nómina de la empresa."""
        config = await self._obtener_configuracion_nomina(empresa_id)
        config_fiscal = await self._obtener_configuracion_fiscal(empresa_id)
        periodicidad, politica_kwargs = self._contexto_politica_nomina(config)
        contrato_id_resuelto = await self._resolver_contrato_nomina_id_periodo(
            empresa_id,
            contrato_id,
        )
        periodo_calculado = resolver_periodo_por_key(
            periodo_key,
            periodicidad,
            **politica_kwargs,
        )

        fecha_pago = fecha_pago_override or periodo_calculado.fecha_pago_sugerida
        if fecha_pago < periodo_calculado.fecha_inicio:
            raise BusinessRuleError(
                "fecha_pago debe ser mayor o igual a la fecha de inicio del periodo"
            )

        periodo = await self.crear_periodo(
            empresa_id=empresa_id,
            nombre=periodo_calculado.nombre,
            fecha_inicio=periodo_calculado.fecha_inicio,
            fecha_fin=periodo_calculado.fecha_fin,
            periodicidad=periodo_calculado.periodicidad.value,
            regla_calculo_quincenal=self._snapshot_regla_calculo_quincenal(
                periodo_calculado.periodicidad,
                config,
            ),
            contrato_id=contrato_id_resuelto,
            fecha_pago=fecha_pago,
            notas=notas,
            creado_por=usuario_id,
            creado_por_nombre=usuario_nombre,
            zona_frontera=bool(getattr(config_fiscal, "zona_frontera", False)),
            aplicar_art_36=bool(getattr(config_fiscal, "aplicar_art_36", True)),
        )
        await self._sincronizar_contrato_nomina_configurado(
            empresa_id,
            contrato_id_resuelto,
        )
        total_empleados = await self.poblar_empleados(periodo['id'])
        return {
            **periodo,
            'total_empleados_poblados': total_empleados,
        }

    async def crear_periodo_quincenal(
        self,
        empresa_id: int,
        quincena_key: str,
        fecha_pago_override: Optional[date] = None,
        usuario_id: Optional[str] = None,
        usuario_nombre: Optional[str] = None,
        contrato_id: Optional[int] = None,
        notas: Optional[str] = None,
    ) -> dict:
        """Compatibilidad con el flujo quincenal previo."""
        config = await self._obtener_configuracion_nomina(empresa_id)
        config_fiscal = await self._obtener_configuracion_fiscal(empresa_id)
        contrato_nomina_id = await self._resolver_contrato_nomina_id_periodo(
            empresa_id,
            contrato_id,
        )
        quincena = resolver_quincena_por_key(
            quincena_key=quincena_key,
            dia_pago_primera_quincena=self._leer_config(
                config,
                "dia_pago_primera_quincena",
                15,
            ),
            dia_pago_segunda_quincena=self._leer_config(
                config,
                "dia_pago_segunda_quincena",
                0,
            ),
        )

        fecha_pago = fecha_pago_override or quincena.fecha_pago_sugerida
        if fecha_pago < quincena.fecha_inicio:
            raise BusinessRuleError(
                "fecha_pago debe ser mayor o igual a la fecha de inicio de la quincena"
            )

        periodo = await self.crear_periodo(
            empresa_id=empresa_id,
            nombre=quincena.nombre,
            fecha_inicio=quincena.fecha_inicio,
            fecha_fin=quincena.fecha_fin,
            periodicidad='QUINCENAL',
            regla_calculo_quincenal=self._regla_calculo_quincenal_configurada(config),
            contrato_id=contrato_nomina_id,
            fecha_pago=fecha_pago,
            notas=notas,
            creado_por=usuario_id,
            creado_por_nombre=usuario_nombre,
            zona_frontera=bool(getattr(config_fiscal, "zona_frontera", False)),
            aplicar_art_36=bool(getattr(config_fiscal, "aplicar_art_36", True)),
        )
        await self._sincronizar_contrato_nomina_configurado(
            empresa_id,
            contrato_nomina_id,
        )
        total_empleados = await self.poblar_empleados(periodo['id'])
        return {
            **periodo,
            'total_empleados_poblados': total_empleados,
        }

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
        contrato_id = periodo.get('contrato_id')
        fecha_inicio = periodo['fecha_inicio']
        fecha_fin = periodo['fecha_fin']

        try:
            plaza_snapshot_por_empleado = self._mapear_plaza_vigente_por_empleado(
                empresa_id=empresa_id,
                fecha_referencia=fecha_fin,
                contrato_id=contrato_id,
            )
            empleado_ids_con_plaza = list(plaza_snapshot_por_empleado.keys())
            if not empleado_ids_con_plaza:
                logger.warning(
                    "No hay empleados con plaza ocupada vigente para empresa %s en período %s",
                    empresa_id,
                    periodo_id,
                )
                self._actualizar_total_empleados_periodo(periodo_id, 0)
                return 0

            fiscal_periodo = await self._resolver_contexto_fiscal_periodo(periodo)
            contexto_fiscal = fiscal_periodo["contexto"]

            # 1. Empleados ACTIVOS de la empresa con plaza vigente
            res_emp = (
                self.supabase.table('empleados')
                .select('id, nombre, apellido_paterno, banco, clabe_interbancaria')
                .eq('empresa_id', empresa_id)
                .eq('estatus', 'ACTIVO')
                .in_('id', empleado_ids_con_plaza)
                .execute()
            )
            empleados = res_emp.data or []
            if not empleados:
                logger.warning(
                    "No hay empleados ACTIVOS con plaza vigente para empresa %s",
                    empresa_id,
                )
                self._actualizar_total_empleados_periodo(periodo_id, 0)
                return 0

            empleado_ids = [emp['id'] for emp in empleados if emp.get('id') is not None]
            empleados_con_plaza_inactivos = sorted(set(empleado_ids_con_plaza) - set(empleado_ids))
            if empleados_con_plaza_inactivos:
                logger.warning(
                    "Período %s: %s empleado(s) con plaza vigente no están ACTIVO en empleados: %s",
                    periodo_id,
                    len(empleados_con_plaza_inactivos),
                    empleados_con_plaza_inactivos,
                )
            empleados_sin_salario = [
                emp_id
                for emp_id in empleado_ids
                if float(
                    plaza_snapshot_por_empleado.get(emp_id, {}).get("salario_diario") or 0
                ) <= 0
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
            )
            if contrato_id is not None:
                res_asist = res_asist.eq('contrato_id', contrato_id)
            res_asist = res_asist.execute()
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

                dias_faltas = sum(
                    1
                    for a in asistencias
                    if a['tipo_registro'] in _TIPOS_INASISTENCIA_NO_PAGADA
                )
                dias_incapacidad = sum(
                    1 for a in asistencias if a['tipo_registro'] in _TIPOS_INCAPACIDAD
                )
                dias_trabajados = self._calcular_dias_trabajados_nomina(
                    dias_periodo=dias_periodo,
                    dias_faltas=dias_faltas,
                    dias_incapacidad=dias_incapacidad,
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

                snapshot_plaza = plaza_snapshot_por_empleado.get(emp_id, {})
                salario_diario = float(snapshot_plaza.get("salario_diario") or 0.0)
                if salario_diario <= 0:
                    empleados_omitidos.append(emp_id)
                    continue

                tipo_jornada = self._normalizar_tipo_jornada(
                    snapshot_plaza.get("tipo_jornada")
                )
                factor_jornada = self._normalizar_factor_jornada(
                    snapshot_plaza.get("factor_jornada"),
                    tipo_jornada,
                )
                salario_minimo_diario = Decimal(
                    str(contexto_fiscal.salario_minimo_diario_aplicable or 0)
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                salario_minimo_proporcional = self._salario_minimo_proporcional_diario(
                    salario_minimo_diario,
                    factor_jornada,
                )
                observaciones_fiscales: list[dict[str, str]] = []
                if not contexto_fiscal.vigencia_soportada and contexto_fiscal.mensaje_vigencia:
                    observaciones_fiscales.append(
                        self._observacion_fiscal(
                            codigo="CATALOGO_FISCAL_NO_VIGENTE",
                            mensaje=contexto_fiscal.mensaje_vigencia,
                            severidad="error",
                        )
                    )

                salario_diario_decimal = Decimal(str(salario_diario)).quantize(
                    Decimal("0.01"),
                    rounding=ROUND_HALF_UP,
                )
                if salario_diario_decimal < salario_minimo_proporcional and not Tolerancias.es_salario_minimo(
                    salario_diario_decimal,
                    salario_minimo_proporcional,
                ):
                    observaciones_fiscales.append(
                        self._observacion_fiscal(
                            codigo="SALARIO_BAJO_MINIMO_PROPORCIONAL",
                            mensaje=(
                                "El salario diario de la plaza está por debajo del mínimo "
                                "proporcional para la jornada capturada."
                            ),
                            severidad="warning",
                        )
                    )

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
                    'tipo_jornada': tipo_jornada,
                    'factor_jornada': factor_jornada,
                    'salario_minimo_diario_aplicable': float(salario_minimo_diario),
                    'es_salario_minimo_art36': False,
                    'imss_obrero_absorbido': 0.0,
                    'listo_para_timbrar': False,
                    'observaciones_fiscales': observaciones_fiscales,
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

    async def _materializar_descuentos_recurrentes_rrhh(self, periodo: dict) -> int:
        """Genera snapshot de descuentos recurrentes vigentes al iniciar preparación."""
        from app.services.empleado_descuento_recurrente_service import (
            empleado_descuento_recurrente_service,
        )

        periodo_id = int(periodo["id"])
        items = self._consultar_empleados_periodo(periodo_id)
        if not items:
            total = await self.poblar_empleados(periodo_id)
            if total <= 0:
                return 0
            items = self._consultar_empleados_periodo(periodo_id)
            if not items:
                return 0

        empleado_ids = [
            int(item["empleado_id"])
            for item in items
            if item.get("empleado_id") is not None
        ]
        if not empleado_ids:
            return 0

        fecha_inicio = date.fromisoformat(str(periodo["fecha_inicio"]))
        fecha_fin = date.fromisoformat(str(periodo["fecha_fin"]))
        descuentos_vigentes = await empleado_descuento_recurrente_service.obtener_vigentes_en_rango(
            empleado_ids,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        if not descuentos_vigentes:
            return 0

        conceptos_result = (
            self.supabase.table("conceptos_nomina")
            .select("id, clave")
            .in_("clave", list(DESCUENTOS_RECURRENTES_CLAVES))
            .execute()
        )
        concepto_ids = {
            str(item.get("clave") or "").strip().upper(): item.get("id")
            for item in (conceptos_result.data or [])
            if item.get("id") is not None
        }
        if not concepto_ids:
            logger.warning(
                "Período %s: no se encontraron conceptos de nómina para descuentos RRHH",
                periodo_id,
            )
            return 0

        nomina_empleado_ids = [
            int(item["id"])
            for item in items
            if item.get("id") is not None
        ]
        existentes_result = (
            self.supabase.table("nomina_movimientos")
            .select("nomina_empleado_id, concepto_id")
            .in_("nomina_empleado_id", nomina_empleado_ids)
            .eq("origen", "RRHH")
            .execute()
        )
        existentes = {
            (
                int(item.get("nomina_empleado_id")),
                int(item.get("concepto_id")),
            )
            for item in (existentes_result.data or [])
            if item.get("nomina_empleado_id") is not None
            and item.get("concepto_id") is not None
        }

        payload: list[dict] = []
        for item in items:
            nomina_empleado_id = item.get("id")
            empleado_id = item.get("empleado_id")
            if nomina_empleado_id is None or empleado_id is None:
                continue

            for descuento in descuentos_vigentes.get(int(empleado_id), []):
                concepto_id = concepto_ids.get(descuento.concepto_clave)
                if concepto_id is None:
                    continue

                llave = (int(nomina_empleado_id), int(concepto_id))
                if llave in existentes:
                    continue

                payload.append(
                    {
                        "nomina_empleado_id": int(nomina_empleado_id),
                        "concepto_id": int(concepto_id),
                        "tipo": "DEDUCCION",
                        "origen": "RRHH",
                        "monto": float(descuento.monto_periodico),
                        "monto_gravable": 0.0,
                        "monto_exento": 0.0,
                        "es_automatico": True,
                        "notas": descuento.notas or None,
                    }
                )
                existentes.add(llave)

        if not payload:
            return 0

        self.supabase.table("nomina_movimientos").insert(payload).execute()
        logger.info(
            "Período %s: se generaron %s descuento(s) recurrente(s) RRHH",
            periodo_id,
            len(payload),
        )
        return len(payload)

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

        if nuevo_estatus == 'EN_PREPARACION_RRHH':
            await self._materializar_descuentos_recurrentes_rrhh(periodo)
        elif nuevo_estatus == 'CERRADO' and not bool(periodo.get('listo_para_timbrar', False)):
            total_obs = int(periodo.get('total_empleados_con_observaciones_fiscales') or 0)
            detalle = (
                f" Hay {total_obs} empleado(s) con observaciones fiscales."
                if total_obs > 0
                else ""
            )
            raise BusinessRuleError(
                "El período no está listo para timbrar y no puede cerrarse."
                + detalle
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
        estatuses: Optional[list[str]] = None,
    ) -> list[dict]:
        """Lista períodos de una empresa."""
        try:
            query = (
                self.supabase.table(self.tabla)
                .select('*')
                .eq('empresa_id', empresa_id)
                .order('fecha_inicio', desc=True)
            )
            if estatus:
                query = query.eq('estatus', estatus)
            elif estatuses:
                query = query.in_('estatus', estatuses)
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
                return self._adjuntar_descuentos_rrhh_periodo(items)

            periodo = await self.obtener_periodo(periodo_id)
            if periodo.get('estatus') in _ESTATUS_REPOBLABLES:
                total = await self.poblar_empleados(periodo_id)
                if total > 0:
                    return self._adjuntar_descuentos_rrhh_periodo(
                        self._consultar_empleados_periodo(periodo_id)
                    )

            return []
        except Exception as e:
            logger.error(f"Error obteniendo empleados del período {periodo_id}: {e}")
            raise DatabaseError(f"Error obteniendo empleados del período: {e}")

    async def obtener_resumen_operativo_actual(
        self,
        empresa_id: int,
        *,
        fecha_referencia: Optional[date] = None,
        contrato_id: Optional[int] = None,
    ) -> dict:
        """Cards operativas de /portal/nominas calculadas por calendario actual."""
        config = await self._obtener_configuracion_nomina(empresa_id)
        periodicidad, politica_kwargs = self._contexto_politica_nomina(config)
        periodo_actual = detectar_periodo_actual(
            periodicidad,
            fecha_referencia=fecha_referencia,
            **politica_kwargs,
        )

        resumen = {
            "periodicidad": periodicidad,
            "periodo_actual_titulo": periodo_actual.titulo_actual,
            "periodo_actual_rango": periodo_actual.rango_actual_label,
            "periodo_actual_label": periodo_actual.label,
            "periodo_actual_inicio": periodo_actual.fecha_inicio.isoformat(),
            "periodo_actual_fin": periodo_actual.fecha_fin.isoformat(),
            "total_plazas": 0,
            "activos": 0,
            "inasistencias": 0,
            "incapacidades": 0,
            "warning": "",
        }

        contrato_nomina_id = contrato_id
        if contrato_nomina_id is None:
            contrato_nomina_id = self._leer_config(config, "contrato_nomina_id", None)
        if contrato_nomina_id is None:
            resumen["warning"] = (
                "Selecciona un contrato base de nómina para calcular plazas e incidencias."
            )
            return resumen

        try:
            await configuracion_operativa_service.validar_contrato_nomina(
                empresa_id,
                int(contrato_nomina_id),
            )
        except BusinessRuleError as e:
            resumen["warning"] = str(e)
            return resumen

        from app.services import plaza_service

        totales_plaza = await plaza_service.calcular_totales_contrato(int(contrato_nomina_id))
        resumen["total_plazas"] = int(totales_plaza.total_plazas or 0)
        resumen["activos"] = int(totales_plaza.plazas_ocupadas or 0)

        faltas_result = (
            self.supabase.table("registros_asistencia")
            .select("id", count="exact")
            .eq("empresa_id", empresa_id)
            .eq("contrato_id", int(contrato_nomina_id))
            .in_("tipo_registro", list(_TIPOS_INASISTENCIA_NO_PAGADA))
            .gte("fecha", periodo_actual.fecha_inicio.isoformat())
            .lte("fecha", periodo_actual.fecha_fin.isoformat())
            .execute()
        )
        resumen["inasistencias"] = int(faltas_result.count or 0)

        incapacidades_result = (
            self.supabase.table("registros_asistencia")
            .select("id", count="exact")
            .eq("empresa_id", empresa_id)
            .eq("contrato_id", int(contrato_nomina_id))
            .in_("tipo_registro", list(_TIPOS_INCAPACIDAD))
            .gte("fecha", periodo_actual.fecha_inicio.isoformat())
            .lte("fecha", periodo_actual.fecha_fin.isoformat())
            .execute()
        )
        resumen["incapacidades"] = int(incapacidades_result.count or 0)
        return resumen


# Singleton
nomina_periodo_service = NominaPeriodoService()
