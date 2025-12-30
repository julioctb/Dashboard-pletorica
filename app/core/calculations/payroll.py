"""
Motor principal de cálculo de nómina
"""
from decimal import Decimal
from datetime import date, datetime
from typing import Dict, List, Optional

#TODO CONECTAR CON MODULO IMSS E ISR
# from .imss import CalculadoraIMSS
# from .isr import CalculadoraISR

class MotorNomina:
    """Motor de cálculo de nómina integrado"""
    
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