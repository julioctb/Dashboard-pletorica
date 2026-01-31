"""
Entidades de dominio para Requisiciones.

Las requisiciones representan solicitudes de bienes y servicios que la BUAP
(Secretaría Administrativa) realiza antes de generar contratos con proveedores.

Flujo: Requisición (BUAP crea) → Aprobación → Adjudicación → Contrato

Número de requisición auto-generado: REQ-SA-{AÑO}-{CONSECUTIVO:04d}
Ejemplo: REQ-SA-2025-0001
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.core.enums import EstadoRequisicion, TipoContratacion, GrupoConfiguracion
from app.core.validation.constants import (
    NUMERO_REQUISICION_MAX,
    DEPENDENCIA_MAX,
    NOMBRE_PERSONA_MAX,
    CARGO_MAX,
    TELEFONO_REQUISICION_MAX,
    EMAIL_REQUISICION_MAX,
    DOMICILIO_REQUISICION_MAX,
    LUGAR_ENTREGA_MAX,
    TIPO_GARANTIA_MAX,
    FORMA_PAGO_MAX,
    GARANTIA_VIGENCIA_MAX,
    EXISTENCIA_ALMACEN_MAX,
    PARTIDA_PRESUPUESTARIA_MAX,
    AREA_DESTINO_MAX,
    ORIGEN_RECURSO_REQUISICION_MAX,
    OFICIO_SUFICIENCIA_MAX,
    UNIDAD_MEDIDA_MAX,
    CLAVE_CONFIGURACION_MAX,
    DESCRIPCION_CONFIGURACION_MAX,
)
from app.core.error_messages import (
    MSG_FECHA_ENTREGA_FIN_ANTERIOR,
)


# =============================================================================
# TRANSICIONES DE ESTADO VÁLIDAS
# =============================================================================

TRANSICIONES_VALIDAS = {
    EstadoRequisicion.BORRADOR: [
        EstadoRequisicion.ENVIADA,
        EstadoRequisicion.CANCELADA,
    ],
    EstadoRequisicion.ENVIADA: [
        EstadoRequisicion.EN_REVISION,
        EstadoRequisicion.BORRADOR,  # Devolver para corrección
        EstadoRequisicion.CANCELADA,
    ],
    EstadoRequisicion.EN_REVISION: [
        EstadoRequisicion.APROBADA,
        EstadoRequisicion.BORRADOR,  # Rechazada, requiere corrección
        EstadoRequisicion.CANCELADA,
    ],
    EstadoRequisicion.APROBADA: [
        EstadoRequisicion.ADJUDICADA,
        EstadoRequisicion.CANCELADA,
    ],
    EstadoRequisicion.ADJUDICADA: [
        EstadoRequisicion.CONTRATADA,
        EstadoRequisicion.CANCELADA,
    ],
    EstadoRequisicion.CONTRATADA: [],  # Estado final
    EstadoRequisicion.CANCELADA: [],   # Estado final
}


# =============================================================================
# LUGAR DE ENTREGA
# =============================================================================

class LugarEntrega(BaseModel):
    """Lugar de entrega disponible para requisiciones."""

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    nombre: str = Field(max_length=200)
    activo: bool = True
    created_at: Optional[datetime] = None


# =============================================================================
# CONFIGURACIÓN DE REQUISICIÓN
# =============================================================================

class ConfiguracionRequisicion(BaseModel):
    """Valores predeterminados que se pre-llenan al crear una requisición."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    clave: str = Field(max_length=CLAVE_CONFIGURACION_MAX)
    valor: str
    descripcion: Optional[str] = Field(None, max_length=DESCRIPCION_CONFIGURACION_MAX)
    grupo: GrupoConfiguracion
    orden: int = 0
    activo: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# ITEM DE REQUISICIÓN
# =============================================================================

class RequisicionItem(BaseModel):
    """Producto o servicio solicitado en la requisición."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    requisicion_id: Optional[int] = None
    numero_item: int
    unidad_medida: str = Field(max_length=UNIDAD_MEDIDA_MAX)
    cantidad: Decimal = Field(ge=0, decimal_places=2)
    descripcion: str
    precio_unitario_estimado: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    subtotal_estimado: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    especificaciones_tecnicas: Optional[str] = None
    created_at: Optional[datetime] = None

    # Archivos asociados (se cargan desde archivo_sistema)
    archivos: list = []


class RequisicionItemCreate(BaseModel):
    """Modelo para crear un item de requisición."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    numero_item: int = Field(..., ge=1)
    unidad_medida: str = Field(..., max_length=UNIDAD_MEDIDA_MAX)
    cantidad: Decimal = Field(..., gt=0, decimal_places=2)
    descripcion: str
    precio_unitario_estimado: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    especificaciones_tecnicas: Optional[str] = None

    @field_validator('cantidad', 'precio_unitario_estimado', mode='before')
    @classmethod
    def convertir_a_decimal(cls, v):
        """Convierte strings a Decimal."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return Decimal(v.replace(',', ''))
        return v


class RequisicionItemUpdate(BaseModel):
    """Modelo para actualizar un item (todos opcionales)."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    unidad_medida: Optional[str] = Field(None, max_length=UNIDAD_MEDIDA_MAX)
    cantidad: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    descripcion: Optional[str] = None
    precio_unitario_estimado: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    especificaciones_tecnicas: Optional[str] = None

    @field_validator('cantidad', 'precio_unitario_estimado', mode='before')
    @classmethod
    def convertir_a_decimal(cls, v):
        """Convierte strings a Decimal."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return Decimal(v.replace(',', ''))
        return v


# =============================================================================
# PARTIDA PRESUPUESTAL
# =============================================================================

class RequisicionPartida(BaseModel):
    """Distribución presupuestal por área."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    id: Optional[int] = None
    requisicion_id: Optional[int] = None
    partida_presupuestaria: str = Field(max_length=PARTIDA_PRESUPUESTARIA_MAX)
    area_destino: str = Field(max_length=AREA_DESTINO_MAX)
    origen_recurso: str = Field(max_length=ORIGEN_RECURSO_REQUISICION_MAX)
    oficio_suficiencia: Optional[str] = Field(None, max_length=OFICIO_SUFICIENCIA_MAX)
    presupuesto_autorizado: Decimal = Field(ge=0, decimal_places=2)
    descripcion: Optional[str] = None
    created_at: Optional[datetime] = None


class RequisicionPartidaCreate(BaseModel):
    """Modelo para crear una partida presupuestal."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    partida_presupuestaria: str = Field(..., max_length=PARTIDA_PRESUPUESTARIA_MAX)
    area_destino: str = Field(..., max_length=AREA_DESTINO_MAX)
    origen_recurso: str = Field(..., max_length=ORIGEN_RECURSO_REQUISICION_MAX)
    oficio_suficiencia: Optional[str] = Field(None, max_length=OFICIO_SUFICIENCIA_MAX)
    presupuesto_autorizado: Decimal = Field(..., gt=0, decimal_places=2)
    descripcion: Optional[str] = None

    @field_validator('presupuesto_autorizado', mode='before')
    @classmethod
    def convertir_a_decimal(cls, v):
        """Convierte strings a Decimal."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return Decimal(v.replace(',', ''))
        return v


class RequisicionPartidaUpdate(BaseModel):
    """Modelo para actualizar una partida (todos opcionales)."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    partida_presupuestaria: Optional[str] = Field(None, max_length=PARTIDA_PRESUPUESTARIA_MAX)
    area_destino: Optional[str] = Field(None, max_length=AREA_DESTINO_MAX)
    origen_recurso: Optional[str] = Field(None, max_length=ORIGEN_RECURSO_REQUISICION_MAX)
    oficio_suficiencia: Optional[str] = Field(None, max_length=OFICIO_SUFICIENCIA_MAX)
    presupuesto_autorizado: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    descripcion: Optional[str] = None

    @field_validator('presupuesto_autorizado', mode='before')
    @classmethod
    def convertir_a_decimal(cls, v):
        """Convierte strings a Decimal."""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            return Decimal(v.replace(',', ''))
        return v


# =============================================================================
# REQUISICIÓN PRINCIPAL
# =============================================================================

class Requisicion(BaseModel):
    """
    Entidad principal de Requisición.

    Representa una solicitud de bienes o servicios de la BUAP
    (Secretaría Administrativa) antes de generar un contrato.
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

    # Identificación
    id: Optional[int] = None
    numero_requisicion: str = Field(max_length=NUMERO_REQUISICION_MAX)
    fecha_elaboracion: date
    estado: EstadoRequisicion = Field(default=EstadoRequisicion.BORRADOR)

    # Área Requirente (campos con valores default editables)
    dependencia_requirente: str = Field(max_length=DEPENDENCIA_MAX)
    domicilio: str = Field("", max_length=DOMICILIO_REQUISICION_MAX)
    titular_nombre: str = Field(max_length=NOMBRE_PERSONA_MAX)
    titular_cargo: str = Field(max_length=CARGO_MAX)
    titular_telefono: Optional[str] = Field(None, max_length=TELEFONO_REQUISICION_MAX)
    titular_email: Optional[str] = Field(None, max_length=EMAIL_REQUISICION_MAX)
    coordinador_nombre: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    coordinador_telefono: Optional[str] = Field(None, max_length=TELEFONO_REQUISICION_MAX)
    coordinador_email: Optional[str] = Field(None, max_length=EMAIL_REQUISICION_MAX)
    asesor_nombre: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    asesor_telefono: Optional[str] = Field(None, max_length=TELEFONO_REQUISICION_MAX)
    asesor_email: Optional[str] = Field(None, max_length=EMAIL_REQUISICION_MAX)

    # Datos del Bien/Servicio
    tipo_contratacion: TipoContratacion
    objeto_contratacion: str
    lugar_entrega: str = Field("", max_length=LUGAR_ENTREGA_MAX)
    fecha_entrega_inicio: Optional[date] = None
    fecha_entrega_fin: Optional[date] = None
    condiciones_entrega: Optional[str] = None
    tipo_garantia: Optional[str] = Field(None, max_length=TIPO_GARANTIA_MAX)
    garantia_vigencia: Optional[str] = Field(None, max_length=GARANTIA_VIGENCIA_MAX)
    requisitos_proveedor: Optional[str] = None
    justificacion: str
    forma_pago: Optional[str] = Field(None, max_length=FORMA_PAGO_MAX)
    requiere_anticipo: bool = False
    requiere_muestras: bool = False
    requiere_visita: bool = False

    # PDI (Plan de Desarrollo Institucional)
    pdi_eje: Optional[str] = None
    pdi_objetivo: Optional[str] = None
    pdi_estrategia: Optional[str] = None
    pdi_meta: Optional[str] = None

    # Otros
    existencia_almacen: Optional[str] = Field(None, max_length=EXISTENCIA_ALMACEN_MAX)
    observaciones: Optional[str] = None

    # Firmas (campos con valores default editables)
    validacion_asesor: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    elabora_nombre: str = Field(max_length=NOMBRE_PERSONA_MAX)
    elabora_cargo: str = Field(max_length=CARGO_MAX)
    solicita_nombre: str = Field(max_length=NOMBRE_PERSONA_MAX)
    solicita_cargo: str = Field(max_length=CARGO_MAX)

    # Adjudicación
    empresa_id: Optional[int] = None
    fecha_adjudicacion: Optional[date] = None

    # Auditoría
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relaciones (se cargan con joins)
    items: List[RequisicionItem] = []
    partidas: List[RequisicionPartida] = []
    archivos: list = []  # Se cargan desde archivo_sistema

    # ==========================================
    # VALIDADORES
    # ==========================================

    @field_validator('numero_requisicion')
    @classmethod
    def validar_numero(cls, v: str) -> str:
        """Normaliza el número de requisición a mayúsculas."""
        if v:
            v = v.upper().strip()
        return v

    @model_validator(mode='after')
    def validar_fechas(self) -> 'Requisicion':
        """Valida coherencia de fechas de entrega."""
        if self.fecha_entrega_inicio and self.fecha_entrega_fin:
            if self.fecha_entrega_fin < self.fecha_entrega_inicio:
                raise ValueError(MSG_FECHA_ENTREGA_FIN_ANTERIOR)
        return self

    # ==========================================
    # MÉTODOS ESTÁTICOS
    # ==========================================

    @staticmethod
    def generar_numero(anio: int, consecutivo: int) -> str:
        """
        Genera el número único de requisición.

        Args:
            anio: Año de la requisición (ej: 2025)
            consecutivo: Número consecutivo (ej: 1)

        Returns:
            Número formateado: REQ-SA-2025-0001
        """
        return f"REQ-SA-{anio}-{consecutivo:04d}"

    # ==========================================
    # MÉTODOS DE NEGOCIO
    # ==========================================

    def puede_editarse(self) -> bool:
        """Solo se puede editar en estado BORRADOR."""
        return self.estado == EstadoRequisicion.BORRADOR

    def puede_eliminarse(self) -> bool:
        """Solo se puede eliminar en estado BORRADOR."""
        return self.estado == EstadoRequisicion.BORRADOR

    def puede_transicionar_a(self, nuevo_estado: EstadoRequisicion) -> bool:
        """Verifica si la transición de estado es válida."""
        estado_actual = EstadoRequisicion(self.estado)
        return nuevo_estado in TRANSICIONES_VALIDAS.get(estado_actual, [])

    def __str__(self) -> str:
        return f"{self.numero_requisicion} - {self.estado}"


# =============================================================================
# MODELOS DE CREACIÓN/ACTUALIZACIÓN
# =============================================================================

class RequisicionCreate(BaseModel):
    """Modelo para crear una nueva requisición."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    fecha_elaboracion: date

    # Área Requirente (pueden venir pre-llenados desde configuración)
    dependencia_requirente: str = Field("", max_length=DEPENDENCIA_MAX)
    domicilio: str = Field("", max_length=DOMICILIO_REQUISICION_MAX)
    titular_nombre: str = Field("", max_length=NOMBRE_PERSONA_MAX)
    titular_cargo: str = Field("", max_length=CARGO_MAX)
    titular_telefono: Optional[str] = Field(None, max_length=TELEFONO_REQUISICION_MAX)
    titular_email: Optional[str] = Field(None, max_length=EMAIL_REQUISICION_MAX)
    coordinador_nombre: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    coordinador_telefono: Optional[str] = Field(None, max_length=TELEFONO_REQUISICION_MAX)
    coordinador_email: Optional[str] = Field(None, max_length=EMAIL_REQUISICION_MAX)
    asesor_nombre: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    asesor_telefono: Optional[str] = Field(None, max_length=TELEFONO_REQUISICION_MAX)
    asesor_email: Optional[str] = Field(None, max_length=EMAIL_REQUISICION_MAX)

    # Datos del Bien/Servicio
    tipo_contratacion: Optional[TipoContratacion] = None
    objeto_contratacion: str = ""
    lugar_entrega: str = Field("", max_length=LUGAR_ENTREGA_MAX)
    fecha_entrega_inicio: Optional[date] = None
    fecha_entrega_fin: Optional[date] = None
    condiciones_entrega: Optional[str] = None
    tipo_garantia: Optional[str] = Field(None, max_length=TIPO_GARANTIA_MAX)
    garantia_vigencia: Optional[str] = Field(None, max_length=GARANTIA_VIGENCIA_MAX)
    requisitos_proveedor: Optional[str] = None
    justificacion: str = ""
    forma_pago: Optional[str] = Field(None, max_length=FORMA_PAGO_MAX)
    requiere_anticipo: bool = False
    requiere_muestras: bool = False
    requiere_visita: bool = False

    # PDI
    pdi_eje: Optional[str] = None
    pdi_objetivo: Optional[str] = None
    pdi_estrategia: Optional[str] = None
    pdi_meta: Optional[str] = None

    # Otros
    existencia_almacen: Optional[str] = Field(None, max_length=EXISTENCIA_ALMACEN_MAX)
    observaciones: Optional[str] = None

    # Firmas (pueden venir pre-llenados desde configuración)
    validacion_asesor: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    elabora_nombre: str = Field("", max_length=NOMBRE_PERSONA_MAX)
    elabora_cargo: str = Field("", max_length=CARGO_MAX)
    solicita_nombre: str = Field("", max_length=NOMBRE_PERSONA_MAX)
    solicita_cargo: str = Field("", max_length=CARGO_MAX)

    # Items y Partidas (opcionales para borradores)
    items: List[RequisicionItemCreate] = []
    partidas: List[RequisicionPartidaCreate] = []

    @model_validator(mode='after')
    def validar_fechas_entrega(self) -> 'RequisicionCreate':
        """Valida coherencia de fechas de entrega."""
        if self.fecha_entrega_inicio and self.fecha_entrega_fin:
            if self.fecha_entrega_fin < self.fecha_entrega_inicio:
                raise ValueError(MSG_FECHA_ENTREGA_FIN_ANTERIOR)
        return self


class RequisicionUpdate(BaseModel):
    """Modelo para actualizar una requisición (todos opcionales, sin items/partidas)."""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    fecha_elaboracion: Optional[date] = None

    # Área Requirente
    dependencia_requirente: Optional[str] = Field(None, max_length=DEPENDENCIA_MAX)
    domicilio: Optional[str] = Field(None, max_length=DOMICILIO_REQUISICION_MAX)
    titular_nombre: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    titular_cargo: Optional[str] = Field(None, max_length=CARGO_MAX)
    titular_telefono: Optional[str] = Field(None, max_length=TELEFONO_REQUISICION_MAX)
    titular_email: Optional[str] = Field(None, max_length=EMAIL_REQUISICION_MAX)
    coordinador_nombre: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    coordinador_telefono: Optional[str] = Field(None, max_length=TELEFONO_REQUISICION_MAX)
    coordinador_email: Optional[str] = Field(None, max_length=EMAIL_REQUISICION_MAX)
    asesor_nombre: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    asesor_telefono: Optional[str] = Field(None, max_length=TELEFONO_REQUISICION_MAX)
    asesor_email: Optional[str] = Field(None, max_length=EMAIL_REQUISICION_MAX)

    # Datos del Bien/Servicio
    tipo_contratacion: Optional[TipoContratacion] = None
    objeto_contratacion: Optional[str] = None
    lugar_entrega: Optional[str] = Field(None, max_length=LUGAR_ENTREGA_MAX)
    fecha_entrega_inicio: Optional[date] = None
    fecha_entrega_fin: Optional[date] = None
    condiciones_entrega: Optional[str] = None
    tipo_garantia: Optional[str] = Field(None, max_length=TIPO_GARANTIA_MAX)
    garantia_vigencia: Optional[str] = Field(None, max_length=GARANTIA_VIGENCIA_MAX)
    requisitos_proveedor: Optional[str] = None
    justificacion: Optional[str] = None
    forma_pago: Optional[str] = Field(None, max_length=FORMA_PAGO_MAX)
    requiere_anticipo: Optional[bool] = None
    requiere_muestras: Optional[bool] = None
    requiere_visita: Optional[bool] = None

    # PDI
    pdi_eje: Optional[str] = None
    pdi_objetivo: Optional[str] = None
    pdi_estrategia: Optional[str] = None
    pdi_meta: Optional[str] = None

    # Otros
    existencia_almacen: Optional[str] = Field(None, max_length=EXISTENCIA_ALMACEN_MAX)
    observaciones: Optional[str] = None

    # Firmas
    validacion_asesor: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    elabora_nombre: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    elabora_cargo: Optional[str] = Field(None, max_length=CARGO_MAX)
    solicita_nombre: Optional[str] = Field(None, max_length=NOMBRE_PERSONA_MAX)
    solicita_cargo: Optional[str] = Field(None, max_length=CARGO_MAX)


# =============================================================================
# MODELOS DE RESUMEN Y ADJUDICACIÓN
# =============================================================================

class RequisicionResumen(BaseModel):
    """Vista resumida para listados."""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True,
    )

    id: int
    numero_requisicion: str
    fecha_elaboracion: date
    estado: EstadoRequisicion
    tipo_contratacion: TipoContratacion
    objeto_contratacion: str
    dependencia_requirente: str
    total_items: int = 0
    presupuesto_total: Decimal = Decimal('0')
    empresa_nombre: Optional[str] = None  # Si está adjudicada
    created_at: Optional[datetime] = None

    @classmethod
    def from_requisicion(
        cls,
        requisicion: Requisicion,
        empresa_nombre: Optional[str] = None,
    ) -> 'RequisicionResumen':
        """Factory method para crear desde una requisición completa."""
        total_items = len(requisicion.items)
        presupuesto_total = sum(
            p.presupuesto_autorizado for p in requisicion.partidas
        ) if requisicion.partidas else Decimal('0')

        return cls(
            id=requisicion.id,
            numero_requisicion=requisicion.numero_requisicion,
            fecha_elaboracion=requisicion.fecha_elaboracion,
            estado=requisicion.estado,
            tipo_contratacion=requisicion.tipo_contratacion,
            objeto_contratacion=requisicion.objeto_contratacion,
            dependencia_requirente=requisicion.dependencia_requirente,
            total_items=total_items,
            presupuesto_total=presupuesto_total,
            empresa_nombre=empresa_nombre,
            created_at=requisicion.created_at,
        )


class RequisicionAdjudicar(BaseModel):
    """Modelo para adjudicar proveedor a una requisición."""

    model_config = ConfigDict(
        validate_assignment=True,
    )

    empresa_id: int
    fecha_adjudicacion: date
