"""
Configuración declarativa de campos validables.

FieldConfig unifica validación backend y frontend, además de
proporcionar metadatos para generación automática de formularios.

Uso:
    from app.core.validation import CAMPO_RFC

    # En entidad (Pydantic)
    @field_validator('rfc', mode='before')
    def validar_rfc(cls, v):
        v, error = validar_con_config(v, CAMPO_RFC)
        if error:
            raise ValueError(error)
        return v

    # En formulario (Reflex)
    form_field(CAMPO_RFC, value=State.form_rfc, error=State.error_rfc)
"""
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Tuple
from enum import Enum


class InputType(str, Enum):
    """Tipos de input soportados para formularios."""
    TEXT = "text"
    EMAIL = "email"
    TEL = "tel"
    NUMBER = "number"
    PASSWORD = "password"
    SELECT = "select"
    TEXTAREA = "textarea"


@dataclass
class FieldConfig:
    """
    Configuración declarativa de un campo validable.

    Combina reglas de validación con metadatos de UI para generar
    automáticamente tanto validadores como componentes de formulario.

    Attributes:
        # === Identificación ===
        nombre: Nombre interno del campo (para mensajes de error)
        nombre_display: Nombre para mostrar (si difiere de nombre)

        # === Validación ===
        requerido: Si el campo es obligatorio
        min_len: Longitud mínima
        max_len: Longitud máxima
        patron: Regex para validar formato
        patron_error: Mensaje de error si no cumple patrón
        transformar: Función para transformar valor (ej: str.upper)
        validador_custom: Función de validación personalizada

        # === UI (Formularios) ===
        label: Etiqueta del campo (ej: "Nombre comercial *")
        placeholder: Texto placeholder del input
        hint: Texto de ayuda debajo del campo
        input_type: Tipo de input (text, email, select, textarea, etc.)
        options: Opciones para select [(value, label), ...]
        rows: Filas para textarea
        section: Sección del formulario donde aparece
        order: Orden dentro de la sección (menor = primero)
        width: Ancho del campo ("full", "half", "third")
    """

    # === Identificación ===
    nombre: str
    nombre_display: Optional[str] = None

    # === Validación ===
    requerido: bool = False
    min_len: Optional[int] = None
    max_len: Optional[int] = None
    patron: Optional[str] = None
    patron_error: Optional[str] = None
    transformar: Optional[Callable[[str], str]] = None
    validador_custom: Optional[Callable[[str], str]] = None

    # === UI (Formularios) ===
    label: Optional[str] = None
    placeholder: Optional[str] = None
    hint: Optional[str] = None
    input_type: InputType = InputType.TEXT
    options: Optional[List[Tuple[str, str]]] = None  # [(value, label), ...]
    rows: int = 4  # Para textarea
    section: Optional[str] = None
    order: int = 0
    width: str = "full"  # "full", "half", "third"

    def __post_init__(self):
        """Inicializa valores por defecto basados en otros campos."""
        if self.nombre_display is None:
            self.nombre_display = self.nombre

        if self.label is None:
            # Auto-generar label: "Nombre comercial" + "*" si requerido
            self.label = f"{self.nombre}{'*' if self.requerido else ''}"

        if self.placeholder is None:
            # Auto-generar placeholder igual al nombre
            self.placeholder = self.nombre

    @property
    def is_select(self) -> bool:
        """Verifica si es un campo select."""
        return self.input_type == InputType.SELECT

    @property
    def is_textarea(self) -> bool:
        """Verifica si es un campo textarea."""
        return self.input_type == InputType.TEXTAREA

    @property
    def has_validation(self) -> bool:
        """Verifica si tiene alguna regla de validación."""
        return (
            self.requerido or
            self.min_len is not None or
            self.max_len is not None or
            self.patron is not None or
            self.validador_custom is not None
        )

    def get_max_length_hint(self) -> Optional[str]:
        """Genera hint de longitud máxima si aplica."""
        if self.max_len and not self.hint:
            return f"Máximo {self.max_len} caracteres"
        return None

    def get_length_hint(self) -> Optional[str]:
        """Genera hint de longitud si aplica."""
        if self.min_len and self.max_len:
            if self.min_len == self.max_len:
                return f"Exactamente {self.min_len} caracteres"
            return f"{self.min_len}-{self.max_len} caracteres"
        elif self.min_len:
            return f"Mínimo {self.min_len} caracteres"
        elif self.max_len:
            return f"Máximo {self.max_len} caracteres"
        return None
