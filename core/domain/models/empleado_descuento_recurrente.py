"""Entidad de dominio para descuentos recurrentes del empleado."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.core.validation import limpiar_moneda

_MONEDA_QUANTUM = Decimal("0.01")
_NOTAS_MAX = 500

DESCUENTOS_RECURRENTES_CONFIG = (
    {
        "concepto_clave": "DESCUENTO_INFONAVIT",
        "nombre": "Amortización INFONAVIT",
        "label": "INFONAVIT",
        "badge": "INF",
        "color_scheme": "blue",
        "form_key": "infonavit",
        "orden": 1,
    },
    {
        "concepto_clave": "DESCUENTO_FONACOT",
        "nombre": "Descuento FONACOT",
        "label": "FONACOT",
        "badge": "FON",
        "color_scheme": "orange",
        "form_key": "fonacot",
        "orden": 2,
    },
    {
        "concepto_clave": "PRESTAMO_EMPRESA",
        "nombre": "Préstamo empresa",
        "label": "Préstamo empresa",
        "badge": "PRE",
        "color_scheme": "teal",
        "form_key": "prestamo_empresa",
        "orden": 3,
    },
    {
        "concepto_clave": "PENSION_ALIMENTICIA",
        "nombre": "Pensión alimenticia",
        "label": "Pensión alimenticia",
        "badge": "PEN",
        "color_scheme": "red",
        "form_key": "pension_alimenticia",
        "orden": 4,
    },
)

DESCUENTOS_RECURRENTES_POR_CLAVE = {
    item["concepto_clave"]: item for item in DESCUENTOS_RECURRENTES_CONFIG
}
DESCUENTOS_RECURRENTES_POR_FORM_KEY = {
    item["form_key"]: item for item in DESCUENTOS_RECURRENTES_CONFIG
}
DESCUENTOS_RECURRENTES_CLAVES = tuple(DESCUENTOS_RECURRENTES_POR_CLAVE.keys())
DESCUENTOS_RECURRENTES_CLAVES_SET = set(DESCUENTOS_RECURRENTES_CLAVES)


def obtener_meta_descuento_recurrente(concepto_clave: str) -> dict:
    """Retorna la metadata declarativa del concepto soportado."""
    return DESCUENTOS_RECURRENTES_POR_CLAVE[concepto_clave]


def es_descuento_recurrente_activo_en_rango(
    fecha_inicio_descuento: date,
    fecha_fin_descuento: Optional[date],
    fecha_inicio_rango: date,
    fecha_fin_rango: date,
) -> bool:
    """Indica si la vigencia del descuento cruza cualquier parte del rango."""
    return (
        fecha_inicio_descuento <= fecha_fin_rango
        and (
            fecha_fin_descuento is None
            or fecha_fin_descuento >= fecha_inicio_rango
        )
    )


def es_descuento_recurrente_activo_en_fecha(
    fecha_inicio_descuento: date,
    fecha_fin_descuento: Optional[date],
    fecha_referencia: date,
) -> bool:
    """Indica si el descuento está vigente en una fecha específica."""
    return es_descuento_recurrente_activo_en_rango(
        fecha_inicio_descuento=fecha_inicio_descuento,
        fecha_fin_descuento=fecha_fin_descuento,
        fecha_inicio_rango=fecha_referencia,
        fecha_fin_rango=fecha_referencia,
    )


class _EmpleadoDescuentoRecurrenteBase(BaseModel):
    """Contrato base compartido para alta y lectura."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    empleado_id: int
    concepto_clave: str
    monto_periodico: Decimal
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    notas: Optional[str] = Field(None, max_length=_NOTAS_MAX)

    @field_validator("concepto_clave", mode="before")
    @classmethod
    def validar_concepto_clave(cls, value: str) -> str:
        """Normaliza y restringe la clave al catálogo soportado."""
        concepto = str(value or "").strip().upper()
        if concepto not in DESCUENTOS_RECURRENTES_CLAVES_SET:
            raise ValueError("Concepto de descuento recurrente no soportado")
        return concepto

    @field_validator("monto_periodico", mode="before")
    @classmethod
    def validar_monto_periodico(cls, value) -> Decimal:
        """Normaliza montos monetarios a Decimal(12, 2)."""
        monto_limpio = limpiar_moneda(str(value or "").strip())
        if not monto_limpio:
            raise ValueError("El monto periódico es obligatorio")

        monto = Decimal(monto_limpio).quantize(
            _MONEDA_QUANTUM,
            rounding=ROUND_HALF_UP,
        )
        if monto <= 0:
            raise ValueError("El monto periódico debe ser mayor a 0")
        return monto

    @field_validator("fecha_fin")
    @classmethod
    def validar_rango_fechas(cls, value: Optional[date], info) -> Optional[date]:
        """Valida que la fecha fin no sea anterior al inicio."""
        fecha_inicio = info.data.get("fecha_inicio")
        if value and fecha_inicio and value < fecha_inicio:
            raise ValueError("La fecha fin no puede ser anterior a la fecha inicio")
        return value

    def esta_activo_en_fecha(self, fecha_referencia: date) -> bool:
        """Indica si el descuento está vigente en una fecha."""
        return es_descuento_recurrente_activo_en_fecha(
            fecha_inicio_descuento=self.fecha_inicio,
            fecha_fin_descuento=self.fecha_fin,
            fecha_referencia=fecha_referencia,
        )

    def esta_activo_en_rango(self, fecha_inicio: date, fecha_fin: date) -> bool:
        """Indica si el descuento cruza cualquier parte del rango."""
        return es_descuento_recurrente_activo_en_rango(
            fecha_inicio_descuento=self.fecha_inicio,
            fecha_fin_descuento=self.fecha_fin,
            fecha_inicio_rango=fecha_inicio,
            fecha_fin_rango=fecha_fin,
        )


class EmpleadoDescuentoRecurrente(_EmpleadoDescuentoRecurrenteBase):
    """Configuración vigente de descuento recurrente por empleado."""

    id: Optional[int] = None
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None


class EmpleadoDescuentoRecurrenteCreate(_EmpleadoDescuentoRecurrenteBase):
    """DTO para persistir configuración de descuentos recurrentes."""

