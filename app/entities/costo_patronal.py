"""
Entidades de dominio para cálculo de costo patronal.

Modelos puros de datos (dataclasses) que representan:
- ConfiguracionEmpresa: Configuración personalizable por empresa
- Trabajador: Datos de un trabajador individual
- ResultadoCuotas: Resultado detallado del cálculo de cuotas

Migrado desde app/core/calculations/simulador_costo_patronal.py
Fecha: 2025-12-31
"""

from dataclasses import dataclass
from typing import Optional
from app.core.fiscales import ConstantesFiscales, ISN_POR_ESTADO


# =============================================================================
# CONFIGURACIÓN DE EMPRESA
# =============================================================================

@dataclass
class ConfiguracionEmpresa:
    """
    Configuración personalizable por empresa.
    Ajusta estos valores según las políticas de cada empresa.
    """

    # ─────────────────────────────────────────────────────────────────────────
    # IDENTIFICACIÓN
    # ─────────────────────────────────────────────────────────────────────────
    nombre: str
    estado: str

    # ─────────────────────────────────────────────────────────────────────────
    # IMSS - RIESGO DE TRABAJO
    # ─────────────────────────────────────────────────────────────────────────
    prima_riesgo: float  # Ej: 0.025984 para 2.5984%

    # ─────────────────────────────────────────────────────────────────────────
    # REGISTRO PATRONAL (opcional - para simulaciones no es necesario)
    # ─────────────────────────────────────────────────────────────────────────
    registro_patronal: Optional[str] = None

    # ─────────────────────────────────────────────────────────────────────────
    # FACTOR DE INTEGRACIÓN
    # Si es None, se calcula automáticamente con la fórmula del IMSS.
    # Puedes fijarlo manualmente si el IMSS ya te asignó uno específico.
    # ─────────────────────────────────────────────────────────────────────────
    factor_integracion_fijo: Optional[float] = None  # Ej: 1.0493

    # ─────────────────────────────────────────────────────────────────────────
    # PRESTACIONES (para cálculo de factor de integración)
    # Valores mínimos de ley: aguinaldo=15, prima_vac=0.25
    # ─────────────────────────────────────────────────────────────────────────
    dias_aguinaldo: int = 15
    prima_vacacional: float = 0.25  # 25%
    dias_vacaciones_adicionales: int = 0  # Adicionales a la ley

    # ─────────────────────────────────────────────────────────────────────────
    # CONFIGURACIÓN DE DÍAS
    # ─────────────────────────────────────────────────────────────────────────
    dias_por_mes: float = 30.4  # Usar 30.4 para cálculos anuales más precisos

    # ─────────────────────────────────────────────────────────────────────────
    # ZONA GEOGRÁFICA
    # ─────────────────────────────────────────────────────────────────────────
    zona_frontera: bool = False  # True para zona fronteriza norte

    # ─────────────────────────────────────────────────────────────────────────
    # PRESTACIONES ADICIONALES (opcionales)
    # ─────────────────────────────────────────────────────────────────────────
    vales_despensa_mensual: float = 0.0
    fondo_ahorro_porcentaje: float = 0.0  # % del salario

    # ─────────────────────────────────────────────────────────────────────────
    # ART. 36 LSS - Absorción de cuota obrera
    # Por defecto True: patrón paga cuota obrera de trabajadores con SM
    # ─────────────────────────────────────────────────────────────────────────
    aplicar_art_36_lss: bool = True

    def __post_init__(self):
        """Valida estado y normaliza nombre"""
        self.estado = self.estado.lower().replace(" ", "_")
        if self.estado not in ISN_POR_ESTADO:
            raise ValueError(
                f"Estado '{self.estado}' no reconocido. "
                f"Estados válidos: {list(ISN_POR_ESTADO.keys())}"
            )

    @property
    def tasa_isn(self) -> float:
        """Retorna la tasa de ISN del estado configurado"""
        return ISN_POR_ESTADO[self.estado]

    @property
    def salario_minimo_aplicable(self) -> float:
        """Retorna el salario mínimo según zona geográfica"""
        if self.zona_frontera:
            return ConstantesFiscales.SALARIO_MINIMO_FRONTERA
        return ConstantesFiscales.SALARIO_MINIMO_GENERAL

    def calcular_factor_integracion(self, antiguedad_anos: int) -> float:
        """
        Calcula el factor de integración según fórmula del IMSS.

        Factor = 1 + (aguinaldo/365) + (prima_vac × días_vac / 365)

        Si hay un factor fijo configurado, lo usa en su lugar.

        Args:
            antiguedad_anos: Años de antigüedad del trabajador

        Returns:
            Factor de integración (ej: 1.0493)
        """
        if self.factor_integracion_fijo is not None:
            return self.factor_integracion_fijo

        dias_vac = (ConstantesFiscales.dias_vacaciones(antiguedad_anos) +
                    self.dias_vacaciones_adicionales)

        factor = 1.0
        factor += self.dias_aguinaldo / 365
        factor += (self.prima_vacacional * dias_vac) / 365

        return round(factor, 4)

   
# =============================================================================
# DATOS DEL TRABAJADOR
# =============================================================================

@dataclass
class Trabajador:
    """Datos de un trabajador individual"""

    nombre: str
    salario_diario: float
    antiguedad_anos: int = 1
    dias_cotizados_mes: int = 30
    zona_frontera: bool = False

    def es_salario_minimo(
        self,
        salario_minimo_aplicable: float,
        tolerancia: float = 0.01
    ) -> bool:
        """
        Verifica si gana el salario mínimo (con tolerancia de 1%).

        Args:
            salario_minimo_aplicable: Salario mínimo a comparar
            tolerancia: Margen de tolerancia (default 1% = 0.01)

        Returns:
            True si está dentro del rango de salario mínimo
        """
        diferencia = abs(self.salario_diario - salario_minimo_aplicable)
        return diferencia / salario_minimo_aplicable <= tolerancia


# =============================================================================
# RESULTADO DE CÁLCULO
# =============================================================================

@dataclass
class ResultadoCuotas:
    """Resultado detallado del cálculo de cuotas patronales y obreras"""

    # ─────────────────────────────────────────────────────────────────────────
    # IDENTIFICACIÓN
    # ─────────────────────────────────────────────────────────────────────────
    trabajador: str
    empresa: str

    # ─────────────────────────────────────────────────────────────────────────
    # SALARIOS
    # ─────────────────────────────────────────────────────────────────────────
    salario_diario: float
    salario_mensual: float
    factor_integracion: float
    sbc_diario: float
    sbc_mensual: float
    dias_cotizados: int

    # ─────────────────────────────────────────────────────────────────────────
    # IMSS PATRONAL
    # ─────────────────────────────────────────────────────────────────────────
    imss_cuota_fija: float = 0.0
    imss_excedente_pat: float = 0.0
    imss_prest_dinero_pat: float = 0.0
    imss_gastos_med_pens_pat: float = 0.0
    imss_invalidez_vida_pat: float = 0.0
    imss_guarderias: float = 0.0
    imss_retiro: float = 0.0
    imss_cesantia_vejez_pat: float = 0.0
    imss_riesgo_trabajo: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # IMSS OBRERO
    # ─────────────────────────────────────────────────────────────────────────
    imss_excedente_obr: float = 0.0
    imss_prest_dinero_obr: float = 0.0
    imss_gastos_med_pens_obr: float = 0.0
    imss_invalidez_vida_obr: float = 0.0
    imss_cesantia_vejez_obr: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # ART. 36 LSS
    # ─────────────────────────────────────────────────────────────────────────
    imss_obrero_absorbido: float = 0.0
    es_salario_minimo: bool = False

    # ─────────────────────────────────────────────────────────────────────────
    # OTROS PATRONALES
    # ─────────────────────────────────────────────────────────────────────────
    infonavit: float = 0.0
    isn: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # PROVISIONES
    # ─────────────────────────────────────────────────────────────────────────
    provision_aguinaldo: float = 0.0
    provision_vacaciones: float = 0.0
    provision_prima_vac: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # ISR
    # ─────────────────────────────────────────────────────────────────────────
    isr_base_gravable: float = 0.0
    isr_antes_subsidio: float = 0.0
    subsidio_empleo: float = 0.0
    isr_a_retener: float = 0.0

    # ═════════════════════════════════════════════════════════════════════════
    # PROPIEDADES CALCULADAS (TOTALES)
    # ═════════════════════════════════════════════════════════════════════════

    @property
    def total_imss_patronal(self) -> float:
        """Total de cuotas IMSS patronales"""
        return (
            self.imss_cuota_fija +
            self.imss_excedente_pat +
            self.imss_prest_dinero_pat +
            self.imss_gastos_med_pens_pat +
            self.imss_invalidez_vida_pat +
            self.imss_guarderias +
            self.imss_retiro +
            self.imss_cesantia_vejez_pat +
            self.imss_riesgo_trabajo
        )

    @property
    def total_imss_obrero(self) -> float:
        """Total de cuotas IMSS obreras (descuento al trabajador)"""
        return (
            self.imss_excedente_obr +
            self.imss_prest_dinero_obr +
            self.imss_gastos_med_pens_obr +
            self.imss_invalidez_vida_obr +
            self.imss_cesantia_vejez_obr
        )

    @property
    def total_descuentos_trabajador(self) -> float:
        """
        Total de descuentos fiscales obligatorios al trabajador.

        Incluye SOLO:
        - IMSS Obrero (5 ramos): Excedente 3 UMA, Prestaciones en dinero,
          Gastos médicos pensionados, Invalidez y vida, Cesantía y vejez
        - ISR (Impuesto Sobre la Renta): Retención mensual con subsidio al empleo

        NO incluye descuentos variables:
        - Préstamos INFONAVIT/FONACOT
        - Pensión alimenticia
        - Faltas/incapacidades
        - Anticipos/préstamos de la empresa
        - Cuotas sindicales
        """
        return self.total_imss_obrero + self.isr_a_retener

    @property
    def salario_neto(self) -> float:
        """
        Salario neto que recibe el trabajador después de descuentos obligatorios.

        Fórmula: Salario Bruto - (IMSS Obrero + ISR)

        IMPORTANTE: Este es el salario neto FISCAL estándar, calculado con
        descuentos obligatorios únicamente. Para calcular el salario neto REAL
        que aparecerá en el recibo de nómina, deben agregarse descuentos
        adicionales como:
        - Préstamos INFONAVIT (amortización de crédito)
        - Préstamos FONACOT
        - Pensión alimenticia (orden judicial)
        - Faltas/incapacidades
        - Anticipos/préstamos internos

        Ejemplo:
            Salario bruto: $15,000.00
            - IMSS Obrero:    -$537.75
            - ISR:          -$1,339.14
            ──────────────────────────
            Salario neto:  $13,123.11

        Returns:
            Salario neto mensual después de descuentos fiscales obligatorios
        """
        return self.salario_mensual - self.total_descuentos_trabajador

    @property
    def total_provisiones(self) -> float:
        """Total de provisiones mensuales (aguinaldo + vacaciones + prima)"""
        return (
            self.provision_aguinaldo +
            self.provision_vacaciones +
            self.provision_prima_vac
        )

    @property
    def total_carga_patronal(self) -> float:
        """
        Total de lo que paga el patrón además del salario.

        Incluye:
        - IMSS patronal
        - INFONAVIT
        - ISN
        - Provisiones
        - IMSS obrero absorbido (Art. 36 LSS)
        """
        return (
            self.total_imss_patronal +
            self.infonavit +
            self.isn +
            self.total_provisiones +
            self.imss_obrero_absorbido
        )

    @property
    def costo_total(self) -> float:
        """Costo total mensual para la empresa (salario + cargas)"""
        return self.salario_mensual + self.total_carga_patronal

    @property
    def factor_costo(self) -> float:
        """
        Factor de costo patronal (cuánto cuesta el empleado vs su salario).

        Ejemplo: factor_costo = 1.35 significa que el empleado cuesta 35% más
        de su salario nominal.
        """
        if self.salario_mensual > 0:
            return self.costo_total / self.salario_mensual
        return 0.0
