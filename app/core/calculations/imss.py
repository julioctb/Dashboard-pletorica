# app/core/calculations/imss.py
"""
Cálculos de IMSS según Ley del Seguro Social 2024
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import Dict, Tuple

class CalculadoraIMSS:
    """Calculadora de cuotas IMSS patronales y obreras"""
    
    # UMA 2024 (actualizar anualmente)
    UMA_DIARIO = Decimal('108.57')
    UMA_MENSUAL = UMA_DIARIO * 30
    
    # Topes de cotización
    TOPE_SDI = UMA_DIARIO * 25  # 25 UMAs
    
    # Porcentajes de cuotas (Art. 106 y otros LSS)
    CUOTAS = {
        'enfermedad_maternidad': {
            'especie': {
                'patron': Decimal('20.40'),  # % del SBC
                'trabajador': Decimal('0.00')
            },
            'dinero': {
                'patron': Decimal('0.70'),  # % del SBC
                'trabajador': Decimal('0.25')
            },
            'gastos_medicos': {
                'patron': Decimal('1.05'),  # % del SBC
                'trabajador': Decimal('0.375')
            }
        },
        'invalidez_vida': {
            'patron': Decimal('1.75'),
            'trabajador': Decimal('0.625')
        },
        'retiro': {
            'patron': Decimal('2.00'),
            'trabajador': Decimal('0.00')
        },
        'cesantia_vejez': {
            'patron': Decimal('3.150'),
            'trabajador': Decimal('1.125')
        },
        'guarderia': {
            'patron': Decimal('1.00'),
            'trabajador': Decimal('0.00')
        },
        'riesgo_trabajo': {
            # Prima media, ajustar según empresa
            'patron': Decimal('0.54355'),  
            'trabajador': Decimal('0.00')
        }
    }
    
    @classmethod
    def calcular_cuotas(
        cls,
        salario_diario_integrado: Decimal,
        dias_cotizados: int = 15,
        uma_excedente: bool = True
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Calcula las cuotas IMSS patronales y del trabajador
        
        Args:
            salario_diario_integrado: SDI del trabajador
            dias_cotizados: Días a cotizar en el período
            uma_excedente: Si aplica excedente de 3 UMAs
            
        Returns:
            Diccionario con cuotas patronales y del trabajador
        """
        
        # Validar tope de cotización
        sdi = min(salario_diario_integrado, cls.TOPE_SDI)
        sbc = sdi * dias_cotizados  # Salario Base de Cotización
        
        cuotas = {
            'patron': {},
            'trabajador': {},
            'totales': {}
        }
        
        # 1. Enfermedad y Maternidad - Prestaciones en especie
        # Cuota fija patronal sobre UMA
        cuota_fija_patron = cls.UMA_DIARIO * dias_cotizados * cls.CUOTAS['enfermedad_maternidad']['especie']['patron'] / 100
        
        # Excedente de 3 UMAs (si aplica)
        excedente = Decimal('0')
        if uma_excedente and sdi > (cls.UMA_DIARIO * 3):
            excedente_diario = sdi - (cls.UMA_DIARIO * 3)
            excedente = excedente_diario * dias_cotizados * Decimal('1.10') / 100  # 1.1% patron
            excedente_trabajador = excedente_diario * dias_cotizados * Decimal('0.40') / 100  # 0.4% trabajador
        else:
            excedente_trabajador = Decimal('0')
        
        cuotas['patron']['enf_mat_especie'] = cuota_fija_patron + excedente
        cuotas['trabajador']['enf_mat_especie'] = excedente_trabajador
        
        # 2. Enfermedad y Maternidad - Prestaciones en dinero
        cuotas['patron']['enf_mat_dinero'] = sbc * cls.CUOTAS['enfermedad_maternidad']['dinero']['patron'] / 100
        cuotas['trabajador']['enf_mat_dinero'] = sbc * cls.CUOTAS['enfermedad_maternidad']['dinero']['trabajador'] / 100
        
        # 3. Enfermedad y Maternidad - Gastos médicos pensionados
        cuotas['patron']['gastos_medicos'] = sbc * cls.CUOTAS['enfermedad_maternidad']['gastos_medicos']['patron'] / 100
        cuotas['trabajador']['gastos_medicos'] = sbc * cls.CUOTAS['enfermedad_maternidad']['gastos_medicos']['trabajador'] / 100
        
        # 4. Invalidez y Vida
        cuotas['patron']['invalidez_vida'] = sbc * cls.CUOTAS['invalidez_vida']['patron'] / 100
        cuotas['trabajador']['invalidez_vida'] = sbc * cls.CUOTAS['invalidez_vida']['trabajador'] / 100
        
        # 5. Retiro (solo patrón)
        cuotas['patron']['retiro'] = sbc * cls.CUOTAS['retiro']['patron'] / 100
        cuotas['trabajador']['retiro'] = Decimal('0')
        
        # 6. Cesantía y Vejez
        cuotas['patron']['cesantia_vejez'] = sbc * cls.CUOTAS['cesantia_vejez']['patron'] / 100
        cuotas['trabajador']['cesantia_vejez'] = sbc * cls.CUOTAS['cesantia_vejez']['trabajador'] / 100
        
        # 7. Guarderías (solo patrón)
        cuotas['patron']['guarderia'] = sbc * cls.CUOTAS['guarderia']['patron'] / 100
        cuotas['trabajador']['guarderia'] = Decimal('0')
        
        # 8. Riesgo de trabajo (solo patrón)
        cuotas['patron']['riesgo_trabajo'] = sbc * cls.CUOTAS['riesgo_trabajo']['patron'] / 100
        cuotas['trabajador']['riesgo_trabajo'] = Decimal('0')
        
        # Redondear todas las cuotas a 2 decimales
        for tipo in ['patron', 'trabajador']:
            for concepto in cuotas[tipo]:
                cuotas[tipo][concepto] = cuotas[tipo][concepto].quantize(
                    Decimal('0.01'), 
                    rounding=ROUND_HALF_UP
                )
        
        # Calcular totales
        cuotas['totales']['patron'] = sum(cuotas['patron'].values())
        cuotas['totales']['trabajador'] = sum(cuotas['trabajador'].values())
        cuotas['totales']['total'] = cuotas['totales']['patron'] + cuotas['totales']['trabajador']
        
        # Información adicional
        cuotas['info'] = {
            'sdi': sdi,
            'sbc': sbc,
            'dias_cotizados': dias_cotizados,
            'uma_diario': cls.UMA_DIARIO,
            'tope_aplicado': sdi != salario_diario_integrado
        }
        
        return cuotas
    
    @classmethod
    def calcular_sdi(
        cls,
        salario_diario: Decimal,
        aguinaldo_dias: int = 15,
        vacaciones_dias: int = 12,
        prima_vacacional_pct: Decimal = Decimal('25'),
        otras_prestaciones: Decimal = Decimal('0')
    ) -> Decimal:
        """
        Calcula el Salario Diario Integrado (SDI)
        Art. 27 LSS
        
        Args:
            salario_diario: Salario diario base
            aguinaldo_dias: Días de aguinaldo al año
            vacaciones_dias: Días de vacaciones al año
            prima_vacacional_pct: Porcentaje de prima vacacional
            otras_prestaciones: Otras prestaciones anuales
            
        Returns:
            SDI calculado
        """
        
        # Factor de integración
        dias_ano = Decimal('365')
        
        # Aguinaldo
        factor_aguinaldo = Decimal(aguinaldo_dias) / dias_ano
        
        # Prima vacacional
        prima_vacacional_dias = (Decimal(vacaciones_dias) * prima_vacacional_pct) / 100
        factor_prima_vac = prima_vacacional_dias / dias_ano
        
        # Otras prestaciones (vales, bonos, etc.)
        factor_otras = otras_prestaciones / dias_ano / salario_diario
        
        # Factor de integración total
        factor_integracion = Decimal('1') + factor_aguinaldo + factor_prima_vac + factor_otras
        
        # SDI
        sdi = salario_diario * factor_integracion
        
        # Aplicar tope
        sdi_final = min(sdi, cls.TOPE_SDI)
        
        return sdi_final.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


