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


# app/core/calculations/isr.py
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


# app/core/calculations/payroll.py
"""
Motor principal de cálculo de nómina
"""
from decimal import Decimal
from datetime import date, datetime
from typing import Dict, List, Optional
from .imss import CalculadoraIMSS
from .isr import CalculadoraISR

class MotorNomina:
    """Motor de cálculo de nómina integrado"""
    
    # UMA 2024
    UMA_DIARIO = Decimal('108.57')
    SALARIO_MINIMO = Decimal('248.93')  # Zona general 2024
    
    def __init__(self):
        self.calculadora_imss = CalculadoraIMSS()
        self.calculadora_isr = CalculadoraISR()
    
    def procesar_nomina_empleado(
        self,
        empleado_data: Dict,
        periodo_data: Dict,
        asistencias: List[Dict],
        incidencias: List[Dict],
        prestamos: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Procesa la nómina completa de un empleado
        
        Args:
            empleado_data: Datos del empleado
            periodo_data: Datos del período de nómina
            asistencias: Lista de asistencias del período
            incidencias: Lista de incidencias del período
            prestamos: Lista de préstamos activos
            
        Returns:
            Dict con todo el cálculo de nómina
        """
        
        # Inicializar resultado
        resultado = {
            'empleado_id': empleado_data['id'],
            'periodo_id': periodo_data['id'],
            'percepciones': {},
            'deducciones': {},
            'totales': {},
            'detalles': {}
        }
        
        # 1. Calcular días trabajados y faltas
        dias_periodo = 15  # Quincenal
        dias_trabajados, dias_faltas = self._calcular_dias_trabajados(
            asistencias, incidencias, dias_periodo
        )
        
        resultado['detalles']['dias_trabajados'] = dias_trabajados
        resultado['detalles']['dias_faltas'] = dias_faltas
        
        # 2. Calcular percepciones
        salario_diario = Decimal(str(empleado_data['salario_diario']))
        
        # Sueldo base
        sueldo_base = salario_diario * dias_trabajados
        resultado['percepciones']['sueldo'] = sueldo_base
        
        # Tiempo extra
        horas_extra = self._calcular_horas_extra(asistencias)
        if horas_extra['dobles'] > 0:
            resultado['percepciones']['tiempo_extra_doble'] = (
                salario_diario / 8 * 2 * Decimal(str(horas_extra['dobles']))
            )
        if horas_extra['triples'] > 0:
            resultado['percepciones']['tiempo_extra_triple'] = (
                salario_diario / 8 * 3 * Decimal(str(horas_extra['triples']))
            )
        
        # Prima dominical (si trabajó domingo)
        domingos_trabajados = self._contar_domingos_trabajados(asistencias)
        if domingos_trabajados > 0:
            prima_dominical = salario_diario * Decimal('0.25') * domingos_trabajados
            resultado['percepciones']['prima_dominical'] = prima_dominical
        
        # Bonos y comisiones (si aplica)
        if empleado_data.get('bono_productividad'):
            resultado['percepciones']['bono_productividad'] = Decimal(str(empleado_data['bono_productividad']))
        
        # Total percepciones
        total_percepciones = sum(resultado['percepciones'].values())
        resultado['totales']['percepciones'] = total_percepciones
        
        # 3. Calcular deducciones
        
        # IMSS
        sdi = Decimal(str(empleado_data['salario_diario_integrado']))
        cuotas_imss = self.calculadora_imss.calcular_cuotas(sdi, dias_trabajados)
        resultado['deducciones']['imss'] = cuotas_imss['totales']['trabajador']
        
        # ISR
        base_gravable_isr = self._calcular_base_gravable_isr(resultado['percepciones'])
        isr_data = self.calculadora_isr.calcular_isr_quincenal(base_gravable_isr)
        resultado['deducciones']['isr'] = isr_data['isr_retener']
        
        # Préstamos
        if prestamos:
            total_prestamos = Decimal('0')
            for prestamo in prestamos:
                if prestamo['estatus'] == 'ACTIVO':
                    total_prestamos += Decimal(str(prestamo['monto_quincenal']))
            if total_prestamos > 0:
                resultado['deducciones']['prestamo'] = total_prestamos
        
        # Infonavit (si tiene)
        if empleado_data.get('credito_infonavit'):
            credito = empleado_data['credito_infonavit']
            if credito['tipo'] == 'VSM':
                # Veces salario mínimo
                descuento = self.SALARIO_MINIMO * Decimal(str(credito['factor'])) * dias_trabajados / 30
            elif credito['tipo'] == 'PORCENTAJE':
                descuento = total_percepciones * Decimal(str(credito['porcentaje'])) / 100
            else:  # CUOTA_FIJA
                descuento = Decimal(str(credito['cuota_fija']))
            resultado['deducciones']['infonavit'] = descuento
        
        # Pensión alimenticia (si tiene)
        if empleado_data.get('pension_alimenticia'):
            pension = empleado_data['pension_alimenticia']
            if pension['tipo'] == 'PORCENTAJE':
                monto_pension = total_percepciones * Decimal(str(pension['porcentaje'])) / 100
            else:
                monto_pension = Decimal(str(pension['monto_fijo']))
            resultado['deducciones']['pension_alimenticia'] = monto_pension
        
        # Fonacot (si tiene)
        if empleado_data.get('credito_fonacot'):
            resultado['deducciones']['fonacot'] = Decimal(str(empleado_data['credito_fonacot']['monto_quincenal']))
        
        # Descuento por faltas
        if dias_faltas > 0:
            descuento_faltas = salario_diario * dias_faltas
            resultado['deducciones']['faltas'] = descuento_faltas
        
        # Total deducciones
        total_deducciones = sum(resultado['deducciones'].values())
        resultado['totales']['deducciones'] = total_deducciones
        
        # 4. Calcular neto
        neto_pagar = total_percepciones - total_deducciones
        resultado['totales']['neto'] = max(neto_pagar, Decimal('0'))
        
        # 5. Información adicional
        resultado['detalles'].update({
            'salario_diario': salario_diario,
            'sdi': sdi,
            'base_gravable_isr': base_gravable_isr,
            'cuotas_imss_patron': cuotas_imss['totales']['patron'],
            'fecha_calculo': datetime.now().isoformat()
        })
        
        # Redondear todos los valores a 2 decimales
        for seccion in ['percepciones', 'deducciones', 'totales']:
            if seccion in resultado:
                for concepto in resultado[seccion]:
                    if isinstance(resultado[seccion][concepto], Decimal):
                        resultado[seccion][concepto] = resultado[seccion][concepto].quantize(
                            Decimal('0.01')
                        )
        
        return resultado
    
    def _calcular_dias_trabajados(
        self, 
        asistencias: List[Dict], 
        incidencias: List[Dict], 
        dias_periodo: int
    ) -> tuple:
        """Calcula días trabajados y faltas"""
        
        dias_con_asistencia = len(asistencias)
        dias_faltas = 0
        dias_incidencias_pagadas = 0
        
        for incidencia in incidencias:
            if incidencia['tipo'] == 'FALTA':
                dias_faltas += incidencia['dias_totales']
            elif incidencia['tipo'] in ['INCAPACIDAD_ENFERMEDAD', 'VACACIONES']:
                dias_incidencias_pagadas += incidencia['dias_totales']
        
        dias_trabajados = min(dias_con_asistencia + dias_incidencias_pagadas, dias_periodo)
        
        return dias_trabajados, dias_faltas
    
    def _calcular_horas_extra(self, asistencias: List[Dict]) -> Dict:
        """Calcula horas extra dobles y triples"""
        
        horas_extra = {'dobles': 0, 'triples': 0}
        
        for asistencia in asistencias:
            if asistencia.get('horas_extra'):
                horas = asistencia['horas_extra']
                # Primeras 9 horas a la semana son dobles
                if horas <= 9:
                    horas_extra['dobles'] += horas
                else:
                    horas_extra['dobles'] += 9
                    horas_extra['triples'] += horas - 9
        
        return horas_extra
    
    def _contar_domingos_trabajados(self, asistencias: List[Dict]) -> int:
        """Cuenta domingos trabajados"""
        
        domingos = 0
        for asistencia in asistencias:
            fecha = datetime.strptime(asistencia['fecha'], '%Y-%m-%d').date()
            if fecha.weekday() == 6:  # Domingo
                domingos += 1
        
        return domingos
    
    def _calcular_base_gravable_isr(self, percepciones: Dict[str, Decimal]) -> Decimal:
        """Calcula base gravable para ISR considerando exenciones"""
        
        base_gravable = Decimal('0')
        
        # Conceptos y sus límites de exención
        for concepto, monto in percepciones.items():
            if concepto == 'prima_dominical':
                # Exenta hasta 1 UMA
                exento = min(monto, self.UMA_DIARIO * 15)  # Por quincena
                base_gravable += monto - exento
            elif concepto in ['tiempo_extra_doble', 'tiempo_extra_triple']:
                # 50% exento con límite de 5 UMAs semanales
                exento = min(monto * Decimal('0.5'), self.UMA_DIARIO * 5 * 2)  # 2 semanas
                base_gravable += monto - exento
            else:
                # Sueldo y otros conceptos son 100% gravables
                base_gravable += monto
        
        return base_gravable