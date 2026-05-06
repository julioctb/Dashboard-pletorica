import asyncio
from datetime import date

from app.core.exceptions import BusinessRuleError
from app.domain.enums import EstatusEmpleado
from app.domain.models.empleado import Empleado, EmpleadoUpdate
from app.domain.services.empleados.mutations import EmpleadoMutationService


class _Repo:
    def __init__(self, empleado: Empleado):
        self.empleado = empleado

    async def obtener_por_id(self, empleado_id: int) -> Empleado:
        assert empleado_id == self.empleado.id
        return self.empleado

    async def actualizar(self, empleado: Empleado) -> Empleado:
        self.empleado = empleado
        return empleado


class _Root:
    def __init__(self, empleado: Empleado):
        self.repository = _Repo(empleado)

    async def _validar_empresa(self, empresa_id: int) -> None:
        return None


def test_reactivar_sin_plaza_deja_inactivo():
    empleado = Empleado(
        id=1,
        clave="B26-00001",
        curp="AAAA010101HDFBCD01",
        nombre="JUAN",
        apellido_paterno="PEREZ",
        estatus=EstatusEmpleado.SUSPENDIDO,
        fecha_ingreso=date.today(),
        plaza_actual_id=None,
    )

    service = EmpleadoMutationService(_Root(empleado))

    actualizado = asyncio.run(service.reactivar(1))

    assert actualizado.estatus == EstatusEmpleado.INACTIVO


def test_reactivar_con_plaza_deja_activo():
    empleado = Empleado(
        id=1,
        clave="B26-00002",
        curp="BBBB010101HDFBCD02",
        nombre="JUAN",
        apellido_paterno="PEREZ",
        estatus=EstatusEmpleado.SUSPENDIDO,
        fecha_ingreso=date.today(),
        plaza_actual_id=99,
    )

    service = EmpleadoMutationService(_Root(empleado))

    actualizado = asyncio.run(service.reactivar(1))

    assert actualizado.estatus == EstatusEmpleado.ACTIVO


def test_reactivar_exige_suspendido():
    empleado = Empleado(
        id=1,
        clave="B26-00003",
        curp="CCCC010101HDFBCD03",
        nombre="JUAN",
        apellido_paterno="PEREZ",
        estatus=EstatusEmpleado.INACTIVO,
        fecha_ingreso=date.today(),
    )

    service = EmpleadoMutationService(_Root(empleado))

    try:
        asyncio.run(service.reactivar(1))
    except BusinessRuleError as exc:
        assert "suspendido" in str(exc).lower()
    else:
        raise AssertionError("Se esperaba BusinessRuleError")


def test_reingresar_sin_plaza_permanece_inactivo():
    empleado = Empleado(
        id=1,
        clave="B26-00004",
        curp="DDDD010101HDFBCD04",
        nombre="JUAN",
        apellido_paterno="PEREZ",
        estatus=EstatusEmpleado.INACTIVO,
        fecha_ingreso=date.today(),
        empresa_id=10,
        plaza_actual_id=None,
    )

    service = EmpleadoMutationService(_Root(empleado))

    actualizado = asyncio.run(
        service.reingresar(
            1,
            20,
            EmpleadoUpdate(fecha_ingreso_vigente=date.today()),
        )
    )

    assert actualizado.estatus == EstatusEmpleado.INACTIVO
    assert actualizado.empresa_id == 20
