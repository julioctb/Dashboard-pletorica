from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class FieldConfig:
    '''Configuración declarativa de un campo validable'''
    nombre: str
    nombre_display: Optional[str] = None
    requerido: bool = False
    min_len: Optional[int] = None
    max_len: Optional[int] = None
    patron: Optional[str] = None
    patron_error: Optional[str] = None
    transformar: Optional[Callable] = None
    validador_custom: Optional[Callable] = None

    def __post_init__(self):
        if self.nombre_display is None:
            self.nombre_display = self.nombre
