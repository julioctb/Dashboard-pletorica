"""
Calculadora de Costo Patronal - México
Versión Configurable - 2026

Permite ajustar todas las variables por empresa:
- Factor de integración personalizado
- Prima de riesgo específica
- Prestaciones superiores a la ley
- Días de pago por mes (30 o 30.4)
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# =============================================================================
# CONSTANTES FISCALES (LEYES VIGENTES)
# =============================================================================

class ConstantesFiscales:
    """
    Constantes definidas por ley - NO MODIFICAR
    Estas son las tasas oficiales de IMSS, INFONAVIT, etc.
    """
    
    # Año fiscal
    ANO = 2026
    
    # ─────────────────────────────────────────────────────────────────────────
    # UMA - Unidad de Medida y Actualización
    # NOTA: Actualizar cuando INEGI publique (enero), vigente desde 1-feb
    # ─────────────────────────────────────────────────────────────────────────
    UMA_DIARIO = 113.14  # Vigente hasta 31-ene-2026
    UMA_MENSUAL = UMA_DIARIO * 30.4  # $3,439.46
    
    # ─────────────────────────────────────────────────────────────────────────
    # SALARIOS MÍNIMOS 2026 (DOF 9-dic-2025)
    # ─────────────────────────────────────────────────────────────────────────
    SALARIO_MINIMO_GENERAL = 315.04
    SALARIO_MINIMO_FRONTERA = 440.87
    
    # ─────────────────────────────────────────────────────────────────────────
    # IMSS - Tasas de cotización (Ley del Seguro Social)
    # ─────────────────────────────────────────────────────────────────────────
    
    # Enfermedades y Maternidad
    IMSS_CUOTA_FIJA = 0.204            # 20.4% del UMA (solo patronal)
    IMSS_EXCEDENTE_PAT = 0.011         # 1.10% sobre excedente de 3 UMA
    IMSS_EXCEDENTE_OBR = 0.004         # 0.40% sobre excedente de 3 UMA
    IMSS_PREST_DINERO_PAT = 0.007      # 0.70% del SBC
    IMSS_PREST_DINERO_OBR = 0.0025     # 0.25% del SBC
    IMSS_GASTOS_MED_PENS_PAT = 0.0105  # 1.05% del SBC
    IMSS_GASTOS_MED_PENS_OBR = 0.00375 # 0.375% del SBC
    
    # Invalidez y Vida
    IMSS_INVALIDEZ_VIDA_PAT = 0.0175   # 1.75% del SBC
    IMSS_INVALIDEZ_VIDA_OBR = 0.00625  # 0.625% del SBC
    
    # Guarderías y Prestaciones Sociales (solo patronal)
    IMSS_GUARDERIAS = 0.01             # 1.00% del SBC
    
    # Retiro, Cesantía y Vejez
    IMSS_RETIRO = 0.02                 # 2.00% del SBC (solo patronal)
    
    # Cesantía y Vejez - REFORMA GRADUAL 2020-2030
    # Año 2026: incremento de 0.175% respecto a 2025
    IMSS_CESANTIA_VEJEZ_PAT = 0.03513  # 3.513% (antes 3.338%)
    IMSS_CESANTIA_VEJEZ_OBR = 0.01125  # 1.125% (fijo)
    
    # ─────────────────────────────────────────────────────────────────────────
    # INFONAVIT
    # ─────────────────────────────────────────────────────────────────────────
    INFONAVIT_PAT = 0.05               # 5% del SBC
    
    # ─────────────────────────────────────────────────────────────────────────
    # TOPES
    # ─────────────────────────────────────────────────────────────────────────
    TOPE_SBC_DIARIO = UMA_DIARIO * 25  # 25 UMA = $2,828.50
    TRES_UMA = UMA_DIARIO * 3          # Para cálculo de excedente
    
    # ─────────────────────────────────────────────────────────────────────────
    # SUBSIDIO AL EMPLEO (Decreto DOF 31-dic-2024)
    # ─────────────────────────────────────────────────────────────────────────
    SUBSIDIO_PORCENTAJE = 0.138        # 13.8% del UMA mensual
    SUBSIDIO_EMPLEO_MENSUAL = UMA_MENSUAL * SUBSIDIO_PORCENTAJE  # $474.65
    LIMITE_SUBSIDIO_MENSUAL = 10_171.00
    
    # ─────────────────────────────────────────────────────────────────────────
    # TABLAS ISR 2025 (vigentes hasta que SAT publique Anexo 8 2026)
    # ─────────────────────────────────────────────────────────────────────────
    TABLA_ISR_MENSUAL = [
        # (límite_inferior, límite_superior, cuota_fija, tasa_excedente)
        (0.01, 746.04, 0.00, 0.0192),
        (746.05, 6332.05, 14.32, 0.0640),
        (6332.06, 11128.01, 371.83, 0.1088),
        (11128.02, 12935.82, 893.63, 0.1600),
        (12935.83, 15487.71, 1182.88, 0.1792),
        (15487.72, 31236.49, 1640.18, 0.2136),
        (31236.50, 49233.00, 5004.12, 0.2352),
        (49233.01, 93993.90, 9236.89, 0.3000),
        (93993.91, 125325.20, 22665.17, 0.3200),
        (125325.21, 375975.61, 32691.18, 0.3400),
        (375975.62, float('inf'), 117912.32, 0.3500),
    ]
    
    # ─────────────────────────────────────────────────────────────────────────
    # VACACIONES (Art. 76 LFT - Reforma 2023)
    # ─────────────────────────────────────────────────────────────────────────
    DIAS_VACACIONES_POR_ANO = {
        1: 12, 2: 14, 3: 16, 4: 18, 5: 20,
        6: 22, 7: 22, 8: 22, 9: 22, 10: 22,
        11: 24, 12: 24, 13: 24, 14: 24, 15: 24,
        16: 26, 17: 26, 18: 26, 19: 26, 20: 26,
        21: 28, 22: 28, 23: 28, 24: 28, 25: 28,
        26: 30, 27: 30, 28: 30, 29: 30, 30: 30,
    }
    
    @classmethod
    def dias_vacaciones(cls, antiguedad_anos: int) -> int:
        if antiguedad_anos <= 0:
            return 12
        if antiguedad_anos > 30:
            return 30 + ((antiguedad_anos - 30) // 5) * 2
        return cls.DIAS_VACACIONES_POR_ANO.get(antiguedad_anos, 12)


# =============================================================================
# ISN POR ESTADO
# =============================================================================

ISN_POR_ESTADO = {
    "aguascalientes": 0.030,
    "baja_california": 0.0265,
    "baja_california_sur": 0.025,
    "campeche": 0.030,
    "chiapas": 0.020,
    "chihuahua": 0.030,
    "ciudad_de_mexico": 0.030,
    "cdmx": 0.030,
    "coahuila": 0.030,
    "colima": 0.020,
    "durango": 0.020,
    "estado_de_mexico": 0.030,
    "guanajuato": 0.0295,
    "guerrero": 0.020,
    "hidalgo": 0.030,
    "jalisco": 0.030,
    "michoacan": 0.030,
    "morelos": 0.020,
    "nayarit": 0.020,
    "nuevo_leon": 0.030,
    "oaxaca": 0.030,
    "puebla": 0.030,
    "queretaro": 0.030,
    "quintana_roo": 0.030,
    "san_luis_potosi": 0.030,
    "sinaloa": 0.0265,
    "sonora": 0.0265,
    "tabasco": 0.030,
    "tamaulipas": 0.030,
    "tlaxcala": 0.030,
    "veracruz": 0.030,
    "yucatan": 0.030,
    "zacatecas": 0.030,
}


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
    registro_patronal: str
    estado: str
    
    # ─────────────────────────────────────────────────────────────────────────
    # IMSS - RIESGO DE TRABAJO
    # ─────────────────────────────────────────────────────────────────────────
    prima_riesgo: float  # Ej: 0.025984 para 2.5984%
    
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
        self.estado = self.estado.lower().replace(" ", "_")
        if self.estado not in ISN_POR_ESTADO:
            raise ValueError(f"Estado '{self.estado}' no reconocido. Estados válidos: {list(ISN_POR_ESTADO.keys())}")
    
    @property
    def tasa_isn(self) -> float:
        return ISN_POR_ESTADO[self.estado]
    
    @property
    def salario_minimo_aplicable(self) -> float:
        if self.zona_frontera:
            return ConstantesFiscales.SALARIO_MINIMO_FRONTERA
        return ConstantesFiscales.SALARIO_MINIMO_GENERAL
    
    def calcular_factor_integracion(self, antiguedad_anos: int) -> float:
        """
        Calcula el factor de integración según fórmula del IMSS.
        
        Factor = 1 + (aguinaldo/365) + (prima_vac × días_vac / 365)
        
        Si hay un factor fijo configurado, lo usa en su lugar.
        """
        if self.factor_integracion_fijo is not None:
            return self.factor_integracion_fijo
        
        dias_vac = ConstantesFiscales.dias_vacaciones(antiguedad_anos) + self.dias_vacaciones_adicionales
        
        factor = 1.0
        factor += self.dias_aguinaldo / 365
        factor += (self.prima_vacacional * dias_vac) / 365
        
        return round(factor, 4)
    
    def mostrar_configuracion(self):
        """Imprime la configuración actual de la empresa"""
        print("\n" + "="*60)
        print(f"CONFIGURACIÓN: {self.nombre}")
        print("="*60)
        print(f"  Registro patronal:     {self.registro_patronal}")
        print(f"  Estado:                {self.estado.title()} (ISN: {self.tasa_isn:.1%})")
        print(f"  Prima de riesgo:       {self.prima_riesgo:.4%}")
        print(f"  Zona frontera:         {'Sí' if self.zona_frontera else 'No'}")
        print(f"  Salario mínimo:        ${self.salario_minimo_aplicable:,.2f}")
        print(f"\n  PRESTACIONES:")
        print(f"  Días aguinaldo:        {self.dias_aguinaldo}")
        print(f"  Prima vacacional:      {self.prima_vacacional:.0%}")
        print(f"  Vacaciones extra:      {self.dias_vacaciones_adicionales} días")
        print(f"  Factor fijo:           {self.factor_integracion_fijo or 'Automático'}")
        print(f"\n  CONFIGURACIÓN:")
        print(f"  Días por mes:          {self.dias_por_mes}")
        print(f"  Aplicar Art 36 LSS:    {'Sí' if self.aplicar_art_36_lss else 'No'}")
        print("="*60)


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
    
    def es_salario_minimo(self, salario_minimo_aplicable: float, tolerancia: float = 0.01) -> bool:
        """Verifica si gana el salario mínimo (con tolerancia de 1%)"""
        return abs(self.salario_diario - salario_minimo_aplicable) / salario_minimo_aplicable <= tolerancia


# =============================================================================
# RESULTADO DE CÁLCULO
# =============================================================================

@dataclass
class ResultadoCuotas:
    """Resultado detallado del cálculo de cuotas"""
    
    # Identificación
    trabajador: str
    empresa: str
    
    # Salarios
    salario_diario: float
    salario_mensual: float
    factor_integracion: float
    sbc_diario: float
    sbc_mensual: float
    dias_cotizados: int
    
    # IMSS Patronal
    imss_cuota_fija: float = 0.0
    imss_excedente_pat: float = 0.0
    imss_prest_dinero_pat: float = 0.0
    imss_gastos_med_pens_pat: float = 0.0
    imss_invalidez_vida_pat: float = 0.0
    imss_guarderias: float = 0.0
    imss_retiro: float = 0.0
    imss_cesantia_vejez_pat: float = 0.0
    imss_riesgo_trabajo: float = 0.0
    
    # IMSS Obrero
    imss_excedente_obr: float = 0.0
    imss_prest_dinero_obr: float = 0.0
    imss_gastos_med_pens_obr: float = 0.0
    imss_invalidez_vida_obr: float = 0.0
    imss_cesantia_vejez_obr: float = 0.0
    
    # Art. 36 LSS
    imss_obrero_absorbido: float = 0.0
    es_salario_minimo: bool = False
    
    # Otros patronales
    infonavit: float = 0.0
    isn: float = 0.0
    
    # Provisiones
    provision_aguinaldo: float = 0.0
    provision_vacaciones: float = 0.0
    provision_prima_vac: float = 0.0
    
    # ISR
    isr_base_gravable: float = 0.0
    isr_antes_subsidio: float = 0.0
    subsidio_empleo: float = 0.0
    isr_a_retener: float = 0.0
    
    @property
    def total_imss_patronal(self) -> float:
        return (self.imss_cuota_fija + self.imss_excedente_pat + 
                self.imss_prest_dinero_pat + self.imss_gastos_med_pens_pat +
                self.imss_invalidez_vida_pat + self.imss_guarderias +
                self.imss_retiro + self.imss_cesantia_vejez_pat +
                self.imss_riesgo_trabajo)
    
    @property
    def total_imss_obrero(self) -> float:
        return (self.imss_excedente_obr + self.imss_prest_dinero_obr +
                self.imss_gastos_med_pens_obr + self.imss_invalidez_vida_obr +
                self.imss_cesantia_vejez_obr)
    
    @property
    def total_descuentos_trabajador(self) -> float:
        return self.total_imss_obrero + self.isr_a_retener
    
    @property
    def salario_neto(self) -> float:
        return self.salario_mensual - self.total_descuentos_trabajador
    
    @property
    def total_provisiones(self) -> float:
        return self.provision_aguinaldo + self.provision_vacaciones + self.provision_prima_vac
    
    @property
    def total_carga_patronal(self) -> float:
        """Todo lo que paga el patrón además del salario"""
        return (self.total_imss_patronal + self.infonavit + self.isn + 
                self.total_provisiones + self.imss_obrero_absorbido)
    
    @property
    def costo_total(self) -> float:
        return self.salario_mensual + self.total_carga_patronal
    
    @property
    def factor_costo(self) -> float:
        return self.costo_total / self.salario_mensual if self.salario_mensual > 0 else 0


# =============================================================================
# CALCULADORA PRINCIPAL
# =============================================================================

class CalculadoraCostoPatronal:
    """Calculadora de costo patronal con configuración por empresa"""
    
    def __init__(self, config: ConfiguracionEmpresa):
        self.config = config
        self.const = ConstantesFiscales
        self.resultados: list[ResultadoCuotas] = []
    
    def calcular_isr(self, base_gravable: float) -> tuple[float, float, float]:
        """
        Calcula ISR mensual.
        Retorna: (isr_antes_subsidio, subsidio, isr_a_retener)
        """
        if base_gravable <= 0:
            return 0.0, 0.0, 0.0
        
        # Buscar rango en tabla
        isr = 0.0
        for lim_inf, lim_sup, cuota_fija, tasa in self.const.TABLA_ISR_MENSUAL:
            if lim_inf <= base_gravable <= lim_sup:
                excedente = base_gravable - lim_inf
                isr = cuota_fija + (excedente * tasa)
                break
        
        # Subsidio al empleo
        subsidio = 0.0
        if base_gravable <= self.const.LIMITE_SUBSIDIO_MENSUAL:
            subsidio = self.const.SUBSIDIO_EMPLEO_MENSUAL
        
        isr_a_retener = max(0, isr - subsidio)
        
        return isr, subsidio, isr_a_retener
    
    def calcular(self, trabajador: Trabajador) -> ResultadoCuotas:
        """Calcula todas las cuotas para un trabajador"""
        
        dias = trabajador.dias_cotizados_mes
        
        # Factor de integración y SBC
        factor_int = self.config.calcular_factor_integracion(trabajador.antiguedad_anos)
        sbc_diario = trabajador.salario_diario * factor_int
        sbc_diario = min(sbc_diario, self.const.TOPE_SBC_DIARIO)  # Aplicar tope
        
        # Bases de cálculo
        uma = self.const.UMA_DIARIO
        tres_uma = self.const.TRES_UMA
        excedente_base = max(0, sbc_diario - tres_uma)
        
        # ─────────────────────────────────────────────────────────────────────
        # IMSS PATRONAL
        # ─────────────────────────────────────────────────────────────────────
        imss_cuota_fija = uma * self.const.IMSS_CUOTA_FIJA * dias
        imss_excedente_pat = excedente_base * self.const.IMSS_EXCEDENTE_PAT * dias
        imss_prest_dinero_pat = sbc_diario * self.const.IMSS_PREST_DINERO_PAT * dias
        imss_gastos_med_pat = sbc_diario * self.const.IMSS_GASTOS_MED_PENS_PAT * dias
        imss_invalidez_pat = sbc_diario * self.const.IMSS_INVALIDEZ_VIDA_PAT * dias
        imss_guarderias = sbc_diario * self.const.IMSS_GUARDERIAS * dias
        imss_retiro = sbc_diario * self.const.IMSS_RETIRO * dias
        imss_cesantia_pat = sbc_diario * self.const.IMSS_CESANTIA_VEJEZ_PAT * dias
        imss_riesgo = sbc_diario * self.config.prima_riesgo * dias
        
        # ─────────────────────────────────────────────────────────────────────
        # IMSS OBRERO - Art. 36 LSS
        # ─────────────────────────────────────────────────────────────────────
        es_sm = trabajador.es_salario_minimo(self.config.salario_minimo_aplicable)
        
        if es_sm and self.config.aplicar_art_36_lss:
            # Art. 36 LSS: Patrón absorbe cuota obrera
            imss_obrero_absorbido = (
                excedente_base * self.const.IMSS_EXCEDENTE_OBR * dias +
                sbc_diario * self.const.IMSS_PREST_DINERO_OBR * dias +
                sbc_diario * self.const.IMSS_GASTOS_MED_PENS_OBR * dias +
                sbc_diario * self.const.IMSS_INVALIDEZ_VIDA_OBR * dias +
                sbc_diario * self.const.IMSS_CESANTIA_VEJEZ_OBR * dias
            )
            imss_excedente_obr = 0.0
            imss_prest_dinero_obr = 0.0
            imss_gastos_med_obr = 0.0
            imss_invalidez_obr = 0.0
            imss_cesantia_obr = 0.0
        else:
            # Cálculo normal: se descuenta al trabajador
            imss_obrero_absorbido = 0.0
            imss_excedente_obr = excedente_base * self.const.IMSS_EXCEDENTE_OBR * dias
            imss_prest_dinero_obr = sbc_diario * self.const.IMSS_PREST_DINERO_OBR * dias
            imss_gastos_med_obr = sbc_diario * self.const.IMSS_GASTOS_MED_PENS_OBR * dias
            imss_invalidez_obr = sbc_diario * self.const.IMSS_INVALIDEZ_VIDA_OBR * dias
            imss_cesantia_obr = sbc_diario * self.const.IMSS_CESANTIA_VEJEZ_OBR * dias
        
        # ─────────────────────────────────────────────────────────────────────
        # INFONAVIT
        # ─────────────────────────────────────────────────────────────────────
        infonavit = sbc_diario * self.const.INFONAVIT_PAT * dias
        
        # ─────────────────────────────────────────────────────────────────────
        # ISN
        # ─────────────────────────────────────────────────────────────────────
        salario_mensual = trabajador.salario_diario * dias
        isn = salario_mensual * self.config.tasa_isn
        
        # ─────────────────────────────────────────────────────────────────────
        # PROVISIONES
        # ─────────────────────────────────────────────────────────────────────
        provision_aguinaldo = (trabajador.salario_diario * self.config.dias_aguinaldo) / 12
        dias_vac = (ConstantesFiscales.dias_vacaciones(trabajador.antiguedad_anos) + 
                    self.config.dias_vacaciones_adicionales)
        provision_vacaciones = (trabajador.salario_diario * dias_vac) / 12
        provision_prima_vac = provision_vacaciones * self.config.prima_vacacional
        
        # ─────────────────────────────────────────────────────────────────────
        # ISR
        # ─────────────────────────────────────────────────────────────────────
        if es_sm:
            # Art. 96 LISR: Exento de retención
            isr_antes, subsidio, isr_a_retener = 0.0, 0.0, 0.0
        else:
            isr_antes, subsidio, isr_a_retener = self.calcular_isr(salario_mensual)
        
        # ─────────────────────────────────────────────────────────────────────
        # RESULTADO
        # ─────────────────────────────────────────────────────────────────────
        return ResultadoCuotas(
            trabajador=trabajador.nombre,
            empresa=self.config.nombre,
            salario_diario=trabajador.salario_diario,
            salario_mensual=salario_mensual,
            factor_integracion=factor_int,
            sbc_diario=sbc_diario,
            sbc_mensual=sbc_diario * dias,
            dias_cotizados=dias,
            
            imss_cuota_fija=imss_cuota_fija,
            imss_excedente_pat=imss_excedente_pat,
            imss_prest_dinero_pat=imss_prest_dinero_pat,
            imss_gastos_med_pens_pat=imss_gastos_med_pat,
            imss_invalidez_vida_pat=imss_invalidez_pat,
            imss_guarderias=imss_guarderias,
            imss_retiro=imss_retiro,
            imss_cesantia_vejez_pat=imss_cesantia_pat,
            imss_riesgo_trabajo=imss_riesgo,
            
            imss_excedente_obr=imss_excedente_obr,
            imss_prest_dinero_obr=imss_prest_dinero_obr,
            imss_gastos_med_pens_obr=imss_gastos_med_obr,
            imss_invalidez_vida_obr=imss_invalidez_obr,
            imss_cesantia_vejez_obr=imss_cesantia_obr,
            
            imss_obrero_absorbido=imss_obrero_absorbido,
            es_salario_minimo=es_sm,
            
            infonavit=infonavit,
            isn=isn,
            
            provision_aguinaldo=provision_aguinaldo,
            provision_vacaciones=provision_vacaciones,
            provision_prima_vac=provision_prima_vac,
            
            isr_base_gravable=salario_mensual,
            isr_antes_subsidio=isr_antes,
            subsidio_empleo=subsidio,
            isr_a_retener=isr_a_retener,
        )
    
    def calcular_y_guardar(self, trabajador: Trabajador) -> ResultadoCuotas:
        resultado = self.calcular(trabajador)
        self.resultados.append(resultado)
        return resultado

    def calcular_desde_neto(self, salario_neto_deseado: float,
                            trabajador: Trabajador) -> tuple[ResultadoCuotas, int]:
        """
        Calcula el salario bruto necesario para alcanzar un neto deseado.
        Usa método iterativo (bisección) para encontrar el salario correcto.

        Retorna: (resultado, iteraciones)
        """
        # Límites de búsqueda
        salario_min = salario_neto_deseado / trabajador.dias_cotizados_mes  # Estimación baja
        salario_max = salario_neto_deseado * 2 / trabajador.dias_cotizados_mes  # Estimación alta

        max_iteraciones = 50
        tolerancia = 1.0  # $1 de tolerancia

        for i in range(max_iteraciones):
            # Probar con el punto medio
            salario_medio = (salario_min + salario_max) / 2

            # Crear trabajador temporal con este salario
            trabajador_temp = Trabajador(
                nombre=trabajador.nombre,
                salario_diario=salario_medio,
                antiguedad_anos=trabajador.antiguedad_anos,
                dias_cotizados_mes=trabajador.dias_cotizados_mes,
                zona_frontera=trabajador.zona_frontera,
            )

            # Calcular
            resultado = self.calcular(trabajador_temp)

            # Verificar si llegamos al neto deseado
            diferencia = resultado.salario_neto - salario_neto_deseado

            if abs(diferencia) <= tolerancia:
                return resultado, i + 1

            # Ajustar límites según el resultado
            if diferencia < 0:
                # El neto es menor, necesitamos salario bruto más alto
                salario_min = salario_medio
            else:
                # El neto es mayor, necesitamos salario bruto más bajo
                salario_max = salario_medio

        # Si no converge, retornar el mejor resultado
        return resultado, max_iteraciones

    def limpiar_resultados(self):
        """Limpia la lista de resultados guardados"""
        self.resultados.clear()

    def exportar_excel(self, nombre_archivo: str = "costo_patronal_2026.xlsx") -> str:
        """
        Exporta los resultados a Excel.
        Requiere la biblioteca openpyxl: pip install openpyxl

        Retorna: ruta del archivo creado
        """
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            from openpyxl.utils import get_column_letter
        except ImportError:
            raise ImportError(
                "Para exportar a Excel necesitas instalar openpyxl:\n"
                "pip install openpyxl"
            )

        if not self.resultados:
            raise ValueError("No hay resultados para exportar")

        # Crear libro
        wb = openpyxl.Workbook()

        # Hoja 1: Resumen
        ws_resumen = wb.active
        ws_resumen.title = "Resumen"

        # Encabezados
        encabezados = [
            "Trabajador", "Salario Diario", "Salario Mensual", "SBC Diario",
            "IMSS Patronal", "IMSS Obrero", "INFONAVIT", "ISN",
            "Provisiones", "ISR", "Salario Neto", "Costo Total", "Factor Costo"
        ]

        for col, encabezado in enumerate(encabezados, 1):
            celda = ws_resumen.cell(1, col, encabezado)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            celda.alignment = Alignment(horizontal="center")

        # Datos
        for fila, r in enumerate(self.resultados, 2):
            ws_resumen.cell(fila, 1, r.trabajador)
            ws_resumen.cell(fila, 2, r.salario_diario)
            ws_resumen.cell(fila, 3, r.salario_mensual)
            ws_resumen.cell(fila, 4, r.sbc_diario)
            ws_resumen.cell(fila, 5, r.total_imss_patronal)
            ws_resumen.cell(fila, 6, r.total_imss_obrero)
            ws_resumen.cell(fila, 7, r.infonavit)
            ws_resumen.cell(fila, 8, r.isn)
            ws_resumen.cell(fila, 9, r.total_provisiones)
            ws_resumen.cell(fila, 10, r.isr_a_retener)
            ws_resumen.cell(fila, 11, r.salario_neto)
            ws_resumen.cell(fila, 12, r.costo_total)
            ws_resumen.cell(fila, 13, r.factor_costo)

        # Formatear columnas numéricas como moneda
        for fila in range(2, len(self.resultados) + 2):
            for col in range(2, 13):
                ws_resumen.cell(fila, col).number_format = '$#,##0.00'
            ws_resumen.cell(fila, 13).number_format = '0.0000'

        # Ajustar anchos
        for col in range(1, len(encabezados) + 1):
            ws_resumen.column_dimensions[get_column_letter(col)].width = 15

        # Hoja 2: Constantes
        ws_const = wb.create_sheet("Constantes 2026")
        ws_const['A1'] = "CONSTANTES FISCALES 2026"
        ws_const['A1'].font = Font(bold=True, size=14)

        fila = 3
        constantes_info = [
            ("SALARIOS MÍNIMOS", ""),
            ("  General", f"${self.const.SALARIO_MINIMO_GENERAL:.2f}/día"),
            ("  Frontera", f"${self.const.SALARIO_MINIMO_FRONTERA:.2f}/día"),
            ("", ""),
            ("UMA", ""),
            ("  Diario", f"${self.const.UMA_DIARIO:.2f}"),
            ("  Mensual", f"${self.const.UMA_MENSUAL:.2f}"),
            ("  Tope SBC", f"${self.const.TOPE_SBC_DIARIO:.2f}"),
            ("", ""),
            ("IMSS - TASAS", ""),
            ("  Cesantía y Vejez Patronal", f"{self.const.IMSS_CESANTIA_VEJEZ_PAT:.3%}"),
            ("  Cesantía y Vejez Obrero", f"{self.const.IMSS_CESANTIA_VEJEZ_OBR:.3%}"),
            ("  Retiro", f"{self.const.IMSS_RETIRO:.2%}"),
            ("  INFONAVIT", f"{self.const.INFONAVIT_PAT:.2%}"),
            ("", ""),
            ("SUBSIDIO AL EMPLEO", ""),
            ("  Mensual", f"${self.const.SUBSIDIO_EMPLEO_MENSUAL:.2f}"),
            ("  Límite", f"${self.const.LIMITE_SUBSIDIO_MENSUAL:.2f}"),
        ]

        for concepto, valor in constantes_info:
            ws_const.cell(fila, 1, concepto)
            ws_const.cell(fila, 2, valor)
            if concepto and not concepto.startswith("  "):
                ws_const.cell(fila, 1).font = Font(bold=True)
            fila += 1

        ws_const.column_dimensions['A'].width = 30
        ws_const.column_dimensions['B'].width = 20

        # Guardar archivo
        wb.save(nombre_archivo)
        return nombre_archivo


# =============================================================================
# FUNCIONES DE IMPRESIÓN
# =============================================================================

def imprimir_resultado(r: ResultadoCuotas):
    """Imprime resultado de forma legible"""
    
    print("\n" + "="*65)
    print(f"COSTO PATRONAL: {r.trabajador}")
    print(f"Empresa: {r.empresa}")
    print("="*65)
    
    if r.es_salario_minimo:
        print("\n   ⚠️  SALARIO MÍNIMO:")
        print("       • Exento de retención ISR (Art. 96 LISR)")
        print("       • Cuota obrera IMSS la paga el patrón (Art. 36 LSS)")
    
    print(f"\n📋 SALARIO")
    print(f"   Salario diario:            ${r.salario_diario:>12,.2f}")
    print(f"   Días cotizados:            {r.dias_cotizados:>12}")
    print(f"   Salario mensual:           ${r.salario_mensual:>12,.2f}")
    
    print(f"\n📊 INTEGRACIÓN")
    print(f"   Factor de integración:     {r.factor_integracion:>13.4f}")
    print(f"   SBC diario:                ${r.sbc_diario:>12,.2f}")
    print(f"   SBC mensual:               ${r.sbc_mensual:>12,.2f}")
    
    print(f"\n🏥 IMSS PATRONAL")
    print(f"   Cuota fija (E.M.):         ${r.imss_cuota_fija:>12,.2f}")
    print(f"   Excedente (E.M.):          ${r.imss_excedente_pat:>12,.2f}")
    print(f"   Prest. en dinero (E.M.):   ${r.imss_prest_dinero_pat:>12,.2f}")
    print(f"   Gastos méd. pensionados:   ${r.imss_gastos_med_pens_pat:>12,.2f}")
    print(f"   Invalidez y vida:          ${r.imss_invalidez_vida_pat:>12,.2f}")
    print(f"   Guarderías:                ${r.imss_guarderias:>12,.2f}")
    print(f"   Retiro:                    ${r.imss_retiro:>12,.2f}")
    print(f"   Cesantía y vejez (3.513%): ${r.imss_cesantia_vejez_pat:>12,.2f}")
    print(f"   Riesgo de trabajo:         ${r.imss_riesgo_trabajo:>12,.2f}")
    print(f"   ─────────────────────────────────────────────")
    print(f"   TOTAL IMSS PATRONAL:       ${r.total_imss_patronal:>12,.2f}")
    
    if r.imss_obrero_absorbido > 0:
        print(f"\n⚖️  ART. 36 LSS - CUOTA OBRERA (patrón paga)")
        print(f"   IMSS obrero absorbido:     ${r.imss_obrero_absorbido:>12,.2f}")
    
    print(f"\n🏠 INFONAVIT (5%)")
    print(f"   Aportación patronal:       ${r.infonavit:>12,.2f}")
    
    print(f"\n💰 ISN")
    print(f"   Impuesto sobre nómina:     ${r.isn:>12,.2f}")
    
    print(f"\n📅 PROVISIONES MENSUALES")
    print(f"   Aguinaldo:                 ${r.provision_aguinaldo:>12,.2f}")
    print(f"   Vacaciones:                ${r.provision_vacaciones:>12,.2f}")
    print(f"   Prima vacacional:          ${r.provision_prima_vac:>12,.2f}")
    print(f"   ─────────────────────────────────────────────")
    print(f"   TOTAL PROVISIONES:         ${r.total_provisiones:>12,.2f}")
    
    print(f"\n👷 DESCUENTOS AL TRABAJADOR")
    if r.es_salario_minimo:
        print(f"   IMSS Obrero:               $        0.00  (Art. 36 LSS)")
        print(f"   ISR:                       $        0.00  (Art. 96 LISR)")
    else:
        print(f"   IMSS Obrero:               ${r.total_imss_obrero:>12,.2f}")
        print(f"   ISR a retener:             ${r.isr_a_retener:>12,.2f}")
    print(f"   ─────────────────────────────────────────────")
    print(f"   TOTAL DESCUENTOS:          ${r.total_descuentos_trabajador:>12,.2f}")
    
    print(f"\n" + "="*65)
    print(f"💵 COSTO TOTAL PATRONAL:      ${r.costo_total:>12,.2f}")
    print(f"📈 FACTOR DE COSTO:           {r.factor_costo:>13.4f}")
    print(f"   (El trabajador cuesta {r.factor_costo:.2%} de su salario nominal)")
    print("="*65)
    print(f"💰 SALARIO NETO TRABAJADOR:   ${r.salario_neto:>12,.2f}")
    print("="*65)


# =============================================================================
# CONFIGURACIONES PREDEFINIDAS
# =============================================================================

def crear_configuracion_mantiser() -> ConfiguracionEmpresa:
    """Configuración de Mantiser basada en EMA real"""
    return ConfiguracionEmpresa(
        nombre="Mantiser",
        registro_patronal="Y46-55423-10-3",
        estado="puebla",
        prima_riesgo=0.0259840,  # 2.5984%
        factor_integracion_fijo=1.0493,  # Del EMA real
        dias_aguinaldo=15,
        prima_vacacional=0.25,
        dias_vacaciones_adicionales=0,
        dias_por_mes=30,
        zona_frontera=False,
        aplicar_art_36_lss=True,
    )


def crear_configuracion_pletorica() -> ConfiguracionEmpresa:
    """Configuración de Pletórica (ajustar según datos reales)"""
    return ConfiguracionEmpresa(
        nombre="Pletórica",
        registro_patronal="XXXXXX",  # Completar
        estado="puebla",
        prima_riesgo=0.005,  # Prima mínima clase I (ajustar según real)
        factor_integracion_fijo=None,  # Calcular automáticamente
        dias_aguinaldo=15,
        prima_vacacional=0.25,
        dias_vacaciones_adicionales=0,
        dias_por_mes=30,
        zona_frontera=False,
        aplicar_art_36_lss=True,
    )


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONFIGURAR EMPRESA
    # ─────────────────────────────────────────────────────────────────────────
    
    mantiser = crear_configuracion_mantiser()
    mantiser.mostrar_configuracion()
    
    # ─────────────────────────────────────────────────────────────────────────
    # CREAR CALCULADORA
    # ─────────────────────────────────────────────────────────────────────────
    
    calc = CalculadoraCostoPatronal(mantiser)
    
    # ─────────────────────────────────────────────────────────────────────────
    # CALCULAR TRABAJADOR SM
    # ─────────────────────────────────────────────────────────────────────────
    
    trabajador_sm = Trabajador(
        nombre="Trabajador SM 2026 (1 año)",
        salario_diario=ConstantesFiscales.SALARIO_MINIMO_GENERAL,
        antiguedad_anos=1,
        dias_cotizados_mes=30,
    )
    
    resultado = calc.calcular(trabajador_sm)
    imprimir_resultado(resultado)
    
    # ─────────────────────────────────────────────────────────────────────────
    # COMPARACIÓN CON CIFRAS DEL CONTADOR
    # ─────────────────────────────────────────────────────────────────────────
    
    print("\n" + "="*65)
    print("COMPARACIÓN CON CIFRAS DEL CONTADOR (2026)")
    print("="*65)
    
    # Cifras del contador (por día, usando 30.4 días)
    cont_imss = 53.68
    cont_rcv = 27.87
    cont_infonavit = 16.53
    cont_total = 98.08
    
    # Mis cifras (por día)
    dias = resultado.dias_cotizados
    mi_imss_dia = (resultado.total_imss_patronal - resultado.imss_retiro -
                   resultado.imss_cesantia_vejez_pat) / dias
    mi_rcv_dia = (resultado.imss_retiro + resultado.imss_cesantia_vejez_pat) / dias
    mi_infonavit_dia = resultado.infonavit / dias
    mi_obrero_dia = resultado.imss_obrero_absorbido / dias
    
    print(f"\n{'Concepto':<25} {'Contador':>12} {'Mi cálculo':>12}")
    print("─"*50)
    print(f"{'IMSS (sin RCV)':<25} ${cont_imss:>10,.2f} ${mi_imss_dia + mi_obrero_dia:>10,.2f}")
    print(f"{'RCV':<25} ${cont_rcv:>10,.2f} ${mi_rcv_dia:>10,.2f}")
    print(f"{'INFONAVIT':<25} ${cont_infonavit:>10,.2f} ${mi_infonavit_dia:>10,.2f}")
    print("─"*50)
    
    mi_total_dia = mi_imss_dia + mi_obrero_dia + mi_rcv_dia + mi_infonavit_dia
    print(f"{'TOTAL/día':<25} ${cont_total:>10,.2f} ${mi_total_dia:>10,.2f}")
    print(f"{'TOTAL/mes (×30.4)':<25} ${cont_total * 30.4:>10,.2f} ${mi_total_dia * 30.4:>10,.2f}")