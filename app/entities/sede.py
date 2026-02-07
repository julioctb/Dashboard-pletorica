"""
Entidades de dominio para Sedes BUAP.

Las sedes representan ubicaciones y unidades organizacionales de BUAP:
campus, facultades, edificios, direcciones, coordinaciones, etc.

Soporta jerarquía organizacional (sede_padre_id) y ubicación física
(ubicacion_fisica_id) como conceptos independientes.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator

from app.core.enums import Estatus, TipoSede
from app.core.validation import (
    CAMPO_CODIGO_SEDE,
    CAMPO_NOMBRE_SEDE,
    CAMPO_NOMBRE_CORTO_SEDE,
    pydantic_field,
    campo_validador,
)


class Sede(BaseModel):
    """
    Entidad principal de Sede BUAP.

    Representa una ubicación o unidad organizacional dentro de BUAP.
    Soporta dos relaciones auto-referenciales independientes:
    - sede_padre_id: jerarquía organizacional (CAETO dentro de CU)
    - ubicacion_fisica_id: dónde está físicamente (CGAU en Torre de Gestión)
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    # Identificación
    id: Optional[int] = None
    codigo: str = pydantic_field(CAMPO_CODIGO_SEDE)
    nombre: str = pydantic_field(CAMPO_NOMBRE_SEDE)
    nombre_corto: Optional[str] = pydantic_field(CAMPO_NOMBRE_CORTO_SEDE)
    tipo_sede: TipoSede = Field(...)

    # Ubicación
    es_ubicacion_fisica: bool = Field(default=True)
    sede_padre_id: Optional[int] = None
    ubicacion_fisica_id: Optional[int] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None

    # Control
    estatus: Estatus = Field(default=Estatus.ACTIVO)

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    # =========================================================================
    # VALIDADORES
    # =========================================================================

    validar_codigo = campo_validador('codigo', CAMPO_CODIGO_SEDE)
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_SEDE)

    @model_validator(mode='after')
    def validar_coherencia_ubicacion(self):
        """Si es ubicación física, no puede tener ubicacion_fisica_id."""
        if self.es_ubicacion_fisica and self.ubicacion_fisica_id is not None:
            raise ValueError(
                'Una sede con espacio físico propio no puede tener ubicacion_fisica_id'
            )
        return self

    @field_validator('sede_padre_id')
    @classmethod
    def validar_no_auto_referencia_padre(cls, v, info):
        """sede_padre_id no puede apuntar a sí mismo."""
        if v is not None and info.data.get('id') is not None and v == info.data['id']:
            raise ValueError('Una sede no puede ser su propia sede padre')
        return v

    @field_validator('ubicacion_fisica_id')
    @classmethod
    def validar_no_auto_referencia_ubicacion(cls, v, info):
        """ubicacion_fisica_id no puede apuntar a sí mismo."""
        if v is not None and info.data.get('id') is not None and v == info.data['id']:
            raise ValueError('Una sede no puede ser su propia ubicación física')
        return v

    # =========================================================================
    # MÉTODOS DE NEGOCIO
    # =========================================================================

    def esta_activa(self) -> bool:
        return self.estatus == Estatus.ACTIVO

    def es_raiz(self) -> bool:
        """True si no tiene sede padre (es raíz del árbol)."""
        return self.sede_padre_id is None

    def nombre_display(self) -> str:
        """Nombre corto si existe, sino nombre completo."""
        return self.nombre_corto or self.nombre

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nombre}"


class SedeCreate(BaseModel):
    """Modelo para crear una nueva sede."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    codigo: str = pydantic_field(CAMPO_CODIGO_SEDE)
    nombre: str = pydantic_field(CAMPO_NOMBRE_SEDE)
    nombre_corto: Optional[str] = pydantic_field(CAMPO_NOMBRE_CORTO_SEDE)
    tipo_sede: TipoSede = Field(...)
    es_ubicacion_fisica: bool = Field(default=True)
    sede_padre_id: Optional[int] = None
    ubicacion_fisica_id: Optional[int] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
    estatus: Estatus = Field(default=Estatus.ACTIVO)

    # Validadores
    validar_codigo = campo_validador('codigo', CAMPO_CODIGO_SEDE)
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_SEDE)

    @model_validator(mode='after')
    def validar_coherencia_ubicacion(self):
        if self.es_ubicacion_fisica and self.ubicacion_fisica_id is not None:
            raise ValueError(
                'Una sede con espacio físico propio no puede tener ubicacion_fisica_id'
            )
        return self


class SedeUpdate(BaseModel):
    """Modelo para actualizar una sede existente (campos opcionales)."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    codigo: Optional[str] = pydantic_field(CAMPO_CODIGO_SEDE, default=None)
    nombre: Optional[str] = pydantic_field(CAMPO_NOMBRE_SEDE, default=None)
    nombre_corto: Optional[str] = pydantic_field(CAMPO_NOMBRE_CORTO_SEDE)
    tipo_sede: Optional[TipoSede] = None
    es_ubicacion_fisica: Optional[bool] = None
    sede_padre_id: Optional[int] = None
    ubicacion_fisica_id: Optional[int] = None
    direccion: Optional[str] = None
    notas: Optional[str] = None
    estatus: Optional[Estatus] = None

    # Validadores
    validar_codigo = campo_validador('codigo', CAMPO_CODIGO_SEDE)
    validar_nombre = campo_validador('nombre', CAMPO_NOMBRE_SEDE)


class SedeResumen(BaseModel):
    """Modelo ligero para listados de sedes con campos calculados."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    nombre_corto: Optional[str] = None
    tipo_sede: str
    es_ubicacion_fisica: bool
    sede_padre_id: Optional[int] = None
    ubicacion_fisica_id: Optional[int] = None
    estatus: str

    # Campos enriquecidos (vienen de JOINs o cálculos)
    sede_padre_nombre: Optional[str] = None
    ubicacion_fisica_nombre: Optional[str] = None
    total_contactos: int = 0
    total_hijos: int = 0

    @property
    def tipo_descripcion(self) -> str:
        try:
            return TipoSede(self.tipo_sede).descripcion
        except ValueError:
            return self.tipo_sede

    @property
    def nombre_display(self) -> str:
        return self.nombre_corto or self.nombre

    @classmethod
    def from_sede(cls, sede: Sede, **extras) -> 'SedeResumen':
        return cls(
            id=sede.id,
            codigo=sede.codigo,
            nombre=sede.nombre,
            nombre_corto=sede.nombre_corto,
            tipo_sede=sede.tipo_sede if isinstance(sede.tipo_sede, str) else sede.tipo_sede.value,
            es_ubicacion_fisica=sede.es_ubicacion_fisica,
            sede_padre_id=sede.sede_padre_id,
            ubicacion_fisica_id=sede.ubicacion_fisica_id,
            estatus=sede.estatus if isinstance(sede.estatus, str) else sede.estatus.value,
            **extras,
        )
