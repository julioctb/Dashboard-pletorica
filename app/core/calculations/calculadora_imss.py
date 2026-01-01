"""
Calculadora de cuotas IMSS (Instituto Mexicano del Seguro Social).

Separa la lógica de cálculo de IMSS patronal y obrero según la
Ley del Seguro Social vigente.

Responsabilidades:
- Cálculo de cuotas patronales (9 conceptos)
- Cálculo de cuotas obreras (5 conceptos)
- Aplicación del Art. 36 LSS (absorción de cuota obrera en salario mínimo)

Fecha: 2025-12-31 (Fase 2 de refactorización)
"""

from app.core.fiscales import ConstantesFiscales


class CalculadoraIMSS:
    """
    Calculadora de cuotas IMSS según Ley del Seguro Social.

    Maneja tanto cuotas patronales como obreras, incluyendo
    el caso especial del Art. 36 LSS para salario mínimo.
    """

    def __init__(self, constantes: type[ConstantesFiscales] = ConstantesFiscales):
        """
        Inicializa calculadora con constantes fiscales.

        Args:
            constantes: Clase con constantes fiscales (default: ConstantesFiscales)
        """
        self.const = constantes

    def calcular_patronal(
        self,
        sbc_diario: float,
        dias: int,
        prima_riesgo: float
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
        uma = self.const.UMA_DIARIO
        tres_uma = self.const.TRES_UMA
        excedente_base = max(0, sbc_diario - tres_uma)

        return {
            # Enfermedad y Maternidad
            "cuota_fija": uma * self.const.IMSS_CUOTA_FIJA * dias,
            "excedente": excedente_base * self.const.IMSS_EXCEDENTE_PAT * dias,
            "prest_dinero": sbc_diario * self.const.IMSS_PREST_DINERO_PAT * dias,
            "gastos_med": sbc_diario * self.const.IMSS_GASTOS_MED_PENS_PAT * dias,

            # Invalidez y Vida
            "invalidez_vida": sbc_diario * self.const.IMSS_INVALIDEZ_VIDA_PAT * dias,

            # Guarderías
            "guarderias": sbc_diario * self.const.IMSS_GUARDERIAS * dias,

            # Retiro, Cesantía y Vejez
            "retiro": sbc_diario * self.const.IMSS_RETIRO * dias,
            "cesantia_vejez": sbc_diario * self.const.IMSS_CESANTIA_VEJEZ_PAT * dias,

            # Riesgo de Trabajo (variable por empresa)
            "riesgo_trabajo": sbc_diario * prima_riesgo * dias,
        }

    def calcular_obrero(
        self,
        sbc_diario: float,
        dias: int,
        es_salario_minimo: bool,
        aplicar_art_36: bool
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
        tres_uma = self.const.TRES_UMA
        excedente_base = max(0, sbc_diario - tres_uma)

        if es_salario_minimo and aplicar_art_36:
            # ═════════════════════════════════════════════════════════════════
            # ART. 36 LSS: PATRÓN ABSORBE CUOTA OBRERA
            # ═════════════════════════════════════════════════════════════════
            # El patrón paga la cuota que le tocaría al trabajador
            # Trabajador NO tiene descuento IMSS
            imss_obrero_absorbido = (
                excedente_base * self.const.IMSS_EXCEDENTE_OBR * dias +
                sbc_diario * self.const.IMSS_PREST_DINERO_OBR * dias +
                sbc_diario * self.const.IMSS_GASTOS_MED_PENS_OBR * dias +
                sbc_diario * self.const.IMSS_INVALIDEZ_VIDA_OBR * dias +
                sbc_diario * self.const.IMSS_CESANTIA_VEJEZ_OBR * dias
            )

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
                "excedente": excedente_base * self.const.IMSS_EXCEDENTE_OBR * dias,
                "prest_dinero": sbc_diario * self.const.IMSS_PREST_DINERO_OBR * dias,
                "gastos_med": sbc_diario * self.const.IMSS_GASTOS_MED_PENS_OBR * dias,
                "invalidez_vida": sbc_diario * self.const.IMSS_INVALIDEZ_VIDA_OBR * dias,
                "cesantia_vejez": sbc_diario * self.const.IMSS_CESANTIA_VEJEZ_OBR * dias,
            }

        return cuotas, imss_obrero_absorbido

    def calcular_total_patronal(self, cuotas_patronales: dict[str, float]) -> float:
        """
        Suma todas las cuotas patronales.

        Args:
            cuotas_patronales: Dict retornado por calcular_patronal()

        Returns:
            Total de cuotas IMSS patronales
        """
        return sum(cuotas_patronales.values())

    def calcular_total_obrero(self, cuotas_obreras: dict[str, float]) -> float:
        """
        Suma todas las cuotas obreras.

        Args:
            cuotas_obreras: Dict retornado por calcular_obrero()[0]

        Returns:
            Total de cuotas IMSS obreras (descuento al trabajador)
        """
        return sum(cuotas_obreras.values())
