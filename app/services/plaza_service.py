"""
Servicio de aplicación para gestión de Plazas.

Modelo plazas-first:
- el contrato define cuántas plazas existen
- si el contrato desglosa categorías, la plaza se materializa o sincroniza con ellas
- la sede, el salario operativo y la asignación de personal se gestionan desde plazas
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Optional

from app.core.enums import EstatusPlaza, TipoJornadaPlaza
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.entities.plaza import (
    Plaza,
    PlazaCreate,
    PlazaResumen,
    PlazaUpdate,
    ResumenPlazasCategoria,
    ResumenPlazasContrato,
)
from app.repositories.plaza_repository import SupabasePlazaRepository

logger = logging.getLogger(__name__)

try:
    import sys

    services_pkg = sys.modules.get("app.services")
    if services_pkg is not None and not hasattr(services_pkg, "contrato_categoria_service"):
        from app.services.contrato_categoria_service import (
            contrato_categoria_service as _contrato_categoria_service,
        )

        services_pkg.contrato_categoria_service = _contrato_categoria_service
except Exception:
    pass


class PlazaService:
    """Orquesta validaciones y operaciones de negocio sobre plazas."""

    def __init__(self, repository=None):
        if repository is None:
            repository = SupabasePlazaRepository()
        self.repository = repository

    def _normalizar_jornada(
        self,
        tipo_jornada: TipoJornadaPlaza | str | None,
        factor_jornada: Decimal | None,
    ) -> tuple[TipoJornadaPlaza, Decimal]:
        try:
            tipo = (
                tipo_jornada
                if isinstance(tipo_jornada, TipoJornadaPlaza)
                else TipoJornadaPlaza(str(tipo_jornada or "").upper())
            )
        except ValueError:
            tipo = TipoJornadaPlaza.COMPLETA

        if tipo == TipoJornadaPlaza.COMPLETA:
            return tipo, Decimal("1.0")
        if tipo == TipoJornadaPlaza.MEDIA_JORNADA:
            return tipo, Decimal("0.5")

        if factor_jornada is None:
            raise BusinessRuleError(
                "Captura el factor de jornada para plazas por horas."
            )
        if factor_jornada <= 0 or factor_jornada > 1:
            raise BusinessRuleError(
                "El factor de jornada debe ser mayor a 0 y menor o igual a 1."
            )
        return tipo, factor_jornada

    async def obtener_por_id(self, id: int) -> Plaza:
        return await self.repository.obtener_por_id(id)

    async def obtener_por_contrato(
        self,
        contrato_id: int,
        incluir_canceladas: bool = False,
    ) -> list[Plaza]:
        return await self.repository.obtener_por_contrato(contrato_id, incluir_canceladas)

    async def obtener_por_estatus(
        self,
        estatus: EstatusPlaza,
        limite: int = 100,
    ) -> list[PlazaResumen]:
        resumen_data = await self.repository.obtener_resumen_por_estatus(estatus, limite)
        return [self._map_resumen(item) for item in resumen_data]

    async def obtener_resumen_de_contrato(self, contrato_id: int) -> list[PlazaResumen]:
        resumen_data = await self.repository.obtener_resumen_por_contrato(contrato_id)
        return [self._map_resumen(item) for item in resumen_data]

    async def obtener_resumen_de_categoria(
        self,
        contrato_id: int,
        categoria_puesto_id: int,
        incluir_canceladas: bool = False,
    ) -> list[PlazaResumen]:
        resumen_data = await self.repository.obtener_resumen_por_categoria(
            contrato_id,
            categoria_puesto_id,
            incluir_canceladas,
        )
        return [self._map_resumen(item) for item in resumen_data]

    async def calcular_totales_contrato(self, contrato_id: int) -> ResumenPlazasContrato:
        totales = await self.repository.obtener_totales_por_contrato(contrato_id)
        return ResumenPlazasContrato(
            contrato_id=contrato_id,
            total_plazas=totales["total_plazas"],
            plazas_vacantes=totales["plazas_vacantes"],
            plazas_ocupadas=totales["plazas_ocupadas"],
            plazas_suspendidas=totales["plazas_suspendidas"],
            plazas_canceladas=totales["plazas_canceladas"],
            plazas_categorizadas=totales["plazas_categorizadas"],
            plazas_sin_categoria=totales["plazas_sin_categoria"],
            cantidad_plazas_minima=totales["cantidad_plazas_minima"],
            cantidad_plazas_maxima=totales["cantidad_plazas_maxima"],
            plazas_desfase=totales["plazas_desfase"],
            costo_total_mensual=totales["costo_total_mensual"],
        )

    async def obtener_resumen_categorias_con_plazas(
        self,
        empresa_id: Optional[int] = None,
    ) -> list[dict]:
        return await self.repository.obtener_resumen_categorias_con_plazas(empresa_id)

    async def obtener_resumen_contratos_con_plazas(
        self,
        empresa_id: Optional[int] = None,
        solo_activos: bool = False,
    ) -> list[dict]:
        return await self.repository.obtener_resumen_contratos_con_plazas(
            empresa_id=empresa_id,
            solo_activos=solo_activos,
        )

    async def obtener_empleados_asignados(
        self,
        empresa_id: Optional[int] = None,
    ) -> list[int]:
        return await self.repository.obtener_empleados_asignados(empresa_id)

    async def obtener_cantidad_esperada_por_categoria(
        self,
        contrato_id: int,
        fecha_referencia: Optional[date] = None,
    ) -> dict[int, int]:
        return await self.repository.contar_vigentes_por_categoria(contrato_id, fecha_referencia)

    async def sincronizar_plazas_contrato(
        self,
        contrato_id: int,
        cantidad_plazas_maxima: int,
        fecha_inicio: date,
    ) -> int:
        """Materializa plazas vacantes hasta alcanzar el máximo contractual."""
        plazas_existentes = await self.repository.contar_por_contrato(contrato_id, incluir_canceladas=True)
        faltantes = max(0, cantidad_plazas_maxima - plazas_existentes)
        if faltantes == 0:
            return 0

        siguiente_numero = await self.repository.obtener_siguiente_numero_plaza(contrato_id)
        creadas = 0
        for offset in range(faltantes):
            plaza = Plaza(
                contrato_id=contrato_id,
                sede_id=None,
                categoria_puesto_id=None,
                numero_plaza=siguiente_numero + offset,
                codigo="",
                empleado_id=None,
                fecha_inicio=fecha_inicio,
                fecha_fin=None,
                salario_mensual=Decimal("0"),
                estatus=EstatusPlaza.VACANTE,
                notas="Generada automáticamente desde el contrato",
            )
            await self.repository.crear(plaza)
            creadas += 1

        logger.info(f"Sincronizadas {creadas} plazas para contrato {contrato_id}")
        return creadas

    async def sincronizar_categorias_desde_contrato(self, contrato_id: int) -> int:
        """
        Aplica el desglose por categoría del contrato a las plazas materializadas.

        Regla de negocio:
        - el contrato define la categoría y el costo contractual por categoría
        - la plaza conserva su salario operativo propio; este método no lo modifica
        - solo se reasignan plazas vacantes/libres cuando hace falta cubrir el máximo
          configurado por categoría
        """
        from app.services import contrato_categoria_service

        categorias_contrato = await contrato_categoria_service.obtener_categorias_de_contrato(contrato_id)
        if not categorias_contrato:
            return 0

        plazas = await self.repository.obtener_por_contrato(contrato_id, incluir_canceladas=True)
        if not plazas:
            return 0

        objetivos = {
            item.categoria_puesto_id: int(item.cantidad_maxima or 0)
            for item in categorias_contrato
            if int(item.cantidad_maxima or 0) > 0
        }
        if not objetivos:
            return 0

        conteo_actual: dict[int, int] = {}
        vacantes_sin_categoria: list[Plaza] = []
        vacantes_reasignables_por_categoria: dict[int, list[Plaza]] = {}

        for plaza in sorted(plazas, key=lambda item: item.numero_plaza):
            if plaza.estatus == EstatusPlaza.CANCELADA:
                continue

            categoria_id = plaza.categoria_puesto_id
            if categoria_id is not None:
                conteo_actual[categoria_id] = conteo_actual.get(categoria_id, 0) + 1
                if plaza.estatus == EstatusPlaza.VACANTE and plaza.empleado_id is None:
                    vacantes_reasignables_por_categoria.setdefault(categoria_id, []).append(plaza)
                continue

            if plaza.estatus == EstatusPlaza.VACANTE and plaza.empleado_id is None:
                vacantes_sin_categoria.append(plaza)

        pool_reasignable: list[Plaza] = list(vacantes_sin_categoria)

        for categoria_id, vacantes_categoria in vacantes_reasignables_por_categoria.items():
            objetivo = objetivos.get(categoria_id, 0)
            actual = conteo_actual.get(categoria_id, 0)
            excedente = max(0, actual - objetivo)
            if categoria_id not in objetivos:
                excedente = len(vacantes_categoria)

            if excedente <= 0:
                continue

            seleccionadas = vacantes_categoria[:excedente]
            pool_reasignable.extend(seleccionadas)
            conteo_actual[categoria_id] = max(0, actual - len(seleccionadas))

        actualizadas = 0
        for categoria_contrato in categorias_contrato:
            categoria_id = categoria_contrato.categoria_puesto_id
            objetivo = objetivos.get(categoria_id, 0)
            if objetivo <= 0:
                continue

            faltantes = max(0, objetivo - conteo_actual.get(categoria_id, 0))
            while faltantes > 0 and pool_reasignable:
                plaza = pool_reasignable.pop(0)
                if plaza.categoria_puesto_id == categoria_id:
                    conteo_actual[categoria_id] = conteo_actual.get(categoria_id, 0) + 1
                    faltantes -= 1
                    continue

                plaza.categoria_puesto_id = categoria_id
                await self.repository.actualizar(plaza)
                conteo_actual[categoria_id] = conteo_actual.get(categoria_id, 0) + 1
                actualizadas += 1
                faltantes -= 1

            if faltantes > 0:
                logger.warning(
                    "No fue posible cubrir el maximo por categoria contrato=%s categoria=%s faltantes=%s",
                    contrato_id,
                    categoria_id,
                    faltantes,
                )

        if actualizadas:
            logger.info(
                "Sincronizadas %s plaza(s) por categoria para contrato %s",
                actualizadas,
                contrato_id,
            )

        return actualizadas

    async def crear(self, plaza_create: PlazaCreate) -> Plaza:
        await self._validar_limite_contrato(plaza_create.contrato_id, nueva_cantidad=1)
        if plaza_create.sede_id is not None:
            await self._validar_sede_activa(plaza_create.sede_id)
        if plaza_create.categoria_puesto_id is not None:
            await self._validar_categoria_activa(plaza_create.categoria_puesto_id)
        tipo_jornada, factor_jornada = self._normalizar_jornada(
            plaza_create.tipo_jornada,
            plaza_create.factor_jornada,
        )
        payload = plaza_create.model_dump()
        payload["tipo_jornada"] = tipo_jornada
        payload["factor_jornada"] = factor_jornada
        plaza = Plaza(**payload)
        return await self.repository.crear(plaza)

    async def actualizar(self, id: int, plaza_update: PlazaUpdate) -> Plaza:
        plaza = await self.repository.obtener_por_id(id)
        cambios = plaza_update.model_dump(exclude_unset=True)
        sede_final = cambios.get("sede_id", plaza.sede_id)
        categoria_final = cambios.get("categoria_puesto_id", plaza.categoria_puesto_id)
        if sede_final is not None:
            await self._validar_sede_activa(sede_final)
        if categoria_final is not None:
            await self._validar_categoria_activa(categoria_final)

        for campo, valor in cambios.items():
            setattr(plaza, campo, valor)

        tipo_jornada, factor_jornada = self._normalizar_jornada(
            plaza.tipo_jornada,
            plaza.factor_jornada,
        )
        plaza.tipo_jornada = tipo_jornada
        plaza.factor_jornada = factor_jornada

        if plaza.categoria_puesto_id is None and plaza.empleado_id is not None:
            raise BusinessRuleError(
                "No se puede dejar una plaza ocupada sin categoría asignada"
            )

        if plaza.sede_id is None and plaza.empleado_id is not None:
            raise BusinessRuleError(
                "No se puede dejar una plaza ocupada sin sede asignada"
            )

        if plaza.estatus == EstatusPlaza.OCUPADA and plaza.empleado_id is None:
            raise BusinessRuleError(
                "No se puede marcar una plaza como ocupada sin empleado asignado"
            )

        if plaza.estatus == EstatusPlaza.OCUPADA and plaza.sede_id is None:
            raise BusinessRuleError(
                "No se puede marcar una plaza como ocupada sin sede asignada"
            )

        if plaza.empleado_id is not None and plaza.estatus != EstatusPlaza.OCUPADA:
            raise BusinessRuleError(
                "Una plaza con empleado asignado debe permanecer en estatus OCUPADA"
            )

        return await self.repository.actualizar(plaza)

    async def cancelar(self, id: int) -> Plaza:
        plaza = await self.repository.obtener_por_id(id)
        if plaza.estatus == EstatusPlaza.CANCELADA:
            raise BusinessRuleError("La plaza ya está cancelada")
        plaza.estatus = EstatusPlaza.CANCELADA
        plaza.empleado_id = None
        return await self.repository.actualizar(plaza)

    async def asignar_categoria_en_lote(
        self,
        contrato_id: int,
        categoria_puesto_id: int,
        cantidad: int,
        sede_id: Optional[int] = None,
        salario_mensual: Optional[Decimal] = None,
        prefijo_codigo: str = "",
    ) -> list[Plaza]:
        if cantidad <= 0:
            raise BusinessRuleError("La cantidad debe ser mayor a cero")
        await self._validar_categoria_activa(categoria_puesto_id)
        if sede_id is not None:
            await self._validar_sede_activa(sede_id)

        vacantes = await self.repository.obtener_vacantes_sin_categoria(contrato_id)
        if len(vacantes) < cantidad:
            raise BusinessRuleError(
                f"No hay suficientes plazas vacantes sin categoría. Disponibles: {len(vacantes)}"
            )

        actualizadas: list[Plaza] = []
        prefijo_normalizado = prefijo_codigo.strip().upper()
        for plaza in vacantes[:cantidad]:
            if plaza.sede_id is None:
                plaza.sede_id = sede_id
            plaza.categoria_puesto_id = categoria_puesto_id
            if salario_mensual is not None:
                plaza.salario_mensual = salario_mensual
            if prefijo_normalizado:
                plaza.codigo = f"{prefijo_normalizado}-{plaza.numero_plaza:03d}"
            actualizadas.append(await self.repository.actualizar(plaza))

        return actualizadas

    async def asignar_sede_en_lote(
        self,
        contrato_id: int,
        sede_id: int,
        cantidad: int,
    ) -> list[Plaza]:
        if cantidad <= 0:
            raise BusinessRuleError("La cantidad debe ser mayor a cero")

        await self._validar_sede_activa(sede_id)
        vacantes = await self.repository.obtener_vacantes_con_categoria_sin_sede(contrato_id)
        if len(vacantes) < cantidad:
            raise BusinessRuleError(
                "No hay suficientes plazas vacantes con categoría y sin sede. "
                f"Disponibles: {len(vacantes)}"
            )

        actualizadas: list[Plaza] = []
        for plaza in vacantes[:cantidad]:
            plaza.sede_id = sede_id
            actualizadas.append(await self.repository.actualizar(plaza))

        return actualizadas

    async def asignar_empleado(self, plaza_id: int, empleado_id: int) -> Plaza:
        plaza = await self.repository.obtener_por_id(plaza_id)
        if plaza.categoria_puesto_id is None:
            raise BusinessRuleError("La plaza debe tener categoría antes de asignar un empleado")
        if plaza.sede_id is None:
            raise BusinessRuleError("La plaza debe tener sede antes de asignar un empleado")
        if not plaza.puede_asignar_empleado():
            raise BusinessRuleError("La plaza no está disponible para asignación")
        plaza.empleado_id = empleado_id
        plaza.estatus = EstatusPlaza.OCUPADA
        return await self.repository.actualizar(plaza)

    async def liberar_plaza(self, plaza_id: int) -> Plaza:
        plaza = await self.repository.obtener_por_id(plaza_id)
        if plaza.estatus != EstatusPlaza.OCUPADA:
            raise BusinessRuleError("Solo se pueden liberar plazas ocupadas")
        plaza.empleado_id = None
        plaza.estatus = EstatusPlaza.VACANTE
        return await self.repository.actualizar(plaza)

    async def suspender_plaza(self, plaza_id: int) -> Plaza:
        plaza = await self.repository.obtener_por_id(plaza_id)
        if not plaza.puede_suspender():
            raise BusinessRuleError("La plaza no se puede suspender en su estatus actual")
        plaza.estatus = EstatusPlaza.SUSPENDIDA
        return await self.repository.actualizar(plaza)

    async def reactivar_plaza(self, plaza_id: int) -> Plaza:
        plaza = await self.repository.obtener_por_id(plaza_id)
        if not plaza.puede_reactivar():
            raise BusinessRuleError("Solo se pueden reactivar plazas suspendidas")
        plaza.estatus = EstatusPlaza.VACANTE
        return await self.repository.actualizar(plaza)

    async def obtener_resumen_categoria(
        self,
        contrato_id: int,
        categoria_puesto_id: int,
        fecha_referencia: Optional[date] = None,
    ) -> ResumenPlazasCategoria:
        plazas = await self.obtener_resumen_de_categoria(contrato_id, categoria_puesto_id)
        cantidades = await self.obtener_cantidad_esperada_por_categoria(contrato_id, fecha_referencia)
        cantidad_esperada = cantidades.get(categoria_puesto_id, 0)

        categoria_clave = ""
        categoria_nombre = ""
        total_plazas = len(plazas)
        vacantes = 0
        ocupadas = 0
        suspendidas = 0
        costo_total = Decimal("0")
        for plaza in plazas:
            categoria_clave = plaza.categoria_clave or categoria_clave
            categoria_nombre = plaza.categoria_nombre or categoria_nombre
            if plaza.estatus == EstatusPlaza.VACANTE:
                vacantes += 1
            elif plaza.estatus == EstatusPlaza.OCUPADA:
                ocupadas += 1
            elif plaza.estatus == EstatusPlaza.SUSPENDIDA:
                suspendidas += 1
            costo_total += plaza.salario_mensual

        return ResumenPlazasCategoria(
            contrato_id=contrato_id,
            categoria_puesto_id=categoria_puesto_id,
            categoria_clave=categoria_clave,
            categoria_nombre=categoria_nombre,
            cantidad_esperada=cantidad_esperada,
            total_plazas=total_plazas,
            plazas_vacantes=vacantes,
            plazas_ocupadas=ocupadas,
            plazas_suspendidas=suspendidas,
            costo_total_mensual=costo_total,
        )

    async def _validar_limite_contrato(self, contrato_id: int, nueva_cantidad: int = 0) -> None:
        from app.services import contrato_service

        contrato = await contrato_service.obtener_por_id(contrato_id)
        plazas_existentes = await self.repository.contar_por_contrato(contrato_id, incluir_canceladas=True)
        if contrato.cantidad_plazas_maxima and plazas_existentes + nueva_cantidad > contrato.cantidad_plazas_maxima:
            raise BusinessRuleError(
                f"Ya se alcanzó el máximo contractual de plazas ({contrato.cantidad_plazas_maxima})"
            )

    async def _validar_categoria_activa(self, categoria_puesto_id: int) -> None:
        from app.services import categoria_puesto_service

        categoria = await categoria_puesto_service.obtener_por_id(categoria_puesto_id)
        if not categoria.esta_activo():
            raise BusinessRuleError(
                f"La categoría '{categoria.nombre}' no está activa"
            )

    async def _validar_sede_activa(self, sede_id: int) -> None:
        from app.services import sede_service

        sede = await sede_service.obtener_por_id(sede_id)
        if not sede.esta_activa():
            raise BusinessRuleError(
                f"La sede '{sede.nombre_display()}' no está activa"
            )

    def _map_resumen(self, item: dict) -> PlazaResumen:
        return PlazaResumen(
            id=item["id"],
            contrato_id=item["contrato_id"],
            sede_id=item.get("sede_id"),
            categoria_puesto_id=item.get("categoria_puesto_id"),
            numero_plaza=item["numero_plaza"],
            codigo=item.get("codigo", ""),
            empleado_id=item.get("empleado_id"),
            fecha_inicio=item["fecha_inicio"],
            fecha_fin=item.get("fecha_fin"),
            salario_mensual=Decimal(str(item["salario_mensual"])),
            tipo_jornada=TipoJornadaPlaza(
                str(item.get("tipo_jornada") or TipoJornadaPlaza.COMPLETA.value)
            ),
            factor_jornada=Decimal(str(item.get("factor_jornada") or "1.0")),
            estatus=EstatusPlaza(item["estatus"]),
            notas=item.get("notas"),
            contrato_codigo=item.get("contrato_codigo", ""),
            sede_codigo=item.get("sede_codigo", ""),
            sede_nombre=item.get("sede_nombre", "Sin sede"),
            categoria_clave=item.get("categoria_clave", ""),
            categoria_nombre=item.get("categoria_nombre", "Sin categoría"),
            empleado_nombre=item.get("empleado_nombre", ""),
            empleado_curp=item.get("empleado_curp", ""),
        )


plaza_service = PlazaService()
