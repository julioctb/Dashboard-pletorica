from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_serializer

class EstatusSede(str, Enum):
    ACTIVA = 'ACTIVA'
    INACTIVA = ' INACTIVA'
    EN_MANTENIMIENTO ='EN MANTENIMIENTO'

class Sede(BaseModel):

    model_config = ConfigDict(
        use_enum_values= True,
        str_strip_whitespace= True,
        validate_assignment= True,
        from_attributes= True

    )

    id: Optional[int] = None
    codigo: str = Field(
        min_length=3,
        max_length= 10,
        description='Codigo único de la sede'
    )
    nombre: str = Field(
        min_length=1,
        max_length=100,
        description='Nombre de la sede'
    )
    direccion: str = Field(
        min_length= 1,
        max_length= 200,
        description='Direccion completa'
    )
    personal_actual: str = Field(
        default=0,
        ge=0,
        description='Personal asignado'
    )
    empresas_ids: List[int] = Field(
        default_factory=list,
        description='IDs de empresas que operan esta sede'
    )
    responsable_de_sede: str = Field(
        None,
        max_length=100,
        description='Nombre del responable de la sede por parte del contratante' 
    )
    telefono_responsable: Optional[str] = Field(
        None,
        max_length=15
    )
    estatus : EstatusSede = Field( default= EstatusSede.ACTIVA)
    fecha_de_registro: Optional[datetime] = None
    notas: Optional[str] = None

