"""
Entidad Historial Laboral.

Bitacora automatica de movimientos de empleados.
Cada registro representa un periodo/estado del empleado.
Esta entidad es de SOLO LECTURA - los registros se crean automaticamente.
"""
from datetime import date, datetime, timedelta
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
try:
    from dateutil.relativedelta import relativedelta
except ModuleNotFoundError:  # pragma: no cover - fallback para entornos mínimos
    class _RelativeDeltaFallback:
        """Fallback básico para años/meses/días sin python-dateutil."""

        def __init__(self, fin: date, inicio: date):
            years = fin.year - inicio.year
            months = fin.month - inicio.month
            days = fin.day - inicio.day

            if days < 0:
                months -= 1
                ultimo_dia_mes_previo = (fin.replace(day=1) - timedelta(days=1)).day
                days += ultimo_dia_mes_previo

            if months < 0:
                years -= 1
                months += 12

            self.years = years
            self.months = months
            self.days = days

    def relativedelta(fin: date, inicio: date):
        return _RelativeDeltaFallback(fin, inicio)

from app.domain.enums import TipoMovimiento


# =============================================================================
# MODELO PRINCIPAL
# =============================================================================

class HistorialLaboral(BaseModel):
    """
    Modelo de historial laboral.
    Representa un periodo/estado de un empleado.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True
    )

    id: int
    empleado_id: int
    plaza_id: Optional[int] = None  # NULL si no tiene plaza asignada
    tipo_movimiento: Optional[TipoMovimiento] = None
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    notas: Optional[str] = None
    empresa_anterior_id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    def calcular_duracion(self) -> dict:
        """Calcula la duracion del periodo"""
        fin = self.fecha_fin or date.today()
        delta = relativedelta(fin, self.fecha_inicio)

        total_meses = delta.months + (delta.years * 12)

        if delta.years > 0:
            descripcion = f"{delta.years} ano{'s' if delta.years > 1 else ''}"
            if delta.months > 0:
                descripcion += f", {delta.months} mes{'es' if delta.months > 1 else ''}"
        elif delta.months > 0:
            descripcion = f"{delta.months} mes{'es' if delta.months > 1 else ''}"
        else:
            descripcion = f"{delta.days} dia{'s' if delta.days != 1 else ''}"

        return {
            "anos": delta.years,
            "meses": delta.months,
            "dias": delta.days,
            "total_meses": total_meses,
            "descripcion": descripcion
        }

    @property
    def esta_activo(self) -> bool:
        """Indica si el registro es el actual (sin fecha_fin)"""
        return self.fecha_fin is None

    @property
    def duracion_texto(self) -> str:
        """Retorna la duracion en formato legible"""
        return self.calcular_duracion()["descripcion"]


# =============================================================================
# MODELO INTERNO PARA CREAR REGISTROS (usado por el servicio, no por UI)
# =============================================================================

class HistorialLaboralInterno(BaseModel):
    """Modelo interno para crear registros automaticamente"""

    model_config = ConfigDict(use_enum_values=True)

    empleado_id: int
    plaza_id: Optional[int] = None
    tipo_movimiento: TipoMovimiento
    fecha_inicio: date = Field(default_factory=date.today)
    notas: Optional[str] = None
    empresa_anterior_id: Optional[int] = None


# =============================================================================
# MODELO RESUMIDO PARA LISTADOS
# =============================================================================

class HistorialLaboralResumen(BaseModel):
    """Modelo resumido para listados con datos enriquecidos"""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True
    )

    id: int
    empleado_id: int
    plaza_id: Optional[int]
    tipo_movimiento: Optional[str]
    fecha_inicio: date
    fecha_fin: Optional[date]

    # Datos del empleado
    empleado_clave: str
    empleado_nombre: str

    # Datos de la plaza (pueden ser None si no hay plaza)
    plaza_numero: Optional[int] = None
    categoria_nombre: Optional[str] = None
    contrato_codigo: Optional[str] = None
    empresa_nombre: Optional[str] = None

    # Calculados
    duracion_texto: str = ""
    periodo_texto: str = ""

    @classmethod
    def from_historial(
        cls,
        historial: HistorialLaboral,
        empleado_clave: str,
        empleado_nombre: str,
        plaza_numero: Optional[int] = None,
        categoria_nombre: Optional[str] = None,
        contrato_codigo: Optional[str] = None,
        empresa_nombre: Optional[str] = None
    ) -> 'HistorialLaboralResumen':
        """Factory method para crear desde historial con datos relacionados"""
        duracion = historial.calcular_duracion()

        # Formatear periodo
        inicio_fmt = historial.fecha_inicio.strftime("%d/%m/%Y")
        if historial.fecha_fin:
            fin_fmt = historial.fecha_fin.strftime("%d/%m/%Y")
            periodo = f"{inicio_fmt} - {fin_fmt}"
        else:
            periodo = f"{inicio_fmt} - Actual"

        # Obtener descripcion del tipo de movimiento
        tipo_mov_desc = None
        if historial.tipo_movimiento:
            if isinstance(historial.tipo_movimiento, TipoMovimiento):
                tipo_mov_desc = historial.tipo_movimiento.descripcion
            else:
                tipo_mov_desc = historial.tipo_movimiento

        return cls(
            id=historial.id,
            empleado_id=historial.empleado_id,
            plaza_id=historial.plaza_id,
            tipo_movimiento=tipo_mov_desc,
            fecha_inicio=historial.fecha_inicio,
            fecha_fin=historial.fecha_fin,
            empleado_clave=empleado_clave,
            empleado_nombre=empleado_nombre,
            plaza_numero=plaza_numero,
            categoria_nombre=categoria_nombre,
            contrato_codigo=contrato_codigo,
            empresa_nombre=empresa_nombre,
            duracion_texto=duracion["descripcion"],
            periodo_texto=periodo
        )
