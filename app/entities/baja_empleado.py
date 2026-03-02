"""
Entidades de dominio para el proceso de Baja de Empleado.

Maquina de estados simplificada (ajustada a operacion real):
    INICIADA -> COMUNICADA -> LIQUIDADA -> CERRADA
    INICIADA -> LIQUIDADA -> CERRADA
    Cualquier estado activo -> CANCELADA

La sustitucion NO se trackea como proceso. Solo se registra
`requiere_sustitucion` como dato informativo.
"""
from datetime import date, datetime
from typing import ClassVar, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import MotivoBaja, EstatusBaja, EstatusLiquidacion


class BajaEmpleado(BaseModel):
    """Entidad principal del proceso de baja."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    empleado_id: int
    empresa_id: int
    plaza_id: Optional[int] = None

    motivo: MotivoBaja
    notas: Optional[str] = Field(default=None, max_length=2000)

    fecha_registro: date = Field(default_factory=date.today)
    fecha_efectiva: date
    fecha_comunicacion_buap: Optional[date] = None
    fecha_limite_liquidacion: date
    estatus_liquidacion: EstatusLiquidacion = EstatusLiquidacion.PENDIENTE
    requiere_sustitucion: Optional[bool] = None
    estatus: EstatusBaja = EstatusBaja.INICIADA
    registrado_por: Optional[UUID] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    @field_validator('fecha_efectiva')
    @classmethod
    def fecha_efectiva_no_anterior_a_registro(cls, v, info):
        fecha_reg = info.data.get('fecha_registro', date.today())
        if v < fecha_reg:
            raise ValueError('La fecha efectiva no puede ser anterior a la fecha de registro')
        return v

    @property
    def dias_para_liquidar(self) -> int:
        """Dias restantes para entregar liquidacion. Negativo = vencido."""
        if self.estatus_liquidacion == EstatusLiquidacion.ENTREGADA:
            return 0
        return (self.fecha_limite_liquidacion - date.today()).days

    @property
    def esta_vencida_liquidacion(self) -> bool:
        return self.dias_para_liquidar < 0

    @property
    def es_proceso_activo(self) -> bool:
        return self.estatus.es_proceso_activo

    @property
    def fue_comunicada(self) -> bool:
        return self.fecha_comunicacion_buap is not None

    TRANSICIONES_VALIDAS: ClassVar[dict[EstatusBaja, set[EstatusBaja]]] = {
        EstatusBaja.INICIADA: {
            EstatusBaja.COMUNICADA,
            EstatusBaja.LIQUIDADA,
            EstatusBaja.CANCELADA,
        },
        EstatusBaja.COMUNICADA: {
            EstatusBaja.LIQUIDADA,
            EstatusBaja.CANCELADA,
        },
        EstatusBaja.LIQUIDADA: {EstatusBaja.CERRADA},
        EstatusBaja.CERRADA: set(),
        EstatusBaja.CANCELADA: set(),
    }

    def puede_transicionar_a(self, nuevo_estatus: EstatusBaja) -> bool:
        return nuevo_estatus in self.TRANSICIONES_VALIDAS.get(self.estatus, set())

    def comunicar(self, fecha: Optional[date] = None):
        """Registra que se comunico la baja a BUAP."""
        if not self.puede_transicionar_a(EstatusBaja.COMUNICADA):
            raise ValueError(f"No se puede comunicar desde estatus {self.estatus.descripcion}")
        self.estatus = EstatusBaja.COMUNICADA
        self.fecha_comunicacion_buap = fecha or date.today()

    def marcar_liquidada(self):
        """Marca que la liquidacion/finiquito fue entregada."""
        if not self.puede_transicionar_a(EstatusBaja.LIQUIDADA):
            raise ValueError(f"No se puede liquidar desde estatus {self.estatus.descripcion}")
        self.estatus = EstatusBaja.LIQUIDADA
        self.estatus_liquidacion = EstatusLiquidacion.ENTREGADA

    def cerrar(self):
        """Cierra el proceso de baja."""
        if not self.puede_transicionar_a(EstatusBaja.CERRADA):
            raise ValueError(f"No se puede cerrar desde estatus {self.estatus.descripcion}")
        self.estatus = EstatusBaja.CERRADA

    def cancelar(self, notas: Optional[str] = None):
        """Cancela el proceso de baja."""
        if not self.puede_transicionar_a(EstatusBaja.CANCELADA):
            raise ValueError(f"No se puede cancelar desde estatus {self.estatus.descripcion}")
        self.estatus = EstatusBaja.CANCELADA
        if notas:
            self.notas = ((self.notas or "").strip() + f"\n[CANCELADA] {notas}").strip()


class BajaEmpleadoCreate(BaseModel):
    """Modelo para registrar una nueva baja."""

    empleado_id: int
    empresa_id: int
    plaza_id: Optional[int] = None
    motivo: MotivoBaja
    fecha_efectiva: date
    notas: Optional[str] = Field(default=None, max_length=2000)
    registrado_por: Optional[UUID] = None


class BajaEmpleadoResumen(BaseModel):
    """Modelo resumido para listados y tabla."""

    id: int
    empleado_id: int
    empleado_nombre: str = ""
    empleado_clave: str = ""
    motivo: str
    fecha_efectiva: date
    estatus: str
    estatus_liquidacion: str = "PENDIENTE"
    dias_para_liquidar: int = 0
    requiere_sustitucion: Optional[bool] = None
    fue_comunicada: bool = False
