"""Subservicio de mutaciones y ciclo de vida laboral de empleados."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional, TYPE_CHECKING

from app.core.enums import EstatusEmpleado, MotivoBaja
from app.core.exceptions import BusinessRuleError, DuplicateError
from app.entities.empleado import Empleado, EmpleadoCreate, EmpleadoUpdate


def _get_historial_service():
    """Import diferido para evitar imports circulares."""
    from app.services.historial_laboral_service import historial_laboral_service
    return historial_laboral_service

if TYPE_CHECKING:
    from app.services.empleado_service import EmpleadoService


logger = logging.getLogger(__name__)


class EmpleadoMutationService:
    """Encapsula altas, actualizaciones y cambios de estatus."""

    def __init__(self, root: "EmpleadoService"):
        self.root = root

    async def crear(self, empleado_create: EmpleadoCreate) -> Empleado:
        empleado_existente = await self.root.repository.obtener_por_curp(empleado_create.curp)
        if empleado_existente:
            if empleado_existente.is_restricted:
                raise BusinessRuleError(
                    f"El empleado con CURP {empleado_create.curp} tiene restricciones "
                    "en el sistema. Contacte al administrador de BUAP para mas informacion."
                )
            raise DuplicateError(
                f"Empleado con CURP {empleado_create.curp} ya existe",
                field="curp",
                value=empleado_create.curp,
            )

        if empleado_create.empresa_id is not None:
            await self.root._validar_empresa(empleado_create.empresa_id)

        clave = await self.root.generar_clave(date.today().year)

        empleado = Empleado(
            clave=clave,
            empresa_id=empleado_create.empresa_id,
            curp=empleado_create.curp,
            rfc=empleado_create.rfc,
            nss=empleado_create.nss,
            nombre=empleado_create.nombre,
            apellido_paterno=empleado_create.apellido_paterno,
            apellido_materno=empleado_create.apellido_materno,
            fecha_nacimiento=empleado_create.fecha_nacimiento,
            genero=empleado_create.genero,
            telefono=empleado_create.telefono,
            email=empleado_create.email,
            direccion=empleado_create.direccion,
            contacto_emergencia=empleado_create.contacto_emergencia,
            fecha_ingreso=empleado_create.fecha_ingreso or date.today(),
            notas=empleado_create.notas,
            estatus=EstatusEmpleado.ACTIVO,
        )

        empleado_creado = await self.root.repository.crear(empleado)

        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_alta(
                empleado_id=empleado_creado.id,
                plaza_id=None,
                fecha=empleado_creado.fecha_ingreso,
                notas=f"Alta de empleado: {empleado_creado.nombre_completo}",
            )
        except Exception as exc:
            logger.warning("Error registrando alta en historial: %s", exc)

        return empleado_creado

    async def actualizar(self, empleado_id: int, empleado_update: EmpleadoUpdate) -> Empleado:
        empleado = await self.root.repository.obtener_por_id(empleado_id)

        if empleado_update.empresa_id and empleado_update.empresa_id != empleado.empresa_id:
            await self.root._validar_empresa(empleado_update.empresa_id)

        update_data = empleado_update.model_dump(exclude_unset=True)
        for campo, valor in update_data.items():
            if valor is not None:
                setattr(empleado, campo, valor)

        return await self.root.repository.actualizar(empleado)

    async def dar_de_baja(
        self,
        empleado_id: int,
        motivo: MotivoBaja,
        fecha_baja: Optional[date] = None,
    ) -> Empleado:
        empleado = await self.root.repository.obtener_por_id(empleado_id)
        if empleado.estatus == EstatusEmpleado.INACTIVO:
            raise BusinessRuleError("El empleado ya está dado de baja")

        empleado.dar_de_baja(motivo, fecha_baja)
        empleado_actualizado = await self.root.repository.actualizar(empleado)

        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_baja(
                empleado_id=empleado_id,
                fecha=fecha_baja,
                notas=f"Baja por: {motivo.descripcion}",
            )
        except Exception as exc:
            logger.warning("Error registrando baja en historial: %s", exc)

        return empleado_actualizado

    async def reactivar(self, empleado_id: int) -> Empleado:
        empleado = await self.root.repository.obtener_por_id(empleado_id)
        if empleado.estatus == EstatusEmpleado.ACTIVO:
            raise BusinessRuleError("El empleado ya está activo")

        empleado.activar()
        empleado_actualizado = await self.root.repository.actualizar(empleado)

        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_reactivacion(
                empleado_id=empleado_id,
                plaza_id=None,
                notas="Reactivación de empleado",
            )
        except Exception as exc:
            logger.warning("Error registrando reactivación en historial: %s", exc)

        return empleado_actualizado

    async def suspender(self, empleado_id: int) -> Empleado:
        empleado = await self.root.repository.obtener_por_id(empleado_id)
        if empleado.estatus == EstatusEmpleado.SUSPENDIDO:
            raise BusinessRuleError("El empleado ya está suspendido")

        empleado.suspender()
        empleado_actualizado = await self.root.repository.actualizar(empleado)

        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_suspension(
                empleado_id=empleado_id,
                notas="Suspensión temporal",
            )
        except Exception as exc:
            logger.warning("Error registrando suspensión en historial: %s", exc)

        return empleado_actualizado

    async def reingresar(
        self,
        empleado_id: int,
        nueva_empresa_id: int,
        datos_actualizados: Optional[EmpleadoUpdate] = None,
    ) -> Empleado:
        empleado = await self.root.repository.obtener_por_id(empleado_id)

        if empleado.is_restricted:
            raise BusinessRuleError(
                f"El empleado con CURP {empleado.curp} tiene restricciones "
                "en el sistema. Contacte al administrador de BUAP para mas informacion."
            )

        if empleado.estatus == EstatusEmpleado.ACTIVO and empleado.empresa_id == nueva_empresa_id:
            raise BusinessRuleError(
                f"El empleado {empleado.clave} ya esta activo en esta empresa"
            )

        await self.root._validar_empresa(nueva_empresa_id)
        empresa_anterior_id = empleado.empresa_id
        empleado.empresa_id = nueva_empresa_id

        if datos_actualizados:
            update_data = datos_actualizados.model_dump(exclude_unset=True)
            for campo, valor in update_data.items():
                if valor is not None:
                    setattr(empleado, campo, valor)

        if empleado.estatus != EstatusEmpleado.ACTIVO:
            empleado.estatus = EstatusEmpleado.ACTIVO
            empleado.fecha_baja = None
            empleado.motivo_baja = None

        empleado_actualizado = await self.root.repository.actualizar(empleado)

        try:
            historial_service = _get_historial_service()
            await historial_service.registrar_reingreso(
                empleado_id=empleado_id,
                empresa_anterior_id=empresa_anterior_id,
                plaza_id=None,
                notas=(
                    f"Reingreso a empresa {nueva_empresa_id} "
                    f"desde empresa {empresa_anterior_id}"
                ),
            )
        except Exception as exc:
            logger.warning("Error registrando reingreso en historial: %s", exc)

        return empleado_actualizado
