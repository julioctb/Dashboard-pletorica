"""
Entidades de dominio para Contratos.

Los contratos representan acuerdos de servicio entre empresas
proveedoras y la BUAP. Cada contrato tiene un código único
autogenerado con el formato: [EMPRESA]-[SERVICIO]-[AÑO][CONSECUTIVO]
Ejemplo: MAN-JAR-25001
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.core.enums import ModalidadAdjudicacion, TipoDuracion, EstatusContrato, TipoContrato
from app.core.validation.constants import (
    CODIGO_CONTRATO_MAX,
    FOLIO_BUAP_MAX,
    DESCRIPCION_OBJETO_MAX,
    ORIGEN_RECURSO_MAX,
    SEGMENTO_ASIGNACION_MAX,
    SEDE_CAMPUS_MAX,
    POLIZA_DETALLE_MAX,
)
from app.core.error_messages import (
    MSG_FECHA_FIN_ANTERIOR,
    MSG_TIEMPO_DETERMINADO_SIN_FIN,
    MSG_MONTO_MAX_MENOR_MIN,
    MSG_CONTRATO_YA_CANCELADO,
    MSG_SOLO_SUSPENDER_ACTIVOS,
    MSG_SOLO_VENCER_ACTIVOS,
    msg_no_puede_activar,
)

class Contrato(BaseModel):
    """
    Entidad principal de Contrato.

    Representa un acuerdo de servicio entre una empresa proveedora
    y la BUAP para un tipo de servicio específico.

    El código se genera automáticamente con el formato:
    [EMPRESA]-[SERVICIO]-[AÑO][CONSECUTIVO]
    Ejemplo: MAN-JAR-25001 (Mantiser, Jardinería, 2025, contrato 001)
    """

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True
    )

    # Identificación
    id: Optional[int] = None
    empresa_id: int = Field(description="ID de la empresa proveedora")
    tipo_servicio_id: Optional[int] = Field(
        None,
        description="ID del tipo de servicio (requerido para SERVICIOS, opcional para ADQUISICION)"
    )
    requisicion_id: Optional[int] = Field(
        None,
        description="ID de la requisicion origen. NULL solo para contratos legacy."
    )

    # Código único autogenerado
    codigo: str = Field(
        max_length=CODIGO_CONTRATO_MAX,
        description="Código único: MAN-JAR-25001"
    )

    # Folio oficial de BUAP
    numero_folio_buap: Optional[str] = Field(
        None,
        max_length=FOLIO_BUAP_MAX,
        description="Número de folio oficial asignado por BUAP"
    )
    
    # Tipo, modalidad y duración
    tipo_contrato: TipoContrato = Field(
        description="Tipo de contrato (Adquisición o Servicios)"
    )
    modalidad_adjudicacion: ModalidadAdjudicacion = Field(
        description="Modalidad de adjudicación del contrato"
    )
    tipo_duracion: Optional[TipoDuracion] = Field(
        None,
        description="Tipo de duración del contrato (requerido para SERVICIOS, no aplica para ADQUISICION)"
    )

    # Vigencia
    fecha_inicio: date = Field(description="Fecha de inicio de vigencia")
    fecha_fin: Optional[date] = Field(
        None,
        description="Fecha de fin de vigencia (null si es indefinido)"
    )
    
    # Descripción (obligatoria para nuevos contratos, pero permite NULL de BD legacy)
    descripcion_objeto: Optional[str] = Field(
        None,
        max_length=DESCRIPCION_OBJETO_MAX,
        description="Descripción del objeto del contrato (obligatorio para nuevos)"
    )
    
    # Montos
    monto_minimo: Optional[Decimal] = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Monto mínimo comprometido"
    )
    monto_maximo: Optional[Decimal] = Field(
        None,
        ge=0,
        decimal_places=2,
        description="Monto máximo autorizado"
    )
    incluye_iva: bool = Field(
        default=False,
        description="Si los montos incluyen IVA"
    )
    
    # Información adicional
    origen_recurso: Optional[str] = Field(
        None,
        max_length=ORIGEN_RECURSO_MAX,
        description="Origen del recurso (artículo de ley, subsidio, etc.)"
    )
    segmento_asignacion: Optional[str] = Field(
        None,
        max_length=SEGMENTO_ASIGNACION_MAX,
        description="Partida o segmento de BUAP"
    )
    sede_campus: Optional[str] = Field(
        None,
        max_length=SEDE_CAMPUS_MAX,
        description="Sede o campus donde aplica"
    )
    
    # Póliza de seguro
    requiere_poliza: bool = Field(
        default=False,
        description="Si requiere póliza de seguro"
    )
    poliza_detalle: Optional[str] = Field(
        None,
        max_length=POLIZA_DETALLE_MAX,
        description="Detalles de la póliza requerida"
    )
    
    # Personal
    tiene_personal: bool = Field(
        default=True,
        description="Si el contrato incluye asignación de personal"
    )
    
    # Estado
    estatus: EstatusContrato = Field(
        default=EstatusContrato.BORRADOR,
        description="Estado actual del contrato"
    )
    
    # Notas
    notas: Optional[str] = Field(
        None,
        description="Notas u observaciones generales"
    )
    
    # Auditoría
    fecha_creacion: Optional[datetime] = Field(
        None,
        description="Fecha de registro en el sistema"
    )
    fecha_actualizacion: Optional[datetime] = None

    # ==========================================
    # VALIDADORES
    # ==========================================

    @field_validator('codigo')
    @classmethod
    def validar_codigo(cls, v: str) -> str:
        """Valida y normaliza el código del contrato"""
        if v:
            v = v.upper().strip()
        return v

    @field_validator('numero_folio_buap')
    @classmethod
    def validar_folio(cls, v: Optional[str]) -> Optional[str]:
        """Valida y normaliza el folio BUAP"""
        if v:
            v = v.strip()
        return v

    @model_validator(mode='after')
    def validar_fechas_y_montos(self) -> 'Contrato':
        """Valida coherencia de fechas y montos según tipo de contrato"""
        # Validar fechas solo si hay fecha_fin
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValueError(MSG_FECHA_FIN_ANTERIOR)

        # Validar que tiempo determinado tenga fecha fin (solo si tipo_duracion está definido)
        if self.tipo_duracion == TipoDuracion.TIEMPO_DETERMINADO and not self.fecha_fin:
            raise ValueError(MSG_TIEMPO_DETERMINADO_SIN_FIN)

        # Validar montos (coherencia solo si ambos están presentes)
        if self.monto_minimo and self.monto_maximo:
            if self.monto_maximo < self.monto_minimo:
                raise ValueError(MSG_MONTO_MAX_MENOR_MIN)

        # Validaciones según tipo de contrato
        es_servicios = self.tipo_contrato == TipoContrato.SERVICIOS
        if es_servicios:
            # SERVICIOS requiere tipo_servicio_id y tipo_duracion
            if not self.tipo_servicio_id:
                raise ValueError("Tipo de servicio es requerido para contratos de servicios")
            if not self.tipo_duracion:
                raise ValueError("Tipo de duración es requerido para contratos de servicios")

        return self

    # ==========================================
    # MÉTODOS ESTÁTICOS
    # ==========================================

    @staticmethod
    def generar_codigo(
        codigo_empresa: str,
        clave_servicio: str,
        anio: int,
        consecutivo: int
    ) -> str:
        """
        Genera el código único del contrato.
        
        Args:
            codigo_empresa: Código corto de la empresa (3 letras): MAN
            clave_servicio: Clave del tipo de servicio (2-5 letras): JAR
            anio: Año del contrato: 2025
            consecutivo: Número consecutivo: 1
        
        Returns:
            Código formateado: MAN-JAR-25001
        
        Ejemplo:
            generar_codigo("MAN", "JAR", 2025, 1) → "MAN-JAR-25001"
        """
        anio_corto = str(anio)[-2:]  # 2025 → 25
        return f"{codigo_empresa.upper()}-{clave_servicio.upper()}-{anio_corto}{consecutivo:03d}"

    # ==========================================
    # MÉTODOS DE NEGOCIO
    # ==========================================

    def esta_activo(self) -> bool:
        """Verifica si el contrato está activo"""
        return self.estatus == EstatusContrato.ACTIVO

    def esta_vigente(self) -> bool:
        """Verifica si el contrato está vigente (activo y dentro de fechas)"""
        if not self.esta_activo():
            return False
        
        hoy = date.today()
        if hoy < self.fecha_inicio:
            return False
        if self.fecha_fin and hoy > self.fecha_fin:
            return False
        
        return True

    def puede_tener_plazas(self) -> bool:
        """Verifica si el contrato puede tener plazas asignadas"""
        return self.tiene_personal and self.estatus in [
            EstatusContrato.BORRADOR,
            EstatusContrato.ACTIVO
        ]

    def puede_activarse(self) -> bool:
        """Verifica si el contrato puede cambiar a estado ACTIVO"""
        return self.estatus == EstatusContrato.BORRADOR

    def puede_modificarse(self) -> bool:
        """Verifica si el contrato puede ser modificado"""
        return self.estatus in [
            EstatusContrato.BORRADOR,
            EstatusContrato.ACTIVO,
            EstatusContrato.SUSPENDIDO
        ]

    def activar(self) -> None:
        """Activa el contrato"""
        if not self.puede_activarse():
            raise ValueError(msg_no_puede_activar(self.estatus))
        self.estatus = EstatusContrato.ACTIVO

    def suspender(self) -> None:
        """Suspende el contrato"""
        if self.estatus != EstatusContrato.ACTIVO:
            raise ValueError(MSG_SOLO_SUSPENDER_ACTIVOS)
        self.estatus = EstatusContrato.SUSPENDIDO

    def cancelar(self) -> None:
        """Cancela el contrato"""
        if self.estatus == EstatusContrato.CANCELADO:
            raise ValueError(MSG_CONTRATO_YA_CANCELADO)
        self.estatus = EstatusContrato.CANCELADO

    def marcar_vencido(self) -> None:
        """Marca el contrato como vencido"""
        if self.estatus != EstatusContrato.ACTIVO:
            raise ValueError(MSG_SOLO_VENCER_ACTIVOS)
        self.estatus = EstatusContrato.VENCIDO

    def get_monto_con_iva(self, monto: Decimal, tasa_iva: Decimal = Decimal('0.16')) -> Decimal:
        """Calcula el monto con IVA si no lo incluye"""
        if self.incluye_iva:
            return monto
        return monto * (1 + tasa_iva)

    def __str__(self) -> str:
        return f"{self.codigo} - {self.estatus}"


class ContratoCreate(BaseModel):
    """Modelo para crear un nuevo contrato"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    empresa_id: int
    tipo_servicio_id: Optional[int] = None  # Opcional para ADQUISICION
    requisicion_id: Optional[int] = None
    codigo: str = Field(max_length=CODIGO_CONTRATO_MAX)
    numero_folio_buap: Optional[str] = Field(None, max_length=FOLIO_BUAP_MAX)
    tipo_contrato: TipoContrato
    modalidad_adjudicacion: ModalidadAdjudicacion
    tipo_duracion: Optional[TipoDuracion] = None  # Opcional para ADQUISICION
    fecha_inicio: date
    fecha_fin: Optional[date] = None
    descripcion_objeto: str = Field(..., min_length=1, max_length=DESCRIPCION_OBJETO_MAX)  # Obligatorio
    monto_minimo: Optional[Decimal] = Field(None, ge=0)
    monto_maximo: Optional[Decimal] = Field(None, ge=0)
    incluye_iva: bool = False
    origen_recurso: Optional[str] = Field(None, max_length=ORIGEN_RECURSO_MAX)
    segmento_asignacion: Optional[str] = Field(None, max_length=SEGMENTO_ASIGNACION_MAX)
    sede_campus: Optional[str] = Field(None, max_length=SEDE_CAMPUS_MAX)
    requiere_poliza: bool = False
    poliza_detalle: Optional[str] = Field(None, max_length=POLIZA_DETALLE_MAX)
    tiene_personal: bool = True
    estatus: EstatusContrato = Field(default=EstatusContrato.BORRADOR)
    notas: Optional[str] = None


class ContratoUpdate(BaseModel):
    """Modelo para actualizar un contrato existente (todos los campos opcionales)"""

    model_config = ConfigDict(
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    empresa_id: Optional[int] = None
    tipo_servicio_id: Optional[int] = None
    requisicion_id: Optional[int] = None
    numero_folio_buap: Optional[str] = Field(None, max_length=FOLIO_BUAP_MAX)
    tipo_contrato: Optional[TipoContrato] = None
    modalidad_adjudicacion: Optional[ModalidadAdjudicacion] = None
    tipo_duracion: Optional[TipoDuracion] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    descripcion_objeto: Optional[str] = Field(None, max_length=DESCRIPCION_OBJETO_MAX)
    monto_minimo: Optional[Decimal] = Field(None, ge=0)
    monto_maximo: Optional[Decimal] = Field(None, ge=0)
    incluye_iva: Optional[bool] = None
    origen_recurso: Optional[str] = Field(None, max_length=ORIGEN_RECURSO_MAX)
    segmento_asignacion: Optional[str] = Field(None, max_length=SEGMENTO_ASIGNACION_MAX)
    sede_campus: Optional[str] = Field(None, max_length=SEDE_CAMPUS_MAX)
    requiere_poliza: Optional[bool] = None
    poliza_detalle: Optional[str] = Field(None, max_length=POLIZA_DETALLE_MAX)
    tiene_personal: Optional[bool] = None
    estatus: Optional[EstatusContrato] = None
    notas: Optional[str] = None


class ContratoResumen(BaseModel):
    """Modelo resumido de contrato para listados"""

    model_config = ConfigDict(
        use_enum_values=True,
        from_attributes=True
    )

    id: int
    codigo: str
    numero_folio_buap: Optional[str]
    empresa_id: int
    tipo_servicio_id: Optional[int]  # Opcional para ADQUISICION
    tipo_contrato: TipoContrato
    modalidad_adjudicacion: ModalidadAdjudicacion
    tipo_duracion: Optional[TipoDuracion]  # Opcional para ADQUISICION
    fecha_inicio: date
    fecha_fin: Optional[date]
    monto_minimo: Optional[Decimal]
    monto_maximo: Optional[Decimal]
    tiene_personal: bool
    estatus: EstatusContrato
    fecha_creacion: Optional[datetime]
    descripcion_objeto: Optional[str] = None

    # Campos de requisicion origen
    requisicion_id: Optional[int] = None
    numero_requisicion: Optional[str] = None

    # Campos calculados/join (se llenan desde el servicio)
    nombre_empresa: Optional[str] = None
    nombre_servicio: Optional[str] = None

    @classmethod
    def from_contrato(cls, contrato: Contrato) -> 'ContratoResumen':
        """Factory method para crear desde un contrato completo"""
        return cls(
            id=contrato.id,
            codigo=contrato.codigo,
            numero_folio_buap=contrato.numero_folio_buap,
            empresa_id=contrato.empresa_id,
            tipo_servicio_id=contrato.tipo_servicio_id,
            tipo_contrato=contrato.tipo_contrato,
            modalidad_adjudicacion=contrato.modalidad_adjudicacion,
            tipo_duracion=contrato.tipo_duracion,
            fecha_inicio=contrato.fecha_inicio,
            fecha_fin=contrato.fecha_fin,
            monto_minimo=contrato.monto_minimo,
            monto_maximo=contrato.monto_maximo,
            tiene_personal=contrato.tiene_personal,
            estatus=contrato.estatus,
            fecha_creacion=contrato.fecha_creacion,
            descripcion_objeto=contrato.descripcion_objeto,
            requisicion_id=contrato.requisicion_id,
        )