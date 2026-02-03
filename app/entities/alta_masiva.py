"""
Entidades para Alta Masiva de Personal.

Modelos de dominio para el proceso de carga masiva de empleados
via archivos CSV/Excel.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ResultadoFila(str, Enum):
    """Resultado de la validacion de una fila del archivo"""
    VALIDO = 'VALIDO'
    REINGRESO = 'REINGRESO'
    ERROR = 'ERROR'


class RegistroValidado(BaseModel):
    """
    Resultado de validar una fila individual del archivo.

    Contiene los datos parseados, el resultado de validacion,
    y metadata para el procesamiento posterior.
    """
    model_config = ConfigDict(use_enum_values=True)

    fila: int
    resultado: ResultadoFila
    curp: str = ""
    datos: dict = {}
    empleado_existente_id: Optional[int] = None
    empresa_anterior_id: Optional[int] = None
    errores: List[str] = []
    mensaje: str = ""


class ResultadoValidacion(BaseModel):
    """
    Resultado completo de la fase de validacion del archivo.

    Agrupa los registros por resultado (validos, reingresos, errores)
    para que la UI pueda mostrar un resumen antes de procesar.
    """
    total_filas: int = 0
    validos: List[RegistroValidado] = []
    reingresos: List[RegistroValidado] = []
    errores: List[RegistroValidado] = []

    @property
    def total_validos(self) -> int:
        return len(self.validos)

    @property
    def total_reingresos(self) -> int:
        return len(self.reingresos)

    @property
    def total_errores(self) -> int:
        return len(self.errores)

    @property
    def puede_procesar(self) -> bool:
        """True si hay al menos un registro valido o reingreso para procesar"""
        return len(self.validos) > 0 or len(self.reingresos) > 0


class DetalleResultado(BaseModel):
    """Detalle del resultado de procesamiento de una fila"""
    model_config = ConfigDict(use_enum_values=True)

    fila: int
    curp: str
    resultado: ResultadoFila
    clave: str = ""
    mensaje: str = ""


class ResultadoProcesamiento(BaseModel):
    """
    Resultado final del procesamiento de alta masiva.

    Contiene contadores y detalles por fila para generar
    el reporte de resultados.
    """
    creados: int = 0
    reingresados: int = 0
    errores: int = 0
    detalles: List[DetalleResultado] = []

    @property
    def total_procesados(self) -> int:
        return self.creados + self.reingresados

    @property
    def total_intentados(self) -> int:
        return self.creados + self.reingresados + self.errores
