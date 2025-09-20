"""
Cálculos de ISR según LISR y tablas SAT 2024
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional

class CalculadoraISR:
    """Calculadora de ISR para sueldos y salarios"""
    
    # Tabla ISR Quincenal 2024 (Art. 96 LISR)
    TABLA_ISR_QUINCENAL = [
        {'limite_inferior': Decimal('0.01'), 'limite_superior': Decimal('368.10'), 'cuota_fija': Decimal('0.00'), 'pct': Decimal('1.92')},
        {'limite_inferior': Decimal('368.11'), 'limite_superior': Decimal('3124.35'), 'cuota_fija': Decimal('7.05'), 'pct': Decimal('6.40')},
        {'limite_inferior': Decimal('3124.36'), 'limite_superior': Decimal('5490.75'), 'cuota_fija': Decimal('183.45'), 'pct': Decimal('10.88')},
        {'limite_inferior': Decimal('5490.76'), 'limite_superior': Decimal('6382.80'), 'cuota_fija': Decimal('440.85'), 'pct': Decimal('16.00')},
        {'limite_inferior': Decimal('6382.81'), 'limite_superior': Decimal('7641.90'), 'cuota_fija': Decimal('583.65'), 'pct': Decimal('17.92')},
        {'limite_inferior': Decimal('7641.91'), 'limite_superior': Decimal('15375.90'), 'cuota_fija': Decimal('809.25'), 'pct': Decimal('21.36')},
        {'limite_inferior': Decimal('15375.91'), 'limite_superior': Decimal('20524.20'), 'cuota_fija': Decimal('2459.25'), 'pct': Decimal('23.52')},
        {'limite_inferior': Decimal('20524.21'), 'limite_superior': Decimal('32960.25'), 'cuota_fija': Decimal('3669.15'), 'pct': Decimal('30.00')},
        {'limite_inferior': Decimal('32960.26'), 'limite_superior': Decimal('61834.05'), 'cuota_fija': Decimal('7399.95'), 'pct': Decimal('32.00')},
        {'limite_inferior': Decimal('61834.06'), 'limite_superior': Decimal('185502.30'), 'cuota_fija': Decimal('16639.65'), 'pct': Decimal('34.00')},
        {'limite_inferior': Decimal('185502.31'), 'limite_superior': None, 'cuota_fija': Decimal('58661.70'), 'pct': Decimal('35.00')}
    ]
    
    # Tabla de subsidio al empleo quincenal 2024
    TABLA_SUBSIDIO_QUINCENAL = [
        {'desde': Decimal('0.01'), 'hasta': Decimal('969.50'), 'subsidio': Decimal('217.80')},
        {'desde': Decimal('969.51'), 'hasta': Decimal('1420.80'), 'subsidio': Decimal('217.80')},
        {'desde': Decimal('1420.81'), 'hasta': Decimal('1421.00'), 'subsidio': Decimal('217.80')},
        {'desde': Decimal('1421.01'), 'hasta': Decimal('1500.00'), 'subsidio': Decimal('211.20')},
        {'desde': Decimal('1500.01'), 'hasta': Decimal('2000.00'), 'subsidio': Decimal('204.30')},
        {'desde': Decimal('2000.01'), 'hasta': Decimal('2500.00'), 'subsidio': Decimal('192.90')},
        {'desde': Decimal('2500.01'), 'hasta': Decimal('3000.00'), 'subsidio': Decimal('178.20')},
        {'desde': Decimal('3000.01'), 'hasta': Decimal('3500.00'), 'subsidio': Decimal('163.80')},
        {'desde': Decimal('3500.01'), 'hasta': Decimal('3982.61'), 'subsidio': Decimal('146.70')},
        {'desde': Decimal('3982.62'), 'hasta': None, 'subsidio': Decimal('0.00')}
    ]
    
    @classmethod
    def calcular_isr_quincenal(
        cls,
        base_gravable: Decimal,
        incluir_subsidio: bool = True
    ) -> Dict[str, Decimal]:
        """
        Calcula el ISR quincenal según tablas SAT
        
        Args:
            base_gravable: Base gravable quincenal
            incluir_subsidio: Si se aplica subsidio al empleo
            
        Returns:
            Dict con ISR, subsidio y retención final
        """
        
        # Buscar en tabla ISR
        isr_calculado = Decimal('0')
        for rango in cls.TABLA_ISR_QUINCENAL:
            if base_gravable >= rango['limite_inferior']:
                if rango['limite_superior'] is None or base_gravable <= rango['limite_superior']:
                    # Aplicar fórmula: (Base - Límite Inferior) * % + Cuota Fija
                    excedente = base_gravable - rango['limite_inferior']
                    isr_marginal = (excedente * rango['pct']) / 100
                    isr_calculado = isr_marginal + rango['cuota_fija']
                    break
        
        # Calcular subsidio si aplica
        subsidio = Decimal('0')
        if incluir_subsidio:
            for rango in cls.TABLA_SUBSIDIO_QUINCENAL:
                if base_gravable >= rango['desde']:
                    if rango['hasta'] is None or base_gravable <= rango['hasta']:
                        subsidio = rango['subsidio']
                        break
        
        # ISR a retener
        isr_neto = max(isr_calculado - subsidio, Decimal('0'))
        
        return {
            'base_gravable': base_gravable.quantize(Decimal('0.01')),
            'isr_calculado': isr_calculado.quantize(Decimal('0.01')),
            'subsidio_empleo': subsidio.quantize(Decimal('0.01')),
            'isr_retener': isr_neto.quantize(Decimal('0.01'))
        }
    
    @classmethod
    def calcular_base_gravable(
        cls,
        percepciones: Dict[str, Decimal],
        deducciones_autorizadas: Optional[Dict[str, Decimal]] = None
    ) -> Decimal:
        """
        Calcula la base gravable para ISR
        
        Args:
            percepciones: Dict con todas las percepciones
            deducciones_autorizadas: Deducciones autorizadas por ley
            
        Returns:
            Base gravable para ISR
        """
        
        # Percepciones gravables (Art. 93 LISR - exenciones)
        conceptos_exentos = [
            'prima_vacacional_exenta',
            'aguinaldo_exento',
            'ptu_exenta',
            'horas_extra_exentas',
            'prima_dominical_exenta'
        ]
        
        total_gravable = Decimal('0')
        for concepto, monto in percepciones.items():
            if concepto not in conceptos_exentos:
                total_gravable += monto
        
        # Restar deducciones autorizadas si existen
        if deducciones_autorizadas:
            for deduccion in deducciones_autorizadas.values():
                total_gravable -= deduccion
        
        return max(total_gravable, Decimal('0'))