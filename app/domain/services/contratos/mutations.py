"""Subservicio de mutaciones y ciclo de vida del dominio de contratos."""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING, Optional

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.domain.models import Contrato, ContratoCreate, ContratoUpdate, EstatusContrato
from app.domain.services.shared import merge_update_model

if TYPE_CHECKING:
    from app.domain.services.contrato_service import ContratoService

logger = logging.getLogger(__name__)


class ContratoMutationService:
    """Encapsula creación, edición y cambios de estatus."""

    def __init__(self, root: "ContratoService"):
        self.root = root

    async def crear(self, contrato_create: ContratoCreate) -> Contrato:
        contrato = Contrato(**contrato_create.model_dump())
        creado = await self.root.repository.crear(contrato)
        await self._sincronizar_plazas(creado)
        self._avisar_si_retroactivo(creado)
        return creado

    def _avisar_si_retroactivo(self, contrato: Contrato) -> None:
        """Detecta contratos con fecha_inicio en el pasado.

        TODO (Fase E - periodos retroactivos):
            Cuando `fecha_inicio < today`, generar automáticamente los
            periodos de nómina ya transcurridos con estatus 'cerrado' para
            permitir captura histórica. Hoy solo se loguea un aviso; la
            integración con `nomina_periodo_service.crear_periodo` depende
            de la periodicidad configurada para la empresa y de la semántica
            exacta que deba tener el periodo generado (¿listo? ¿en
            captura histórica?), por lo que requiere decisión de producto
            antes de automatizarse.
        """
        if not contrato or not contrato.fecha_inicio:
            return
        hoy = date.today()
        if contrato.fecha_inicio >= hoy:
            return
        logger.info(
            "Contrato retroactivo creado: %s (fecha_inicio=%s). "
            "Los periodos de nómina previos a hoy no se generaron "
            "automáticamente — capturar desde el módulo de nómina.",
            contrato.codigo,
            contrato.fecha_inicio,
        )

    async def crear_con_codigo_auto(
        self,
        contrato_create: ContratoCreate,
        codigo_empresa: str,
        clave_servicio: str,
    ) -> Contrato:
        codigo = await self.generar_codigo_contrato(
            codigo_empresa,
            clave_servicio,
            contrato_create.fecha_inicio.year,
        )
        datos = contrato_create.model_dump()
        datos["codigo"] = codigo
        contrato = Contrato(**datos)
        creado = await self.root.repository.crear(contrato)
        await self._sincronizar_plazas(creado)
        return creado

    async def generar_codigo_contrato(
        self,
        codigo_empresa: str,
        clave_servicio: str,
        anio: int,
    ) -> str:
        consecutivo = await self.root.repository.obtener_siguiente_consecutivo(
            codigo_empresa,
            clave_servicio,
            anio,
        )
        return Contrato.generar_codigo(codigo_empresa, clave_servicio, anio, consecutivo)

    async def actualizar(self, contrato_id: int, contrato_update: ContratoUpdate) -> Contrato:
        contrato_actual = await self.root.repository.obtener_por_id(contrato_id)
        if not contrato_actual.puede_modificarse():
            raise BusinessRuleError(
                f"No se puede modificar un contrato en estado {contrato_actual.estatus}"
            )

        contrato_modificado = merge_update_model(contrato_actual, contrato_update)
        actualizado = await self.root.repository.actualizar(contrato_modificado)
        await self._sincronizar_plazas(actualizado)
        return actualizado

    async def activar(self, contrato_id: int) -> Contrato:
        contrato = await self.root.repository.obtener_por_id(contrato_id)
        if not contrato.puede_activarse():
            raise BusinessRuleError(
                f"No se puede activar un contrato en estado {contrato.estatus}"
            )
        return await self.root.repository.cambiar_estatus(contrato_id, EstatusContrato.ACTIVO)

    async def suspender(self, contrato_id: int) -> Contrato:
        contrato = await self.root.repository.obtener_por_id(contrato_id)
        if contrato.estatus != EstatusContrato.ACTIVO:
            raise BusinessRuleError("Solo se pueden suspender contratos activos")
        return await self.root.repository.cambiar_estatus(
            contrato_id,
            EstatusContrato.SUSPENDIDO,
        )

    async def reactivar(self, contrato_id: int) -> Contrato:
        contrato = await self.root.repository.obtener_por_id(contrato_id)
        if contrato.estatus != EstatusContrato.SUSPENDIDO:
            raise BusinessRuleError("Solo se pueden reactivar contratos suspendidos")
        return await self.root.repository.cambiar_estatus(contrato_id, EstatusContrato.ACTIVO)

    async def cancelar(self, contrato_id: int) -> Contrato:
        contrato = await self.root.repository.obtener_por_id(contrato_id)
        if contrato.estatus == EstatusContrato.CANCELADO:
            raise BusinessRuleError("El contrato ya está cancelado")
        return await self.root.repository.cambiar_estatus(
            contrato_id,
            EstatusContrato.CANCELADO,
        )

    async def eliminar(self, contrato_id: int) -> bool:
        return await self.root.repository.eliminar(contrato_id)

    async def liquidar(self, contrato_id: int) -> Contrato:
        """Cierra definitivamente un contrato VENCIDO (VENCIDO → LIQUIDADO).

        Un contrato liquidado ya no admite entregables ni nómina nueva.
        """
        contrato = await self.root.repository.obtener_por_id(contrato_id)
        if contrato.estatus != EstatusContrato.VENCIDO:
            raise BusinessRuleError(
                "Solo se pueden liquidar contratos vencidos "
                f"(estado actual: {contrato.estatus})"
            )
        return await self.root.repository.cambiar_estatus(
            contrato_id,
            EstatusContrato.LIQUIDADO,
        )

    async def crear_extension(
        self,
        contrato_padre_id: int,
        *,
        fecha_inicio: date,
        fecha_fin: Optional[date] = None,
        monto_minimo=None,
        monto_maximo=None,
        overrides_categorias: Optional[dict] = None,
    ) -> Contrato:
        """Crea un nuevo contrato vinculado a un contrato padre VENCIDO.

        Regla de negocio: solo se puede extender un contrato cuya vigencia
        original ya terminó (estatus = VENCIDO). Los contratos ACTIVOS deben
        modificarse in-place; los LIQUIDADOS están cerrados definitivamente.

        La extensión hereda del padre:
            - configuración base (empresa, tipo, personal, cantidades de plazas)
            - estructura de plazas (vía `_sincronizar_plazas`)
            - **categorías completas** (clonadas con overrides opcionales por
              categoría: sueldo_base, tipo_sueldo, costo_contractual,
              cantidad_minima, cantidad_maxima. El nombre queda fijo.)

        Parámetro `overrides_categorias`:
            Dict keyed por `id` del `ContratoCategoria` del padre. Cada valor
            es un dict con los campos a sobreescribir al clonar. Campos no
            presentes en el dict de override conservan el valor del padre.
            Si es None, se clona 1:1 sin cambios.

        La asignación de empleados a plazas **no** se clona automáticamente —
        eso requiere un paso manual en la UI (la plaza nueva queda vacante y
        el empleado sigue en la plaza del padre hasta que se reasigne).
        """
        try:
            padre = await self.root.repository.obtener_por_id(contrato_padre_id)
        except NotFoundError:
            raise BusinessRuleError(
                f"El contrato padre con ID {contrato_padre_id} no existe"
            )

        if not padre.puede_extenderse():
            raise BusinessRuleError(
                "Solo se pueden extender contratos VENCIDOS "
                f"(estado actual: {padre.estatus})"
            )

        if fecha_inicio < padre.fecha_inicio:
            raise BusinessRuleError(
                "La fecha de inicio de la extensión no puede ser anterior "
                "a la del contrato padre"
            )

        if fecha_fin is not None and fecha_fin < fecha_inicio:
            raise BusinessRuleError(
                "La fecha de fin de la extensión debe ser posterior a la fecha de inicio"
            )

        # Generar código incremental: PADRE → PADRE-E1 → PADRE-E2 …
        codigo_extension = await self._siguiente_codigo_extension(padre)

        create_payload = ContratoCreate(
            empresa_id=padre.empresa_id,
            tipo_servicio_id=padre.tipo_servicio_id,
            requisicion_id=None,  # la extensión no proviene de una requisición
            contrato_padre_id=padre.id,
            codigo=codigo_extension,
            numero_folio_buap=None,
            tipo_contrato=padre.tipo_contrato,
            modalidad_adjudicacion=padre.modalidad_adjudicacion,
            tipo_duracion=padre.tipo_duracion,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            descripcion_objeto=padre.descripcion_objeto,
            monto_minimo=monto_minimo if monto_minimo is not None else padre.monto_minimo,
            monto_maximo=monto_maximo if monto_maximo is not None else padre.monto_maximo,
            incluye_iva=padre.incluye_iva,
            origen_recurso=padre.origen_recurso,
            segmento_asignacion=padre.segmento_asignacion,
            sede_campus=padre.sede_campus,
            requiere_poliza=padre.requiere_poliza,
            poliza_detalle=padre.poliza_detalle,
            tiene_personal=padre.tiene_personal,
            cantidad_plazas_minima=padre.cantidad_plazas_minima,
            cantidad_plazas_maxima=padre.cantidad_plazas_maxima,
            # La extensión nace ACTIVA: hereda toda la configuración del padre
            # más los overrides del wizard, no requiere un paso adicional de
            # "configurar como borrador". Consecuencia: aparece inmediatamente
            # en la sección Activos de /portal/contratos y en su detalle de plazas.
            estatus=EstatusContrato.ACTIVO,
            notas=f"Extensión automática de {padre.codigo}",
        )

        contrato = Contrato(**create_payload.model_dump())
        extension = await self.root.repository.crear(contrato)
        await self._clonar_categorias_a_extension(
            padre, extension, overrides_categorias
        )
        await self._sincronizar_plazas(extension)
        # Tras materializar plazas, asignarlas a las categorías del hijo para
        # que la migración de empleados (si la hay) pueda hacer match por
        # `categoria_puesto_id`.
        try:
            from app.domain.services import plaza_service

            await plaza_service.sincronizar_categorias_desde_contrato(extension.id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "No se pudieron sincronizar categorías con plazas de la extensión %s: %s",
                extension.codigo,
                exc,
            )
        # Nota: el padre ya está VENCIDO por precondición (`puede_extenderse()`),
        # así que no hay transición de estatus que aplicar aquí.
        return extension

    async def _clonar_categorias_a_extension(
        self,
        padre: Contrato,
        extension: Contrato,
        overrides: Optional[dict] = None,
    ) -> None:
        """Copia las categorías del contrato padre al contrato extensión.

        Si `overrides` es un dict keyed por id de ContratoCategoria del
        padre, cada categoría clona con los campos sobreescritos. Campos
        no presentes en el override conservan el valor del padre.

        Se hace best-effort: si falla el clonado, loguea un warning pero NO
        aborta la creación de la extensión. El usuario puede recapturar las
        categorías manualmente desde la tab Categorías de la extensión.
        """
        from app.domain.models import ContratoCategoriaCreate
        from app.domain.services import contrato_categoria_service

        overrides = overrides or {}

        try:
            categorias_padre = (
                await contrato_categoria_service.obtener_categorias_de_contrato(
                    padre.id
                )
            )
        except Exception as exc:  # noqa: BLE001 - best effort
            logger.warning(
                "No se pudieron obtener categorías del contrato padre %s "
                "para clonar a la extensión %s: %s",
                padre.codigo,
                extension.codigo,
                exc,
            )
            return

        if not categorias_padre:
            return

        clonadas = 0
        for categoria in categorias_padre:
            override = overrides.get(categoria.id, {}) or {}
            try:
                create_payload = ContratoCategoriaCreate(
                    contrato_id=extension.id,
                    categoria_puesto_id=categoria.categoria_puesto_id,
                    cantidad_minima=override.get(
                        "cantidad_minima", categoria.cantidad_minima
                    ),
                    cantidad_maxima=override.get(
                        "cantidad_maxima", categoria.cantidad_maxima
                    ),
                    costo_unitario=override.get(
                        "costo_unitario", categoria.costo_unitario
                    ),
                    costo_contractual=override.get(
                        "costo_contractual", categoria.costo_contractual
                    ),
                    sueldo_base=override.get(
                        "sueldo_base", categoria.sueldo_base
                    ),
                    tipo_sueldo=override.get(
                        "tipo_sueldo", categoria.tipo_sueldo
                    ),
                    nombre=categoria.nombre,  # no renombrable
                    notas=categoria.notas,
                )
                await contrato_categoria_service.crear(create_payload)
                clonadas += 1
            except Exception as exc:  # noqa: BLE001 - best effort por categoría
                logger.warning(
                    "No se pudo clonar la categoría %s (id=%s) del contrato "
                    "padre %s a la extensión %s: %s",
                    categoria.nombre or categoria.categoria_puesto_id,
                    categoria.id,
                    padre.codigo,
                    extension.codigo,
                    exc,
                )

        logger.info(
            "Extensión %s: %d/%d categorías clonadas desde %s",
            extension.codigo,
            clonadas,
            len(categorias_padre),
            padre.codigo,
        )

    async def migrar_empleados_a_extension(
        self,
        padre_id: int,
        extension_id: int,
        empleado_ids: list[int],
    ) -> dict:
        """Migra un subconjunto de empleados del contrato padre a la extensión.

        Por cada empleado en `empleado_ids`:
            1. Localiza su plaza OCUPADA actual en el padre.
            2. Busca una plaza VACANTE en la extensión con la misma
               `categoria_puesto_id`.
            3. Si la plaza destino no tiene `sede_id`, la copia de la plaza
               origen.
            4. Libera la plaza del padre (registra historial de liberación).
            5. Asigna la plaza destino al empleado (registra historial de
               asignación).

        Best-effort por empleado: si falla uno, los demás continúan. Devuelve:
            {
                "migrados": [empleado_ids exitosos],
                "fallidos": [{"empleado_id": X, "razon": "..."}],
            }
        """
        from app.domain.enums import EstatusPlaza
        from app.domain.services import plaza_service

        empleado_ids = [int(e) for e in empleado_ids if int(e or 0) > 0]
        if not empleado_ids:
            return {"migrados": [], "fallidos": []}

        try:
            plazas_padre = await plaza_service.obtener_por_contrato(padre_id)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Error obteniendo plazas del padre %s para migración: %s",
                padre_id,
                exc,
            )
            return {
                "migrados": [],
                "fallidos": [
                    {"empleado_id": eid, "razon": "No se pudieron cargar las plazas del padre"}
                    for eid in empleado_ids
                ],
            }

        try:
            plazas_extension = await plaza_service.obtener_por_contrato(extension_id)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Error obteniendo plazas de la extensión %s: %s",
                extension_id,
                exc,
            )
            return {
                "migrados": [],
                "fallidos": [
                    {"empleado_id": eid, "razon": "No se pudieron cargar las plazas de la extensión"}
                    for eid in empleado_ids
                ],
            }

        # Indexar plazas del padre por empleado.
        plaza_padre_por_empleado: dict[int, object] = {}
        for plaza in plazas_padre:
            if plaza.empleado_id is None:
                continue
            eid = int(plaza.empleado_id)
            if eid in empleado_ids and plaza.estatus == EstatusPlaza.OCUPADA:
                plaza_padre_por_empleado[eid] = plaza

        # Indexar plazas vacantes de la extensión por categoría.
        vacantes_por_categoria: dict[int, list] = {}
        for plaza in plazas_extension:
            if (
                plaza.estatus == EstatusPlaza.VACANTE
                and plaza.empleado_id is None
                and plaza.categoria_puesto_id is not None
            ):
                vacantes_por_categoria.setdefault(
                    int(plaza.categoria_puesto_id), []
                ).append(plaza)

        migrados: list[int] = []
        fallidos: list[dict] = []

        for empleado_id in empleado_ids:
            plaza_padre = plaza_padre_por_empleado.get(empleado_id)
            if plaza_padre is None:
                fallidos.append(
                    {
                        "empleado_id": empleado_id,
                        "razon": "No tiene plaza activa en el contrato padre",
                    }
                )
                continue

            cat_id = plaza_padre.categoria_puesto_id
            if cat_id is None:
                fallidos.append(
                    {
                        "empleado_id": empleado_id,
                        "razon": "La plaza actual no tiene categoría asignada",
                    }
                )
                continue

            disponibles = vacantes_por_categoria.get(int(cat_id), [])
            if not disponibles:
                fallidos.append(
                    {
                        "empleado_id": empleado_id,
                        "razon": "No hay plazas vacantes en la extensión para su categoría",
                    }
                )
                continue

            plaza_destino = disponibles.pop(0)

            try:
                # Copiar sede del padre si la plaza destino no la tiene.
                if plaza_destino.sede_id is None and plaza_padre.sede_id is not None:
                    plaza_destino.sede_id = plaza_padre.sede_id
                    plaza_destino = await plaza_service.repository.actualizar(
                        plaza_destino
                    )

                # Liberar plaza del padre (registra historial).
                await plaza_service.liberar_plaza(int(plaza_padre.id))

                # Asignar plaza del hijo (registra historial).
                await plaza_service.asignar_empleado(
                    int(plaza_destino.id), empleado_id
                )
                migrados.append(empleado_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Error migrando empleado %s de contrato %s a %s: %s",
                    empleado_id,
                    padre_id,
                    extension_id,
                    exc,
                )
                fallidos.append({"empleado_id": empleado_id, "razon": str(exc)})

        logger.info(
            "Migración extensión %s→%s: %d migrados, %d fallidos",
            padre_id,
            extension_id,
            len(migrados),
            len(fallidos),
        )
        return {"migrados": migrados, "fallidos": fallidos}

    async def _siguiente_codigo_extension(self, padre: Contrato) -> str:
        """Calcula el siguiente sufijo -EN para las extensiones de un padre."""
        hijos = []
        try:
            hijos = await self.root.repository.obtener_hijos(padre.id)
        except AttributeError:
            # Fallback si el repo no expone obtener_hijos (escenario legacy).
            hijos = []
        except Exception as exc:  # noqa: BLE001 - best effort
            logger.warning(
                "No se pudieron listar extensiones previas de %s: %s",
                padre.codigo,
                exc,
            )
        numero = len(hijos) + 1
        return f"{padre.codigo}-E{numero}"

    async def _sincronizar_plazas(self, contrato: Contrato) -> None:
        if not contrato.tiene_personal:
            return

        from app.domain.services import plaza_service

        await plaza_service.sincronizar_plazas_contrato(
            contrato.id,
            contrato.cantidad_plazas_maxima,
            contrato.fecha_inicio,
        )
