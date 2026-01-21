"""
Entidades de dominio para Empleados.

El CURP es el identificador único real (gobierno mexicano).
La clave interna (B25-00001) es para uso operativo del sistema.
"""
import re
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.enums import EstatusEmpleado, GeneroEmpleado, MotivoBaja
from app.core.error_messages import msg_entidad_ya_estado

# Patrón de validación CURP
CURP_PATTERN = r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z][0-9]$'

# Patrón de validación RFC persona física (13 caracteres)
# Homoclave: 2 caracteres alfanuméricos + 1 dígito verificador (0-9 o A)
RFC_PERSONA_PATTERN = r'^[A-Z&Ñ]{4}[0-9]{6}[A-Z0-9]{2}[0-9A]$'

# Patrón de validación NSS (11 dígitos)
NSS_PATTERN = r'^[0-9]{11}$'

# Patrón de clave de empleado
CLAVE_EMPLEADO_PATTERN = r'^B[0-9]{2}-[0-9]{5}$'


class Empleado(BaseModel):
    """
    Entidad principal de Empleado.

    El CURP es el identificador único real (gobierno).
    La clave (B25-00001) es para uso operativo interno y nunca cambia.
    El empleado puede cambiar de empresa (proveedor) manteniendo su clave e historial.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación interna
    id: Optional[int] = None
    clave: str = Field(
        max_length=10,
        pattern=CLAVE_EMPLEADO_PATTERN,
        description="Clave permanente única: B25-00001"
    )
    empresa_id: int = Field(description="ID del proveedor actual")

    # Identificación oficial
    curp: str = Field(
        min_length=18,
        max_length=18,
        description="CURP - Identificador único del gobierno mexicano"
    )
    rfc: Optional[str] = Field(
        None,
        min_length=13,
        max_length=13,
        description="RFC persona física (13 caracteres)"
    )
    nss: Optional[str] = Field(
        None,
        min_length=11,
        max_length=11,
        description="Número de Seguro Social IMSS"
    )

    # Datos personales
    nombre: str = Field(min_length=2, max_length=100)
    apellido_paterno: str = Field(min_length=2, max_length=100)
    apellido_materno: Optional[str] = Field(None, max_length=100)
    fecha_nacimiento: Optional[date] = None
    genero: Optional[GeneroEmpleado] = None

    # Contacto
    telefono: Optional[str] = Field(None, max_length=10)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = Field(None, max_length=500)
    contacto_emergencia: Optional[str] = Field(
        None,
        max_length=200,
        description="Nombre y teléfono de contacto de emergencia"
    )

    # Estado laboral
    estatus: EstatusEmpleado = Field(default=EstatusEmpleado.ACTIVO)
    fecha_ingreso: date = Field(default_factory=date.today)
    fecha_baja: Optional[date] = None
    motivo_baja: Optional[MotivoBaja] = None

    # Notas
    notas: Optional[str] = Field(None, max_length=1000)

    # Auditoría
    fecha_creacion: Optional[datetime] = None
    fecha_actualizacion: Optional[datetime] = None

    # =========================================================================
    # VALIDADORES
    # =========================================================================

    @field_validator('curp', mode='before')
    @classmethod
    def validar_curp(cls, v: str) -> str:
        """Valida formato de CURP."""
        if v:
            v = v.upper().strip()
            if len(v) != 18:
                raise ValueError(f'CURP debe tener 18 caracteres (tiene {len(v)})')
            if not re.match(CURP_PATTERN, v):
                raise ValueError('CURP con formato inválido')
        return v

    @field_validator('rfc', mode='before')
    @classmethod
    def validar_rfc(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato de RFC persona física."""
        if v:
            v = v.upper().strip()
            if len(v) != 13:
                raise ValueError(f'RFC debe tener 13 caracteres (tiene {len(v)})')
            if not re.match(RFC_PERSONA_PATTERN, v):
                raise ValueError('RFC con formato inválido')
        return v

    @field_validator('nss', mode='before')
    @classmethod
    def validar_nss(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato de NSS."""
        if v:
            v = v.strip()
            if not re.match(NSS_PATTERN, v):
                raise ValueError('NSS debe tener 11 dígitos numéricos')
        return v

    @field_validator('nombre', 'apellido_paterno', 'apellido_materno', mode='before')
    @classmethod
    def normalizar_nombre(cls, v: Optional[str]) -> Optional[str]:
        """Normaliza nombres a mayúsculas."""
        if v:
            return v.upper().strip()
        return v

    @field_validator('email', mode='before')
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        """Valida formato de email."""
        if v:
            v = v.lower().strip()
            if '@' not in v or '.' not in v:
                raise ValueError('Email con formato inválido')
        return v

    @field_validator('telefono', mode='before')
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        """Valida teléfono (solo 10 dígitos)."""
        if v:
            v = re.sub(r'[^0-9]', '', v)
            if len(v) != 10:
                raise ValueError('Teléfono debe tener 10 dígitos')
        return v

    @field_validator('fecha_baja', mode='after')
    @classmethod
    def validar_fecha_baja(cls, v: Optional[date], info) -> Optional[date]:
        """Valida que fecha_baja sea >= fecha_ingreso."""
        if v and 'fecha_ingreso' in info.data:
            fecha_ingreso = info.data['fecha_ingreso']
            if fecha_ingreso and v < fecha_ingreso:
                raise ValueError('Fecha de baja no puede ser anterior a fecha de ingreso')
        return v

    # =========================================================================
    # MÉTODOS DE CONSULTA
    # =========================================================================

    def esta_activo(self) -> bool:
        """Retorna True si el empleado está activo."""
        return self.estatus == EstatusEmpleado.ACTIVO

    def esta_inactivo(self) -> bool:
        """Retorna True si el empleado está inactivo."""
        return self.estatus == EstatusEmpleado.INACTIVO

    def esta_suspendido(self) -> bool:
        """Retorna True si el empleado está suspendido."""
        return self.estatus == EstatusEmpleado.SUSPENDIDO

    def nombre_completo(self) -> str:
        """Retorna el nombre completo del empleado."""
        partes = [self.nombre, self.apellido_paterno]
        if self.apellido_materno:
            partes.append(self.apellido_materno)
        return " ".join(partes)

    def nombre_corto(self) -> str:
        """Retorna nombre y apellido paterno."""
        return f"{self.nombre} {self.apellido_paterno}"

    def edad(self) -> Optional[int]:
        """Calcula la edad basada en fecha_nacimiento."""
        if not self.fecha_nacimiento:
            return None
        hoy = date.today()
        edad = hoy.year - self.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            edad -= 1
        return edad

    def antiguedad_dias(self) -> int:
        """Calcula días de antigüedad desde fecha_ingreso."""
        fecha_fin = self.fecha_baja or date.today()
        return (fecha_fin - self.fecha_ingreso).days

    def antiguedad_anios(self) -> float:
        """Calcula años de antigüedad."""
        return round(self.antiguedad_dias() / 365.25, 1)

    # =========================================================================
    # MÉTODOS DE CAMBIO DE ESTADO
    # =========================================================================

    def activar(self):
        """Activa el empleado."""
        if self.estatus == EstatusEmpleado.ACTIVO:
            raise ValueError(msg_entidad_ya_estado("El empleado", "activo"))
        self.estatus = EstatusEmpleado.ACTIVO
        self.fecha_baja = None
        self.motivo_baja = None

    def suspender(self):
        """Suspende el empleado."""
        if self.estatus == EstatusEmpleado.SUSPENDIDO:
            raise ValueError(msg_entidad_ya_estado("El empleado", "suspendido"))
        self.estatus = EstatusEmpleado.SUSPENDIDO

    def dar_de_baja(self, motivo: MotivoBaja, fecha: Optional[date] = None):
        """Da de baja al empleado con motivo y fecha."""
        if self.estatus == EstatusEmpleado.INACTIVO:
            raise ValueError(msg_entidad_ya_estado("El empleado", "dado de baja"))
        self.estatus = EstatusEmpleado.INACTIVO
        self.fecha_baja = fecha or date.today()
        self.motivo_baja = motivo

    # =========================================================================
    # MÉTODOS ESTÁTICOS
    # =========================================================================

    @staticmethod
    def generar_clave(anio: int, consecutivo: int) -> str:
        """
        Genera clave de empleado: B25-00001

        Args:
            anio: Año de registro (ej: 2025)
            consecutivo: Número consecutivo del año

        Returns:
            Clave formateada (ej: B25-00001)
        """
        anio_corto = str(anio)[-2:]
        return f"B{anio_corto}-{consecutivo:05d}"

    def __str__(self) -> str:
        return f"{self.clave} - {self.nombre_completo()}"


class EmpleadoCreate(BaseModel):
    """
    Modelo para crear un nuevo empleado.
    La clave se genera automáticamente en el servicio.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    empresa_id: int
    curp: str = Field(min_length=18, max_length=18)
    rfc: Optional[str] = Field(None, max_length=13)
    nss: Optional[str] = Field(None, max_length=11)
    nombre: str = Field(min_length=2, max_length=100)
    apellido_paterno: str = Field(min_length=2, max_length=100)
    apellido_materno: Optional[str] = Field(None, max_length=100)
    fecha_nacimiento: Optional[date] = None
    genero: Optional[GeneroEmpleado] = None
    telefono: Optional[str] = Field(None, max_length=10)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = Field(None, max_length=500)
    contacto_emergencia: Optional[str] = Field(None, max_length=200)
    fecha_ingreso: Optional[date] = None
    notas: Optional[str] = Field(None, max_length=1000)

    # Validadores reutilizados
    validar_curp = field_validator('curp', mode='before')(Empleado.validar_curp.__func__)
    validar_rfc = field_validator('rfc', mode='before')(Empleado.validar_rfc.__func__)
    validar_nss = field_validator('nss', mode='before')(Empleado.validar_nss.__func__)
    normalizar_nombre = field_validator('nombre', 'apellido_paterno', 'apellido_materno', mode='before')(
        Empleado.normalizar_nombre.__func__
    )


class EmpleadoUpdate(BaseModel):
    """
    Modelo para actualizar un empleado existente.
    CURP y clave NO se pueden modificar.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    # empresa_id puede cambiar (cambio de proveedor)
    empresa_id: Optional[int] = None

    # CURP NO se puede cambiar - no incluido

    rfc: Optional[str] = Field(None, max_length=13)
    nss: Optional[str] = Field(None, max_length=11)
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido_paterno: Optional[str] = Field(None, min_length=2, max_length=100)
    apellido_materno: Optional[str] = Field(None, max_length=100)
    fecha_nacimiento: Optional[date] = None
    genero: Optional[GeneroEmpleado] = None
    telefono: Optional[str] = Field(None, max_length=10)
    email: Optional[str] = Field(None, max_length=100)
    direccion: Optional[str] = Field(None, max_length=500)
    contacto_emergencia: Optional[str] = Field(None, max_length=200)
    estatus: Optional[EstatusEmpleado] = None
    fecha_baja: Optional[date] = None
    motivo_baja: Optional[MotivoBaja] = None
    notas: Optional[str] = Field(None, max_length=1000)


class EmpleadoResumen(BaseModel):
    """
    Modelo resumido de empleado para listados.
    Optimizado para mostrar en tablas y cards.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True
    )

    id: int
    clave: str
    curp: str
    nombre_completo: str
    empresa_id: int
    empresa_nombre: Optional[str] = None
    estatus: EstatusEmpleado
    fecha_ingreso: date
    telefono: Optional[str] = None
    email: Optional[str] = None

    @classmethod
    def from_empleado(cls, empleado: Empleado, empresa_nombre: Optional[str] = None) -> 'EmpleadoResumen':
        """Factory method para crear desde un empleado completo."""
        return cls(
            id=empleado.id,
            clave=empleado.clave,
            curp=empleado.curp,
            nombre_completo=empleado.nombre_completo(),
            empresa_id=empleado.empresa_id,
            empresa_nombre=empresa_nombre,
            estatus=empleado.estatus,
            fecha_ingreso=empleado.fecha_ingreso,
            telefono=empleado.telefono,
            email=empleado.email,
        )
