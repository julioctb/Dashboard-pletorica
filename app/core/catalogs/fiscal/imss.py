"""
Catálogo de tasas IMSS (Instituto Mexicano del Seguro Social).

Contiene todas las tasas de cotización para las diferentes ramas
del seguro social, tanto patronales como obreras.

Fuente: Ley del Seguro Social
Artículos: 25, 106, 107, 147, 168
"""

from decimal import Decimal
from typing import ClassVar
from dataclasses import dataclass
from enum import Enum


class RamaSeguro(str, Enum):
    """Ramas del seguro social."""
    ENFERMEDAD_MATERNIDAD = "enfermedad_maternidad"
    INVALIDEZ_VIDA = "invalidez_vida"
    RETIRO = "retiro"
    CESANTIA_VEJEZ = "cesantia_vejez"
    GUARDERIAS = "guarderias"
    RIESGO_TRABAJO = "riesgo_trabajo"


@dataclass(frozen=True)
class TasaIMSS:
    """Representa una tasa de cotización IMSS."""
    concepto: str
    patronal: Decimal
    obrero: Decimal
    base: str
    rama: RamaSeguro

    @property
    def total(self) -> Decimal:
        """Suma de tasa patronal + obrera."""
        return self.patronal + self.obrero


class CatalogoIMSS:
    """
    Tasas de cotización IMSS 2026.

    Incluye todas las ramas del seguro social con sus respectivas
    cuotas patronales y obreras.

    Uso:
        from app.core.catalogs import CatalogoIMSS

        cuota = sbc * CatalogoIMSS.CUOTA_FIJA
        total_pat = CatalogoIMSS.total_patronal_fijo()
    """

    # ═══════════════════════════════════════════════════════════════
    # METADATOS
    # ═══════════════════════════════════════════════════════════════
    ANO: ClassVar[int] = 2026
    FUENTE: ClassVar[str] = "Ley del Seguro Social"
    ARTICULOS: ClassVar[list[str]] = ["Art. 25", "Art. 106", "Art. 147", "Art. 168"]
    NOTAS: ClassVar[str] = "Cesantía patronal progresiva por rango de SBC, reforma 2020-2030"

    # ═══════════════════════════════════════════════════════════════
    # ENFERMEDAD Y MATERNIDAD
    # ═══════════════════════════════════════════════════════════════

    # Cuota fija (solo patronal, sobre UMA hasta 3 UMA)
    CUOTA_FIJA: ClassVar[Decimal] = Decimal("0.204")  # 20.4%

    # Excedente de 3 UMA
    EXCEDENTE_PATRONAL: ClassVar[Decimal] = Decimal("0.011")   # 1.10%
    EXCEDENTE_OBRERO: ClassVar[Decimal] = Decimal("0.004")     # 0.40%

    # Prestaciones en dinero
    PREST_DINERO_PATRONAL: ClassVar[Decimal] = Decimal("0.007")   # 0.70%
    PREST_DINERO_OBRERO: ClassVar[Decimal] = Decimal("0.0025")    # 0.25%

    # Gastos médicos para pensionados
    GASTOS_MED_PATRONAL: ClassVar[Decimal] = Decimal("0.0105")    # 1.05%
    GASTOS_MED_OBRERO: ClassVar[Decimal] = Decimal("0.00375")     # 0.375%

    # ═══════════════════════════════════════════════════════════════
    # INVALIDEZ Y VIDA
    # ═══════════════════════════════════════════════════════════════
    INVALIDEZ_VIDA_PATRONAL: ClassVar[Decimal] = Decimal("0.0175")   # 1.75%
    INVALIDEZ_VIDA_OBRERO: ClassVar[Decimal] = Decimal("0.00625")    # 0.625%

    # ═══════════════════════════════════════════════════════════════
    # GUARDERÍAS Y PRESTACIONES SOCIALES (solo patronal)
    # ═══════════════════════════════════════════════════════════════
    GUARDERIAS: ClassVar[Decimal] = Decimal("0.01")  # 1.00%

    # ═══════════════════════════════════════════════════════════════
    # RETIRO, CESANTÍA Y VEJEZ
    # ═══════════════════════════════════════════════════════════════
    RETIRO: ClassVar[Decimal] = Decimal("0.02")  # 2.00% (solo patronal)

    # Cesantía y Vejez - REFORMA GRADUAL 2020-2030
    # Alias legacy: tasa patronal máxima aplicable en 2026.
    # Para cálculo real usar `tasa_cesantia_vejez_patronal`.
    CESANTIA_VEJEZ_PATRONAL: ClassVar[Decimal] = Decimal("0.07513")  # 7.513%
    CESANTIA_VEJEZ_OBRERO: ClassVar[Decimal] = Decimal("0.01125")    # 1.125%

    # Tasas patronales de cesantía y vejez por año y rango de SBC.
    # Orden de rangos:
    # 1. 1.00 SM
    # 2. 1.01 SM a 1.50 UMA
    # 3. 1.51 a 2.00 UMA
    # 4. 2.01 a 2.50 UMA
    # 5. 2.51 a 3.00 UMA
    # 6. 3.01 a 3.50 UMA
    # 7. 3.51 a 4.00 UMA
    # 8. 4.01 UMA en adelante
    CESANTIA_VEJEZ_PATRONAL_TRANSICION: ClassVar[dict[int, tuple[Decimal, ...]]] = {
        2023: (
            Decimal("0.03150"),
            Decimal("0.03281"),
            Decimal("0.03575"),
            Decimal("0.03751"),
            Decimal("0.03869"),
            Decimal("0.03953"),
            Decimal("0.04016"),
            Decimal("0.04241"),
        ),
        2024: (
            Decimal("0.03150"),
            Decimal("0.03413"),
            Decimal("0.04000"),
            Decimal("0.04353"),
            Decimal("0.04588"),
            Decimal("0.04756"),
            Decimal("0.04882"),
            Decimal("0.05331"),
        ),
        2025: (
            Decimal("0.03150"),
            Decimal("0.03544"),
            Decimal("0.04426"),
            Decimal("0.04954"),
            Decimal("0.05307"),
            Decimal("0.05559"),
            Decimal("0.05747"),
            Decimal("0.06422"),
        ),
        2026: (
            Decimal("0.03150"),
            Decimal("0.03676"),
            Decimal("0.04851"),
            Decimal("0.05556"),
            Decimal("0.06026"),
            Decimal("0.06361"),
            Decimal("0.06613"),
            Decimal("0.07513"),
        ),
        2027: (
            Decimal("0.03150"),
            Decimal("0.03807"),
            Decimal("0.05276"),
            Decimal("0.06157"),
            Decimal("0.06745"),
            Decimal("0.07164"),
            Decimal("0.07479"),
            Decimal("0.08603"),
        ),
        2028: (
            Decimal("0.03150"),
            Decimal("0.03939"),
            Decimal("0.05701"),
            Decimal("0.06759"),
            Decimal("0.07464"),
            Decimal("0.07967"),
            Decimal("0.08345"),
            Decimal("0.09694"),
        ),
        2029: (
            Decimal("0.03150"),
            Decimal("0.04070"),
            Decimal("0.06126"),
            Decimal("0.07360"),
            Decimal("0.08183"),
            Decimal("0.08770"),
            Decimal("0.09211"),
            Decimal("0.10784"),
        ),
        2030: (
            Decimal("0.03150"),
            Decimal("0.04202"),
            Decimal("0.06552"),
            Decimal("0.07962"),
            Decimal("0.08902"),
            Decimal("0.09573"),
            Decimal("0.10077"),
            Decimal("0.11875"),
        ),
    }

    # Histórico de tasas máximas patronales de cesantía (para referencia)
    CESANTIA_VEJEZ_HISTORICO: ClassVar[dict[int, Decimal]] = {
        2023: Decimal("0.04241"),
        2024: Decimal("0.05331"),
        2025: Decimal("0.06422"),
        2026: Decimal("0.07513"),
        2027: Decimal("0.08603"),
        2028: Decimal("0.09694"),
        2029: Decimal("0.10784"),
        2030: Decimal("0.11875"),
    }

    # ═══════════════════════════════════════════════════════════════
    # DATOS ESTRUCTURADOS (para iteración/reportes)
    # ═══════════════════════════════════════════════════════════════

    TASAS: ClassVar[list[TasaIMSS]] = [
        TasaIMSS("Cuota fija", Decimal("0.204"), Decimal("0"), "SBC hasta 3 UMA", RamaSeguro.ENFERMEDAD_MATERNIDAD),
        TasaIMSS("Excedente 3 UMA", Decimal("0.011"), Decimal("0.004"), "SBC excedente", RamaSeguro.ENFERMEDAD_MATERNIDAD),
        TasaIMSS("Prest. en dinero", Decimal("0.007"), Decimal("0.0025"), "SBC", RamaSeguro.ENFERMEDAD_MATERNIDAD),
        TasaIMSS("Gastos médicos", Decimal("0.0105"), Decimal("0.00375"), "SBC", RamaSeguro.ENFERMEDAD_MATERNIDAD),
        TasaIMSS("Invalidez y vida", Decimal("0.0175"), Decimal("0.00625"), "SBC", RamaSeguro.INVALIDEZ_VIDA),
        TasaIMSS("Guarderías", Decimal("0.01"), Decimal("0"), "SBC", RamaSeguro.GUARDERIAS),
        TasaIMSS("Retiro", Decimal("0.02"), Decimal("0"), "SBC", RamaSeguro.RETIRO),
        TasaIMSS("Cesantía y vejez", CESANTIA_VEJEZ_PATRONAL, Decimal("0.01125"), "SBC por rango", RamaSeguro.CESANTIA_VEJEZ),
    ]

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS DE CÁLCULO
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def tasa_cesantia_vejez_patronal(
        cls,
        sbc_diario: Decimal | float | int | str,
        uma_diaria: Decimal | float | int | str,
        *,
        salario_minimo_diario: Decimal | float | int | str | None = None,
        ano: int | None = None,
    ) -> Decimal:
        """
        Resuelve la tasa patronal de Cesantía y Vejez por rango de SBC.

        La tabla transitoria aplica de 2023 a 2030. Para años previos se
        conserva la tasa histórica de 3.150%; para años posteriores se usa la
        tabla final 2030.
        """
        sbc = Decimal(str(sbc_diario or 0))
        uma = Decimal(str(uma_diaria or 0))
        if sbc <= 0 or uma <= 0:
            return Decimal("0")

        ano_tabla = int(ano or cls.ANO)
        if ano_tabla < 2023:
            tasas = (Decimal("0.03150"),) * 8
        elif ano_tabla > 2030:
            tasas = cls.CESANTIA_VEJEZ_PATRONAL_TRANSICION[2030]
        else:
            tasas = cls.CESANTIA_VEJEZ_PATRONAL_TRANSICION[ano_tabla]

        salario_minimo = (
            Decimal(str(salario_minimo_diario))
            if salario_minimo_diario is not None
            else Decimal("0")
        )
        if (
            salario_minimo > 0
            and sbc.quantize(Decimal("0.01")) == salario_minimo.quantize(Decimal("0.01"))
        ):
            return tasas[0]

        sbc_en_uma = sbc / uma
        if salario_minimo <= 0 and sbc_en_uma <= Decimal("1.00"):
            return tasas[0]
        if sbc_en_uma <= Decimal("1.50"):
            return tasas[1]
        if sbc_en_uma <= Decimal("2.00"):
            return tasas[2]
        if sbc_en_uma <= Decimal("2.50"):
            return tasas[3]
        if sbc_en_uma <= Decimal("3.00"):
            return tasas[4]
        if sbc_en_uma <= Decimal("3.50"):
            return tasas[5]
        if sbc_en_uma <= Decimal("4.00"):
            return tasas[6]
        return tasas[7]

    @classmethod
    def total_patronal_fijo(
        cls,
        *,
        sbc_diario: Decimal | float | int | str | None = None,
        uma_diaria: Decimal | float | int | str | None = None,
        salario_minimo_diario: Decimal | float | int | str | None = None,
        ano: int | None = None,
    ) -> Decimal:
        """
        Total de cuotas patronales fijas (sin riesgo de trabajo).

        El riesgo de trabajo varía por empresa, por eso no se incluye. Si se
        provee SBC/UMA, usa la tasa real de Cesantía y Vejez por rango; si no,
        mantiene la tasa máxima 2026 como referencia legacy.
        """
        cesantia_vejez = (
            cls.tasa_cesantia_vejez_patronal(
                sbc_diario,
                uma_diaria,
                salario_minimo_diario=salario_minimo_diario,
                ano=ano,
            )
            if sbc_diario is not None and uma_diaria is not None
            else cls.CESANTIA_VEJEZ_PATRONAL
        )
        return (
            cls.CUOTA_FIJA +
            cls.EXCEDENTE_PATRONAL +
            cls.PREST_DINERO_PATRONAL +
            cls.GASTOS_MED_PATRONAL +
            cls.INVALIDEZ_VIDA_PATRONAL +
            cls.GUARDERIAS +
            cls.RETIRO +
            cesantia_vejez
        )

    @classmethod
    def total_obrero(cls) -> Decimal:
        """Total de cuotas que se descuentan al trabajador."""
        return (
            cls.EXCEDENTE_OBRERO +
            cls.PREST_DINERO_OBRERO +
            cls.GASTOS_MED_OBRERO +
            cls.INVALIDEZ_VIDA_OBRERO +
            cls.CESANTIA_VEJEZ_OBRERO
        )

    @classmethod
    def total_patronal_con_riesgo(cls, prima_riesgo: Decimal) -> Decimal:
        """
        Total patronal incluyendo riesgo de trabajo.

        Args:
            prima_riesgo: Prima de riesgo de la empresa (0.005 - 0.15)
        """
        return cls.total_patronal_fijo() + prima_riesgo
