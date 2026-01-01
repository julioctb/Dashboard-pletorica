"""
Módulo de calculations - Calculadoras especializadas.

Exporta las calculadoras para importación conveniente:
- CalculadoraCostoPatronal: Orquestador principal
- CalculadoraIMSS: Cuotas IMSS patronales y obreras
- CalculadoraISR: Impuesto sobre la renta
- CalculadoraProvisiones: Aguinaldo, vacaciones, prima vacacional

Uso:
    from app.core.calculations import CalculadoraCostoPatronal

    calc = CalculadoraCostoPatronal(config_empresa)
    resultado = calc.calcular(trabajador)
"""

from .simulador_costo_patronal import CalculadoraCostoPatronal
from .calculadora_imss import CalculadoraIMSS
from .calculadora_isr import CalculadoraISR
from .calculadora_provisiones import CalculadoraProvisiones

__all__ = [
    "CalculadoraCostoPatronal",
    "CalculadoraIMSS",
    "CalculadoraISR",
    "CalculadoraProvisiones",
]
