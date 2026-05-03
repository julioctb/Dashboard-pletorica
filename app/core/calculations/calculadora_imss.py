"""
Calculadora de cuotas IMSS (Instituto Mexicano del Seguro Social).

Separa la lógica de cálculo de IMSS patronal y obrero según la
Ley del Seguro Social vigente.

Responsabilidades:
- Cálculo de cuotas patronales (9 conceptos)
- Cálculo de cuotas obreras (5 conceptos)
- Aplicación del Art. 36 LSS (absorción de cuota obrera en salario mínimo)

Fecha: 2025-12-31 (Fase 2 de refactorización)
Actualizado: 2026-01-17 (Migración a catálogos)
"""

from decimal import Decimal, ROUND_HALF_UP

from app.core.catalogs import CatalogoUMA, CatalogoIMSS


CENTAVO = Decimal("0.01")


def _decimal(value: Decimal | float | int | str | None) -> Decimal:
    """Convierte entradas numéricas a Decimal evitando artefactos de float."""
    return Decimal(str(value or 0))


def _moneda(value: Decimal) -> float:
    """Devuelve pesos con dos decimales para mantener la API serializable."""
    return float(value.quantize(CENTAVO, rounding=ROUND_HALF_UP))


class CalculadoraIMSS:
    """
    Calculadora de cuotas IMSS según Ley del Seguro Social.

    Maneja tanto cuotas patronales como obreras, incluyendo
    el caso especial del Art. 36 LSS para salario mínimo.
    """

    def calcular_patronal(
        self,
        sbc_diario: float,
        dias: int,
        prima_riesgo: float,
        uma_diaria: float | None = None,
        salario_minimo_diario: float | None = None,
        ano: int = CatalogoIMSS.ANO,
    ) -> dict[str, float]:
        """
        Calcula todas las cuotas IMSS patronales.

        Incluye los 9 conceptos que paga el patrón:
        1. Cuota fija (Enfermedad y Maternidad)
        2. Excedente 3 UMA (E.M.)
        3. Prestaciones en dinero (E.M.)
        4. Gastos médicos pensionados
        5. Invalidez y vida
        6. Guarderías y prestaciones sociales
        7. Retiro
        8. Cesantía y vejez
        9. Riesgo de trabajo

        Args:
            sbc_diario: Salario Base de Cotización diario
            dias: Días cotizados en el mes
            prima_riesgo: Prima de riesgo de la empresa (ej: 0.025984 para 2.5984%)
            uma_diaria: UMA vigente para la fecha de cálculo
            salario_minimo_diario: Salario mínimo vigente para resolver C&V
            ano: Año fiscal para tabla transitoria de Cesantía y Vejez

        Returns:
            Diccionario con las 9 cuotas patronales:
            {
                "cuota_fija": float,
                "excedente": float,
                "prest_dinero": float,
                "gastos_med": float,
                "invalidez_vida": float,
                "guarderias": float,
                "retiro": float,
                "cesantia_vejez": float,
                "riesgo_trabajo": float
            }
        """
        sbc = _decimal(sbc_diario)
        dias_decimal = _decimal(dias)
        prima = _decimal(prima_riesgo)
        uma = _decimal(uma_diaria if uma_diaria is not None else CatalogoUMA.DIARIO)
        tres_uma = uma * Decimal("3")
        excedente_base = max(Decimal("0"), sbc - tres_uma)
        tasa_cesantia_vejez = CatalogoIMSS.tasa_cesantia_vejez_patronal(
            sbc,
            uma,
            salario_minimo_diario=(
                _decimal(salario_minimo_diario)
                if salario_minimo_diario is not None
                else None
            ),
            ano=ano,
        )

        return {
            # Enfermedad y Maternidad
            "cuota_fija": _moneda(uma * CatalogoIMSS.CUOTA_FIJA * dias_decimal),
            "excedente": _moneda(excedente_base * CatalogoIMSS.EXCEDENTE_PATRONAL * dias_decimal),
            "prest_dinero": _moneda(sbc * CatalogoIMSS.PREST_DINERO_PATRONAL * dias_decimal),
            "gastos_med": _moneda(sbc * CatalogoIMSS.GASTOS_MED_PATRONAL * dias_decimal),

            # Invalidez y Vida
            "invalidez_vida": _moneda(sbc * CatalogoIMSS.INVALIDEZ_VIDA_PATRONAL * dias_decimal),

            # Guarderías
            "guarderias": _moneda(sbc * CatalogoIMSS.GUARDERIAS * dias_decimal),

            # Retiro, Cesantía y Vejez
            "retiro": _moneda(sbc * CatalogoIMSS.RETIRO * dias_decimal),
            "cesantia_vejez": _moneda(sbc * tasa_cesantia_vejez * dias_decimal),

            # Riesgo de Trabajo (variable por empresa)
            "riesgo_trabajo": _moneda(sbc * prima * dias_decimal),
        }

    def calcular_obrero(
        self,
        sbc_diario: float,
        dias: int,
        es_salario_minimo: bool,
        aplicar_art_36: bool,
        uma_diaria: float | None = None,
    ) -> tuple[dict[str, float], float]:
        """
        Calcula cuotas IMSS obreras (descuentos al trabajador).

        Maneja el caso especial del Art. 36 LSS: cuando el trabajador
        gana salario mínimo y la empresa aplica el artículo, el patrón
        absorbe la cuota obrera.

        Incluye los 5 conceptos que se descuentan al trabajador:
        1. Excedente 3 UMA (E.M.)
        2. Prestaciones en dinero (E.M.)
        3. Gastos médicos pensionados
        4. Invalidez y vida
        5. Cesantía y vejez

        Args:
            sbc_diario: Salario Base de Cotización diario
            dias: Días cotizados en el mes
            es_salario_minimo: True si el trabajador gana salario mínimo
            aplicar_art_36: True si la empresa aplica Art. 36 LSS

        Returns:
            Tupla (cuotas_dict, imss_obrero_absorbido):
            - cuotas_dict: Diccionario con las 5 cuotas obreras
            - imss_obrero_absorbido: Monto que absorbe el patrón (Art. 36)

        Ejemplo:
            >>> calc = CalculadoraIMSS()
            >>> cuotas, absorbido = calc.calcular_obrero(315.04, 30, True, True)
            >>> # Trabajador SM: cuotas = {todos en 0}, absorbido > 0
            >>> cuotas, absorbido = calc.calcular_obrero(500.0, 30, False, True)
            >>> # Trabajador normal: cuotas con valores, absorbido = 0
        """
        sbc = _decimal(sbc_diario)
        dias_decimal = _decimal(dias)
        uma = _decimal(uma_diaria if uma_diaria is not None else CatalogoUMA.DIARIO)
        tres_uma = uma * Decimal("3")
        excedente_base = max(Decimal("0"), sbc - tres_uma)

        if es_salario_minimo and aplicar_art_36:
            # ═════════════════════════════════════════════════════════════════
            # ART. 36 LSS: PATRÓN ABSORBE CUOTA OBRERA
            # ═════════════════════════════════════════════════════════════════
            # El patrón paga la cuota que le tocaría al trabajador
            # Trabajador NO tiene descuento IMSS
            imss_obrero_absorbido_decimal = (
                excedente_base * CatalogoIMSS.EXCEDENTE_OBRERO * dias_decimal +
                sbc * CatalogoIMSS.PREST_DINERO_OBRERO * dias_decimal +
                sbc * CatalogoIMSS.GASTOS_MED_OBRERO * dias_decimal +
                sbc * CatalogoIMSS.INVALIDEZ_VIDA_OBRERO * dias_decimal +
                sbc * CatalogoIMSS.CESANTIA_VEJEZ_OBRERO * dias_decimal
            )
            imss_obrero_absorbido = _moneda(imss_obrero_absorbido_decimal)

            # Cuotas obreras en cero (no se descuentan al trabajador)
            cuotas = {
                "excedente": 0.0,
                "prest_dinero": 0.0,
                "gastos_med": 0.0,
                "invalidez_vida": 0.0,
                "cesantia_vejez": 0.0,
            }
        else:
            # ═════════════════════════════════════════════════════════════════
            # CÁLCULO NORMAL: SE DESCUENTA AL TRABAJADOR
            # ═════════════════════════════════════════════════════════════════
            imss_obrero_absorbido = 0.0

            cuotas = {
                "excedente": _moneda(excedente_base * CatalogoIMSS.EXCEDENTE_OBRERO * dias_decimal),
                "prest_dinero": _moneda(sbc * CatalogoIMSS.PREST_DINERO_OBRERO * dias_decimal),
                "gastos_med": _moneda(sbc * CatalogoIMSS.GASTOS_MED_OBRERO * dias_decimal),
                "invalidez_vida": _moneda(sbc * CatalogoIMSS.INVALIDEZ_VIDA_OBRERO * dias_decimal),
                "cesantia_vejez": _moneda(sbc * CatalogoIMSS.CESANTIA_VEJEZ_OBRERO * dias_decimal),
            }

        return cuotas, imss_obrero_absorbido
