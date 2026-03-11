"""
Resolución centralizada de política fiscal por fecha de pago.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.core.catalogs.fiscal.isr import CatalogoISR
from app.core.catalogs.fiscal.salario_minimo import CatalogoSalarioMinimo
from app.core.catalogs.fiscal.uma import CatalogoUMA


@dataclass(frozen=True)
class ContextoFiscalNomina:
    """Valores fiscales efectivos para un cálculo de nómina."""

    fecha_referencia: date
    zona_frontera: bool
    uma_diaria: Decimal
    uma_mensual: Decimal
    tres_uma: Decimal
    tope_sbc: Decimal
    salario_minimo_diario_aplicable: Decimal
    limite_subsidio: Decimal
    subsidio_mensual: Decimal
    vigencia_soportada: bool
    mensaje_vigencia: str = ""


class PoliticaFiscalResolver:
    """Obtiene la política fiscal vigente por fecha."""

    @classmethod
    def resolver(
        cls,
        fecha_referencia: date | str | None,
        *,
        zona_frontera: bool = False,
    ) -> ContextoFiscalNomina:
        fecha = CatalogoUMA._coerce_fecha(fecha_referencia)
        vigencia_uma = CatalogoUMA.obtener_vigencia(fecha, permitir_fallback=True)
        vigencia_salario = CatalogoSalarioMinimo.obtener_vigencia(
            fecha,
            permitir_fallback=True,
        )
        politica_subsidio = CatalogoISR.obtener_politica_subsidio(
            fecha,
            permitir_fallback=True,
        )

        vigencia_soportada = all(
            (
                vigencia_uma is not None and vigencia_uma.aplica_a(fecha),
                vigencia_salario is not None and vigencia_salario.aplica_a(fecha),
                politica_subsidio is not None and politica_subsidio.aplica_a(fecha),
            )
        )

        mensajes: list[str] = []
        if vigencia_uma is None:
            mensajes.append("No existe vigencia UMA cargada para la fecha de pago.")
        elif not vigencia_uma.aplica_a(fecha):
            mensajes.append("La UMA usada es fallback; falta cargar la vigencia fiscal exacta.")

        if vigencia_salario is None:
            mensajes.append("No existe salario mínimo cargado para la fecha de pago.")
        elif not vigencia_salario.aplica_a(fecha):
            mensajes.append(
                "El salario mínimo usado es fallback; falta cargar la vigencia fiscal exacta."
            )

        if politica_subsidio is None:
            mensajes.append("No existe política de subsidio al empleo cargada para la fecha de pago.")
        elif not politica_subsidio.aplica_a(fecha):
            mensajes.append(
                "La política de subsidio al empleo usada es fallback; falta cargar la vigencia fiscal exacta."
            )

        uma_diaria = vigencia_uma.diario if vigencia_uma is not None else Decimal("0")
        uma_mensual = vigencia_uma.mensual if vigencia_uma is not None else Decimal("0")
        salario_minimo = (
            vigencia_salario.frontera if zona_frontera else vigencia_salario.general
        ) if vigencia_salario is not None else Decimal("0")

        return ContextoFiscalNomina(
            fecha_referencia=fecha,
            zona_frontera=zona_frontera,
            uma_diaria=uma_diaria,
            uma_mensual=uma_mensual,
            tres_uma=uma_diaria * Decimal("3"),
            tope_sbc=uma_diaria * Decimal("25"),
            salario_minimo_diario_aplicable=salario_minimo,
            limite_subsidio=(
                politica_subsidio.limite_ingreso_mensual
                if politica_subsidio is not None
                else Decimal("0")
            ),
            subsidio_mensual=(
                politica_subsidio.subsidio_mensual
                if politica_subsidio is not None
                else Decimal("0")
            ),
            vigencia_soportada=vigencia_soportada,
            mensaje_vigencia=" ".join(mensajes).strip(),
        )
