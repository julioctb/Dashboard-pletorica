"""
Constantes fiscales y de negocio para México 2026
Actualizado: Diciembre 2025
"""

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
    # TABLA ISR MENSUAL 2026 (Art. 96 LISR) — Anexo 8 RMF 2026 (DOF 28/12/2025)
    # ─────────────────────────────────────────────────────────────────────────
    TABLA_ISR_MENSUAL = [
        # (límite_inferior, límite_superior, cuota_fija, tasa_excedente)
        (0.01, 844.59, 0.00, 0.0192),
        (844.60, 7168.51, 16.22, 0.0640),
        (7168.52, 12598.02, 420.95, 0.1088),
        (12598.03, 14644.64, 1011.68, 0.1600),
        (14644.65, 17533.64, 1339.14, 0.1792),
        (17533.65, 35362.83, 1856.84, 0.2136),
        (35362.84, 55736.68, 5665.16, 0.2352),
        (55736.69, 106410.50, 10457.09, 0.3000),
        (106410.51, 141880.66, 25659.23, 0.3200),
        (141880.67, 425641.99, 37009.69, 0.3400),
        (425642.00, float('inf'), 133488.54, 0.3500),
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