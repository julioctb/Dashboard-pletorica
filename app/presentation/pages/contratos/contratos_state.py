"""
Estado de Reflex para el módulo de Contratos.
Maneja el estado de la UI y las operaciones del módulo.

Refactorizado para usar:
- CRUDStateMixin para operaciones CRUD genéricas
- ui_helpers para opciones de enums
"""
import reflex as rx
from typing import List, Optional, Callable
from decimal import Decimal, InvalidOperation
from datetime import date

from app.presentation.components.shared.base_state import BaseState
from app.presentation.components.shared.crud_state_mixin import CRUDStateMixin
from app.core.ui_helpers import (
    FILTRO_TODOS,
    FILTRO_SIN_SELECCION,
    opciones_desde_enum,
)
from app.services import contrato_service, empresa_service, tipo_servicio_service, categoria_puesto_service, entregable_service, requisicion_service
from app.core.text_utils import normalizar_mayusculas, formatear_moneda, formatear_fecha

from app.entities import (
    ContratoCreate,
    ContratoUpdate,
    EstatusContrato,
    ModalidadAdjudicacion,
    TipoDuracion,
    TipoContrato,
)
from app.core.enums import TipoContratacion, EstadoRequisicion
from app.entities.contrato_item import ContratoItemCreate
from app.core.enums import TipoEntregable, PeriodicidadEntregable
from app.entities.entregable import ContratoTipoEntregableCreate

from app.core.exceptions import (
    DuplicateError,
    DatabaseError,
    BusinessRuleError,
)

from .contratos_validators import (
    validar_folio_buap,
    validar_descripcion_objeto,
    validar_origen_recurso,
    validar_segmento_asignacion,
    validar_sede_campus,
    validar_poliza_detalle,
    validar_empresa_id,
    validar_tipo_servicio_id,
    validar_modalidad_adjudicacion,
    validar_tipo_duracion,
    validar_tipo_contrato,
    validar_fecha_inicio,
    validar_fecha_fin,
    validar_monto_minimo,
    validar_monto_maximo,
    validar_montos_coherentes,
)


# ============================================================================
# CONFIGURACIÓN DE CAMPOS VALIDABLES
# ============================================================================
CAMPOS_VALIDACION: dict[str, Callable[[str], str]] = {
    # "codigo" se excluye porque es autogenerado
    "folio_buap": validar_folio_buap,
    "descripcion_objeto": validar_descripcion_objeto,
    "origen_recurso": validar_origen_recurso,
    "segmento_asignacion": validar_segmento_asignacion,
    "sede_campus": validar_sede_campus,
    "poliza_detalle": validar_poliza_detalle,
    "monto_minimo": validar_monto_minimo,
    "monto_maximo": validar_monto_maximo,
}

# Campos con sus valores por defecto para limpiar formulario
FORM_DEFAULTS = {
    "empresa_id": "",
    "tipo_servicio_id": "",
    "categoria_puesto_id": "",
    "codigo": "",
    "folio_buap": "",
    "tipo_contrato": "",
    "modalidad_adjudicacion": "",
    "tipo_duracion": "",
    "fecha_inicio": "",
    "fecha_fin": "",
    "descripcion_objeto": "",
    "monto_minimo": "",
    "monto_maximo": "",
    "incluye_iva": True,
    "origen_recurso": "",
    "segmento_asignacion": "",
    "sede_campus": "",
    "requiere_poliza": False,
    "poliza_detalle": "",
    "tiene_personal": True,
    "estatus": EstatusContrato.BORRADOR.value,
    "notas": "",
    "requisicion_id": "",
    "numero_requisicion": "",
}


class ContratosState(BaseState, CRUDStateMixin):
    """Estado para el módulo de Contratos"""

    # ========================
    # CONFIGURACIÓN DEL MIXIN
    # ========================
    _entidad_nombre: str = "Contrato"
    _modal_principal: str = "mostrar_modal_contrato"
    _campos_error: List[str] = [
        "empresa_id", "tipo_servicio_id", "codigo", "folio_buap",
        "tipo_contrato", "modalidad_adjudicacion", "tipo_duracion",
        "fecha_inicio", "fecha_fin", "descripcion_objeto",
        "monto_minimo", "monto_maximo", "origen_recurso",
        "segmento_asignacion", "sede_campus", "poliza_detalle"
    ]

    # ========================
    # ESTADO DE DATOS
    # ========================
    contratos: List[dict] = []
    contrato_seleccionado: Optional[dict] = None
    total_contratos: int = 0

    # Listas para dropdowns
    empresas: List[dict] = []
    tipos_servicio: List[dict] = []
    categorias_puesto: List[dict] = []
    cargando_categorias_puesto: bool = False

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_contrato: bool = False
    mostrar_modal_detalle: bool = False
    mostrar_modal_confirmar_cancelar: bool = False
    es_edicion: bool = False

    # Entregables del contrato seleccionado (para modal detalle)
    entregables_contrato: List[dict] = []
    cargando_entregables: bool = False

    # ========================
    # ESTADO DE VISTA (tabla/cards)
    # ========================
    view_mode: str = "table"

    # ========================
    # FILTROS
    # ========================
    filtro_empresa_id: str = FILTRO_SIN_SELECCION
    filtro_tipo_servicio_id: str = FILTRO_SIN_SELECCION
    filtro_estatus: str = FILTRO_TODOS
    filtro_modalidad: str = ""
    filtro_fecha_desde: str = ""
    filtro_fecha_hasta: str = ""
    incluir_inactivos: bool = False

    # ========================
    # ESTADO DEL FORMULARIO
    # ========================
    form_empresa_id: str = ""
    form_tipo_servicio_id: str = ""
    form_categoria_puesto_id: str = ""
    form_codigo: str = ""
    form_folio_buap: str = ""
    form_tipo_contrato: str = ""
    form_modalidad_adjudicacion: str = ""
    form_tipo_duracion: str = ""
    form_fecha_inicio: str = ""
    form_fecha_fin: str = ""
    form_descripcion_objeto: str = ""
    form_monto_minimo: str = ""
    form_monto_maximo: str = ""
    form_incluye_iva: bool = True
    form_origen_recurso: str = ""
    form_segmento_asignacion: str = ""
    form_sede_campus: str = ""
    form_requiere_poliza: bool = False
    form_poliza_detalle: str = ""
    form_tiene_personal: bool = True
    form_estatus: str = EstatusContrato.BORRADOR.value
    form_notas: str = ""

    # Requisicion origen (pre-llenado desde flujo Req -> Contrato)
    form_requisicion_id: str = ""
    form_numero_requisicion: str = ""  # Solo display, no editable
    form_contrato_items: List[dict] = []  # Items para ADQUISICION

    # ========================
    # CONFIGURACIÓN DE ENTREGABLES
    # ========================
    config_entregables: List[dict] = []  # Lista de tipos de entregable configurados
    form_tipo_entregable: str = ""
    form_periodicidad_entregable: str = PeriodicidadEntregable.MENSUAL.value
    form_entregable_requerido: bool = True
    form_entregable_descripcion: str = ""
    form_entregable_instrucciones: str = ""

    # ========================
    # ERRORES DE VALIDACIÓN
    # ========================
    error_empresa_id: str = ""
    error_tipo_servicio_id: str = ""
    error_codigo: str = ""
    error_folio_buap: str = ""
    error_tipo_contrato: str = ""
    error_modalidad_adjudicacion: str = ""
    error_tipo_duracion: str = ""
    error_fecha_inicio: str = ""
    error_fecha_fin: str = ""
    error_descripcion_objeto: str = ""
    error_monto_minimo: str = ""
    error_monto_maximo: str = ""
    error_origen_recurso: str = ""
    error_segmento_asignacion: str = ""
    error_sede_campus: str = ""
    error_poliza_detalle: str = ""

    # ========================
    # SETTERS (Reflex 0.8.9+)
    # Usa helpers para reducir código repetitivo donde sea posible
    # ========================

    # --- Filtros (retornan callback para recargar datos) ---
    def set_filtro_empresa_id(self, value: str):
        self.filtro_empresa_id = value if value else FILTRO_SIN_SELECCION
        return ContratosState.cargar_contratos

    def set_filtro_tipo_servicio_id(self, value: str):
        self.filtro_tipo_servicio_id = value if value else FILTRO_SIN_SELECCION
        return ContratosState.cargar_contratos

    def set_filtro_estatus(self, value: str):
        self.filtro_estatus = value
        return ContratosState.cargar_contratos

    def set_filtro_modalidad(self, value: str):
        self.filtro_modalidad = value
        return ContratosState.cargar_contratos

    def set_incluir_inactivos(self, value: bool):
        self.incluir_inactivos = value
        return ContratosState.cargar_contratos

    def set_filtro_fecha_desde(self, value: str):
        self.filtro_fecha_desde = value if value else ""
        return ContratosState.cargar_contratos

    def set_filtro_fecha_hasta(self, value: str):
        self.filtro_fecha_hasta = value if value else ""
        return ContratosState.cargar_contratos

    # --- Vista (tabla/cards) ---
    def set_view_table(self):
        self.view_mode = "table"

    def set_view_cards(self):
        self.view_mode = "cards"

    def toggle_view(self):
        self.view_mode = "cards" if self.view_mode == "table" else "table"

    @rx.var
    def is_table_view(self) -> bool:
        return self.view_mode == "table"

    @rx.var
    def is_cards_view(self) -> bool:
        return self.view_mode == "cards"

    # --- Formulario: setters simples ---
    def set_form_empresa_id(self, value):
        self.form_empresa_id = value if value else ""

    def set_form_tipo_servicio_id(self, value):
        self.form_tipo_servicio_id = value if value else ""
        # Limpiar categoría seleccionada al cambiar tipo de servicio
        self.form_categoria_puesto_id = ""
        self.categorias_puesto = []
        # Cargar categorías del nuevo tipo de servicio
        if value:
            return ContratosState.cargar_categorias_puesto

    def set_form_categoria_puesto_id(self, value):
        self.form_categoria_puesto_id = value if value else ""

    def set_form_codigo(self, value):
        self.form_codigo = normalizar_mayusculas(value) if value else ""

    def set_form_folio_buap(self, value):
        self.form_folio_buap = value if value else ""

    def set_form_modalidad_adjudicacion(self, value):
        self.form_modalidad_adjudicacion = value if value else ""

    def set_form_fecha_inicio(self, value):
        self.form_fecha_inicio = value if value else ""

    def set_form_fecha_fin(self, value):
        self.form_fecha_fin = value if value else ""

    def set_form_descripcion_objeto(self, value):
        self.form_descripcion_objeto = value if value else ""

    def set_form_incluye_iva(self, value):
        self.form_incluye_iva = bool(value)

    def set_form_origen_recurso(self, value):
        self.form_origen_recurso = value if value else ""

    def set_form_segmento_asignacion(self, value):
        self.form_segmento_asignacion = value if value else ""

    def set_form_sede_campus(self, value):
        self.form_sede_campus = value if value else ""

    def set_form_requiere_poliza(self, value):
        self.form_requiere_poliza = bool(value)

    def set_form_poliza_detalle(self, value):
        self.form_poliza_detalle = value if value else ""

    def set_form_tiene_personal(self, value):
        self.form_tiene_personal = bool(value)

    def set_form_estatus(self, value):
        self.form_estatus = value if value else ""

    def set_form_notas(self, value):
        self.form_notas = value if value else ""

    # --- Configuración de entregables ---
    def set_form_tipo_entregable(self, value):
        self.form_tipo_entregable = value if value else ""

    def set_form_periodicidad_entregable(self, value):
        self.form_periodicidad_entregable = value if value else PeriodicidadEntregable.MENSUAL.value

    def set_form_entregable_requerido(self, value):
        self.form_entregable_requerido = bool(value)

    def set_form_entregable_descripcion(self, value):
        self.form_entregable_descripcion = value if value else ""

    def set_form_entregable_instrucciones(self, value):
        self.form_entregable_instrucciones = value if value else ""

    # --- Formulario: setters con lógica de negocio (mantener explícitos) ---
    def set_form_tipo_contrato(self, value):
        self.form_tipo_contrato = value if value else ""
        # Auto-configurar campos según tipo de contrato
        if value == TipoContrato.ADQUISICION.value:
            # ADQUISICION: no lleva tipo servicio, tipo duración, ni personal
            self.form_tipo_servicio_id = ""
            self.form_tipo_duracion = ""
            self.form_tiene_personal = False
            self.form_monto_minimo = ""  # Solo monto máximo
            self.form_fecha_fin = ""  # No aplica fecha fin
            # Limpiar errores relacionados
            self.error_tipo_servicio_id = ""
            self.error_tipo_duracion = ""
            self.error_fecha_fin = ""
            self.error_monto_minimo = ""
        elif value == TipoContrato.SERVICIOS.value:
            # SERVICIOS: restaurar defaults
            self.form_tiene_personal = True

    def set_form_tipo_duracion(self, value):
        self.form_tipo_duracion = value if value else ""
        # Si es tiempo indefinido u obra determinada, limpiar fecha fin
        if value in [TipoDuracion.TIEMPO_INDEFINIDO.value, TipoDuracion.OBRA_DETERMINADA.value]:
            self.form_fecha_fin = ""
            self.error_fecha_fin = ""

    def set_form_monto_minimo(self, value: str):
        self.form_monto_minimo = formatear_moneda(value)
        self._auto_set_poliza()

    def set_form_monto_maximo(self, value: str):
        self.form_monto_maximo = formatear_moneda(value)
        self._auto_set_poliza()

    def _auto_set_poliza(self):
        """Auto-activa póliza si es SERVICIOS y tiene ambos montos"""
        if self.form_tipo_contrato == TipoContrato.SERVICIOS.value:
            tiene_min = bool(self.form_monto_minimo and self.form_monto_minimo.strip())
            tiene_max = bool(self.form_monto_maximo and self.form_monto_maximo.strip())
            if tiene_min and tiene_max:
                self.form_requiere_poliza = True

    # --- Contrato Items ---
    def actualizar_contrato_item_campo(self, index: int, campo: str, valor):
        """Actualiza un campo de un item de contrato."""
        items = list(self.form_contrato_items)
        if 0 <= index < len(items):
            item = dict(items[index])
            item[campo] = valor
            items[index] = item
            self.form_contrato_items = items

    # --- Modales ---
    def set_mostrar_modal_contrato(self, value: bool):
        self.mostrar_modal_contrato = value

    def set_mostrar_modal_detalle(self, value: bool):
        self.mostrar_modal_detalle = value

    def set_mostrar_modal_confirmar_cancelar(self, value: bool):
        self.mostrar_modal_confirmar_cancelar = value

    # ========================
    # VALIDACIÓN EN TIEMPO REAL
    # ========================
    def validar_empresa_id_campo(self):
        self.error_empresa_id = validar_empresa_id(self.form_empresa_id)

    def validar_tipo_servicio_id_campo(self):
        self.error_tipo_servicio_id = validar_tipo_servicio_id(self.form_tipo_servicio_id)

    def validar_modalidad_campo(self):
        self.error_modalidad_adjudicacion = validar_modalidad_adjudicacion(self.form_modalidad_adjudicacion)

    def validar_tipo_duracion_campo(self):
        self.error_tipo_duracion = validar_tipo_duracion(self.form_tipo_duracion)

    def validar_tipo_contrato_campo(self):
        self.error_tipo_contrato = validar_tipo_contrato(self.form_tipo_contrato)

    def validar_fecha_inicio_campo(self):
        self.error_fecha_inicio = validar_fecha_inicio(self.form_fecha_inicio)

    def validar_fecha_fin_campo(self):
        self.error_fecha_fin = validar_fecha_fin(
            self.form_fecha_fin,
            self.form_fecha_inicio,
            self.form_tipo_duracion
        )

    def validar_monto_minimo_campo(self):
        self.error_monto_minimo = validar_monto_minimo(self.form_monto_minimo)

    def validar_monto_maximo_campo(self):
        self.error_monto_maximo = validar_monto_maximo(self.form_monto_maximo)
        # También validar coherencia
        if not self.error_monto_maximo:
            self.error_monto_maximo = validar_montos_coherentes(
                self.form_monto_minimo,
                self.form_monto_maximo
            )

    def validar_descripcion_objeto_campo(self):
        """Valida descripción del objeto (obligatorio)"""
        if not self.form_descripcion_objeto or not self.form_descripcion_objeto.strip():
            self.error_descripcion_objeto = "La descripción del objeto es obligatoria"
        else:
            self.error_descripcion_objeto = validar_descripcion_objeto(self.form_descripcion_objeto)

    def _validar_campo(self, campo: str):
        """Valida un campo usando el diccionario de validadores"""
        if campo in CAMPOS_VALIDACION:
            valor = getattr(self, f"form_{campo}")
            error = CAMPOS_VALIDACION[campo](valor)
            setattr(self, f"error_{campo}", error)

    def _validar_todos_los_campos(self):
        """Valida todos los campos del formulario con lógica condicional"""
        # Limpiar todos los errores primero
        self._limpiar_errores()

        # Campos siempre requeridos
        self.validar_empresa_id_campo()
        self.validar_tipo_contrato_campo()
        self.validar_modalidad_campo()
        self.validar_fecha_inicio_campo()
        self.validar_descripcion_objeto_campo()  # Ahora es obligatorio

        # Validaciones condicionales según tipo de contrato
        es_servicios = self.form_tipo_contrato == TipoContrato.SERVICIOS.value
        es_adquisicion = self.form_tipo_contrato == TipoContrato.ADQUISICION.value

        if es_servicios:
            # SERVICIOS: requiere tipo_servicio y tipo_duracion
            self.validar_tipo_servicio_id_campo()
            self.validar_tipo_duracion_campo()

            # Si es tiempo determinado, requiere fecha_fin
            if self.form_tipo_duracion == TipoDuracion.TIEMPO_DETERMINADO.value:
                self.validar_fecha_fin_campo()

            # Validar monto mínimo solo para servicios
            self._validar_campo("monto_minimo")

        # Validar monto máximo siempre (aplica a ambos tipos)
        self._validar_campo("monto_maximo")

        # Validar coherencia de montos solo si es servicios y tiene ambos
        if es_servicios and self.form_monto_minimo and self.form_monto_maximo:
            error_coherencia = validar_montos_coherentes(
                self.form_monto_minimo,
                self.form_monto_maximo
            )
            if error_coherencia and not self.error_monto_maximo:
                self.error_monto_maximo = error_coherencia

        # Validar campos opcionales del diccionario
        for campo in ["folio_buap", "origen_recurso", "segmento_asignacion", "sede_campus", "poliza_detalle"]:
            self._validar_campo(campo)

    @rx.var
    def tiene_errores_formulario(self) -> bool:
        """Verifica si hay errores de validación (considera condicionales)"""
        # Errores de campos del diccionario
        errores_campos = any(
            getattr(self, f"error_{campo}", "")
            for campo in CAMPOS_VALIDACION
        )

        # Errores de selects y campos requeridos
        errores_basicos = bool(
            self.error_empresa_id or
            self.error_tipo_contrato or
            self.error_modalidad_adjudicacion or
            self.error_fecha_inicio or
            self.error_descripcion_objeto
        )

        # Errores condicionales según tipo de contrato
        es_servicios = self.form_tipo_contrato == TipoContrato.SERVICIOS.value
        errores_servicios = False
        if es_servicios:
            errores_servicios = bool(
                self.error_tipo_servicio_id or
                self.error_tipo_duracion or
                self.error_fecha_fin
            )

        return errores_campos or errores_basicos or errores_servicios

    @rx.var
    def puede_guardar(self) -> bool:
        """Verifica si se puede guardar el formulario"""
        # Campos siempre requeridos
        tiene_basicos = bool(
            self.form_empresa_id and
            self.form_tipo_contrato and
            self.form_modalidad_adjudicacion and
            self.form_fecha_inicio and
            self.form_descripcion_objeto.strip()  # Ahora es obligatorio
        )

        # Campos condicionales según tipo de contrato
        if self.form_tipo_contrato == TipoContrato.SERVICIOS.value:
            tiene_servicios = bool(
                self.form_tipo_servicio_id and
                self.form_tipo_duracion
            )
            # Si es tiempo determinado, requiere fecha fin
            if self.form_tipo_duracion == TipoDuracion.TIEMPO_DETERMINADO.value:
                tiene_servicios = tiene_servicios and bool(self.form_fecha_fin)
        else:
            # ADQUISICION no requiere tipo_servicio ni tipo_duracion
            tiene_servicios = True

        return tiene_basicos and tiene_servicios and not self.tiene_errores_formulario and not self.saving

    @rx.var
    def tiene_filtros_activos(self) -> bool:
        """Indica si hay algún filtro aplicado"""
        return (
            self.filtro_empresa_id != FILTRO_SIN_SELECCION or
            self.filtro_tipo_servicio_id != FILTRO_SIN_SELECCION or
            (self.filtro_estatus != FILTRO_TODOS and bool(self.filtro_estatus)) or
            bool(self.filtro_modalidad) or
            bool(self.filtro_fecha_desde) or
            bool(self.filtro_fecha_hasta) or
            bool(self.filtro_busqueda.strip()) or
            self.incluir_inactivos
        )

    @rx.var
    def mostrar_tabla(self) -> bool:
        """Muestra tabla si hay contratos O si hay filtro activo"""
        return self.total_contratos > 0 or bool(self.filtro_busqueda.strip())

    @rx.var
    def opciones_empresa(self) -> List[dict]:
        """Opciones formateadas para el select de empresa"""
        return [{"value": str(e["id"]), "label": f"{e['codigo_corto']} - {e['nombre_comercial']}"} for e in self.empresas]

    @rx.var
    def opciones_tipo_servicio(self) -> List[dict]:
        """Opciones formateadas para el select de tipo de servicio"""
        return [{"value": str(t["id"]), "label": f"{t['clave']} - {t['nombre']}"} for t in self.tipos_servicio]

    @rx.var
    def opciones_categoria_puesto(self) -> List[dict]:
        """Opciones formateadas para el select de categoría de puesto"""
        return [{"value": str(c["id"]), "label": f"{c['clave']} - {c['nombre']}"} for c in self.categorias_puesto]

    @rx.var
    def opciones_modalidad(self) -> List[dict]:
        """Opciones para el select de modalidad de adjudicación"""
        return opciones_desde_enum(ModalidadAdjudicacion)

    @rx.var
    def opciones_tipo_duracion(self) -> List[dict]:
        """Opciones para el select de tipo de duración"""
        return opciones_desde_enum(TipoDuracion)

    @rx.var
    def opciones_tipo_contrato(self) -> List[dict]:
        """Opciones para el select de tipo de contrato"""
        return opciones_desde_enum(TipoContrato)

    # ========================
    # VARS CONDICIONALES DE NEGOCIO
    # ========================
    @rx.var
    def es_adquisicion(self) -> bool:
        """True si el tipo de contrato es ADQUISICION"""
        return self.form_tipo_contrato == TipoContrato.ADQUISICION.value

    @rx.var
    def es_servicios(self) -> bool:
        """True si el tipo de contrato es SERVICIOS"""
        return self.form_tipo_contrato == TipoContrato.SERVICIOS.value

    @rx.var
    def es_tiempo_determinado(self) -> bool:
        """True si el tipo de duración es TIEMPO_DETERMINADO"""
        return self.form_tipo_duracion == TipoDuracion.TIEMPO_DETERMINADO.value

    @rx.var
    def requiere_tipo_servicio(self) -> bool:
        """Tipo de servicio solo es requerido para SERVICIOS"""
        return self.es_servicios

    @rx.var
    def requiere_tipo_duracion(self) -> bool:
        """Tipo de duración solo es requerido para SERVICIOS"""
        return self.es_servicios

    @rx.var
    def requiere_fecha_fin(self) -> bool:
        """Fecha fin solo es requerida si es TIEMPO_DETERMINADO"""
        return self.es_tiempo_determinado

    @rx.var
    def muestra_monto_minimo(self) -> bool:
        """Monto mínimo solo aplica para SERVICIOS"""
        return self.es_servicios

    @rx.var
    def muestra_tiene_personal(self) -> bool:
        """Tiene personal solo aplica para SERVICIOS"""
        return self.es_servicios

    @rx.var
    def requiere_poliza_auto(self) -> bool:
        """
        Póliza es requerida automáticamente si:
        - Es SERVICIOS y tiene ambos montos (mínimo y máximo)
        """
        if not self.es_servicios:
            return False
        tiene_monto_min = bool(self.form_monto_minimo and self.form_monto_minimo.strip())
        tiene_monto_max = bool(self.form_monto_maximo and self.form_monto_maximo.strip())
        return tiene_monto_min and tiene_monto_max

    @rx.var
    def opciones_estatus(self) -> List[dict]:
        """Opciones para el select de estatus"""
        return opciones_desde_enum(EstatusContrato)

    @rx.var
    def opciones_tipo_entregable(self) -> List[dict]:
        """Opciones para el select de tipo de entregable"""
        return opciones_desde_enum(TipoEntregable)

    @rx.var
    def opciones_periodicidad_entregable(self) -> List[dict]:
        """Opciones para el select de periodicidad"""
        return opciones_desde_enum(PeriodicidadEntregable)

    @rx.var
    def tiene_config_entregables(self) -> bool:
        """True si hay tipos de entregable configurados"""
        return len(self.config_entregables) > 0

    @rx.var
    def puede_agregar_entregable(self) -> bool:
        """True si se puede agregar un tipo de entregable"""
        return bool(self.form_tipo_entregable)

    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def cargar_datos_iniciales(self):
        """Cargar empresas, tipos de servicio y contratos"""
        async for _ in self.montar_pagina(
            self.cargar_empresas,
            self.cargar_tipos_servicio,
            self._fetch_contratos,
        ):
            yield

    async def cargar_empresas(self):
        """Cargar empresas para el dropdown"""
        try:
            from app.services import empresa_service
            empresas = await empresa_service.obtener_todas(incluir_inactivas=False)
            self.empresas = [e.model_dump() for e in empresas]
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar empresas: {str(e)}", "error")
            self.empresas = []

    async def cargar_tipos_servicio(self):
        """Cargar tipos de servicio para el dropdown"""
        try:
            tipos = await tipo_servicio_service.obtener_activas()
            self.tipos_servicio = [t.model_dump() for t in tipos]
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar tipos de servicio: {str(e)}", "error")
            self.tipos_servicio = []

    async def cargar_categorias_puesto(self):
        """Cargar categorías de puesto según el tipo de servicio seleccionado"""
        if not self.form_tipo_servicio_id:
            self.categorias_puesto = []
            return
        self.cargando_categorias_puesto = True
        try:
            tipo_servicio_id = self.parse_id(self.form_tipo_servicio_id)
            categorias = await categoria_puesto_service.obtener_por_tipo_servicio(
                tipo_servicio_id,
                incluir_inactivas=False
            )
            self.categorias_puesto = [c.model_dump() for c in categorias]
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar categorías: {str(e)}", "error")
            self.categorias_puesto = []
        finally:
            self.cargando_categorias_puesto = False

    async def _fetch_contratos(self):
        """Carga la lista de contratos con filtros (sin manejo de loading)."""
        try:
            # Preparar filtros
            empresa_id = int(self.filtro_empresa_id) if self.filtro_empresa_id != FILTRO_SIN_SELECCION else None
            tipo_servicio_id = int(self.filtro_tipo_servicio_id) if self.filtro_tipo_servicio_id != FILTRO_SIN_SELECCION else None

            # Preparar filtros de fecha
            fecha_desde = None
            fecha_hasta = None
            if self.filtro_fecha_desde:
                fecha_desde = date.fromisoformat(self.filtro_fecha_desde)
            if self.filtro_fecha_hasta:
                fecha_hasta = date.fromisoformat(self.filtro_fecha_hasta)

            contratos = await contrato_service.buscar_con_filtros(
                texto=self.filtro_busqueda or None,
                empresa_id=empresa_id,
                tipo_servicio_id=tipo_servicio_id,
                estatus=None if self.filtro_estatus == FILTRO_TODOS else (self.filtro_estatus or None),
                modalidad=self.filtro_modalidad or None,
                fecha_inicio_desde=fecha_desde,
                fecha_inicio_hasta=fecha_hasta,
                incluir_inactivos=self.incluir_inactivos,
                limite=100,
                offset=0
            )

            # Obtener saldos pendientes en batch (1 query en lugar de N)
            contratos_info = [
                {"id": c.id, "monto_maximo": c.monto_maximo}
                for c in contratos
            ]
            try:
                saldos_pendientes = await pago_service.obtener_saldos_pendientes_batch(contratos_info)
            except Exception:
                saldos_pendientes = {}

            # Enriquecer con nombres de empresa, tipo de servicio y saldos
            self.contratos = []
            for c in contratos:
                contrato_dict = c.model_dump()
                # Buscar nombre de empresa
                for e in self.empresas:
                    if e["id"] == c.empresa_id:
                        contrato_dict["nombre_empresa"] = e["nombre_comercial"]
                        break
                # Buscar nombre de tipo de servicio
                for t in self.tipos_servicio:
                    if t["id"] == c.tipo_servicio_id:
                        contrato_dict["nombre_servicio"] = t["nombre"]
                        break
                # Formatear fechas para mostrar en la tabla
                contrato_dict["fecha_inicio_fmt"] = formatear_fecha(c.fecha_inicio)
                contrato_dict["fecha_fin_fmt"] = formatear_fecha(c.fecha_fin)
                # Formatear monto máximo como moneda
                contrato_dict["monto_maximo_fmt"] = formatear_moneda(str(c.monto_maximo)) if c.monto_maximo else "-"

                # Obtener saldo pendiente del batch (ya calculado)
                saldo = saldos_pendientes.get(c.id)
                contrato_dict["saldo_pendiente_fmt"] = formatear_moneda(str(saldo)) if saldo is not None else "-"

                self.contratos.append(contrato_dict)

            # Filtro adicional por nombre de empresa (búsqueda in-memory)
            if self.filtro_busqueda and self.filtro_busqueda.strip():
                termino = self.filtro_busqueda.strip().lower()
                self.contratos = [
                    c for c in self.contratos
                    if (
                        termino in c.get("codigo", "").lower() or
                        termino in (c.get("numero_folio_buap") or "").lower() or
                        termino in (c.get("descripcion_objeto") or "").lower() or
                        termino in (c.get("nombre_empresa") or "").lower()
                    )
                ]

            self.total_contratos = len(self.contratos)

        except DatabaseError as e:
            self.mostrar_mensaje(f"Error al cargar contratos: {str(e)}", "error")
            self.contratos = []
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
            self.contratos = []

    async def cargar_contratos(self):
        """Carga contratos con skeleton loading (público)."""
        async for _ in self.recargar_datos(self._fetch_contratos):
            yield

    async def on_change_busqueda(self, value: str):
        """Actualizar filtro y buscar automáticamente"""
        self.filtro_busqueda = value
        async for _ in self.recargar_datos(self._fetch_contratos):
            yield

    async def aplicar_filtros(self):
        """Aplicar filtros y recargar"""
        async for _ in self.recargar_datos(self._fetch_contratos):
            yield

    async def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.filtro_busqueda = ""
        self.filtro_empresa_id = FILTRO_SIN_SELECCION
        self.filtro_tipo_servicio_id = FILTRO_SIN_SELECCION
        self.filtro_estatus = FILTRO_TODOS
        self.filtro_modalidad = ""
        self.filtro_fecha_desde = ""
        self.filtro_fecha_hasta = ""
        self.incluir_inactivos = False
        async for _ in self.recargar_datos(self._fetch_contratos):
            yield

    # ========================
    # OPERACIONES CRUD
    # ========================
    def abrir_modal_crear(self):
        """Abrir modal para crear nuevo contrato"""
        self._limpiar_formulario()
        self.es_edicion = False
        # Auto-seleccionar filtros activos
        if self.filtro_empresa_id != FILTRO_SIN_SELECCION:
            self.form_empresa_id = self.filtro_empresa_id
        if self.filtro_tipo_servicio_id != FILTRO_SIN_SELECCION:
            self.form_tipo_servicio_id = self.filtro_tipo_servicio_id
        # Establecer fecha de inicio con la fecha actual
        self.form_fecha_inicio = date.today().isoformat()
        self.mostrar_modal_contrato = True

    def abrir_modal_editar(self, contrato: dict):
        """Abrir modal para editar contrato"""
        self._limpiar_formulario()
        self.es_edicion = True
        self.contrato_seleccionado = contrato
        self._cargar_contrato_en_formulario(contrato)
        self.mostrar_modal_contrato = True

    def cerrar_modal_contrato(self):
        """Cerrar modal de crear/editar"""
        self.mostrar_modal_contrato = False
        self._limpiar_formulario()

    async def abrir_modal_detalle(self, contrato_id: int):
        """Abrir modal de detalles"""
        try:
            contrato = await contrato_service.obtener_por_id(contrato_id)
            contrato_dict = contrato.model_dump()
            # Enriquecer con nombres
            for e in self.empresas:
                if e["id"] == contrato.empresa_id:
                    contrato_dict["nombre_empresa"] = e["nombre_comercial"]
                    break
            for t in self.tipos_servicio:
                if t["id"] == contrato.tipo_servicio_id:
                    contrato_dict["nombre_servicio"] = t["nombre"]
                    break
            self.contrato_seleccionado = contrato_dict
            self.mostrar_modal_detalle = True
            # Cargar entregables del contrato
            await self._cargar_entregables_contrato(contrato_id)
        except Exception as e:
            self.manejar_error(e, "al abrir detalles")

    async def _cargar_entregables_contrato(self, contrato_id: int):
        """Cargar entregables del contrato seleccionado"""
        self.cargando_entregables = True
        try:
            entregables = await entregable_service.obtener_por_contrato(contrato_id, sincronizar=True)
            self.entregables_contrato = [
                {
                    "id": e.id,
                    "numero_periodo": e.numero_periodo,
                    "periodo_texto": e.periodo_texto,
                    "estatus": e.estatus.value if hasattr(e.estatus, 'value') else e.estatus,
                    "fecha_entrega": str(e.fecha_entrega) if e.fecha_entrega else None,
                    "monto_aprobado": str(e.monto_aprobado) if e.monto_aprobado else None,
                    "puede_revisar": e.puede_revisar_admin,
                }
                for e in entregables
            ]
        except Exception:
            self.entregables_contrato = []
        finally:
            self.cargando_entregables = False

    @rx.var
    def tiene_entregables_contrato(self) -> bool:
        return len(self.entregables_contrato) > 0

    def cerrar_modal_detalle(self):
        """Cerrar modal de detalles"""
        self.mostrar_modal_detalle = False
        self.contrato_seleccionado = None
        self.entregables_contrato = []

    def abrir_confirmar_cancelar(self, contrato: dict):
        """Abrir modal de confirmación para cancelar"""
        self.contrato_seleccionado = contrato
        self.mostrar_modal_confirmar_cancelar = True

    def cerrar_confirmar_cancelar(self):
        """Cerrar modal de confirmación"""
        self.mostrar_modal_confirmar_cancelar = False
        self.contrato_seleccionado = None

    async def guardar_contrato(self):
        """Guardar contrato (crear o actualizar)"""
        self._validar_todos_los_campos()

        if self.tiene_errores_formulario:
            # Recopilar errores para mostrar mensaje descriptivo
            errores = []
            # Errores de campos siempre requeridos
            if self.error_empresa_id:
                errores.append(f"Empresa: {self.error_empresa_id}")
            if self.error_tipo_contrato:
                errores.append(f"Tipo Contrato: {self.error_tipo_contrato}")
            if self.error_modalidad_adjudicacion:
                errores.append(f"Modalidad: {self.error_modalidad_adjudicacion}")
            if self.error_fecha_inicio:
                errores.append(f"Fecha inicio: {self.error_fecha_inicio}")
            if self.error_descripcion_objeto:
                errores.append(f"Descripción: {self.error_descripcion_objeto}")

            # Errores condicionales (solo si es SERVICIOS)
            es_servicios = self.form_tipo_contrato == TipoContrato.SERVICIOS.value
            if es_servicios:
                if self.error_tipo_servicio_id:
                    errores.append(f"Tipo Servicio: {self.error_tipo_servicio_id}")
                if self.error_tipo_duracion:
                    errores.append(f"Duración: {self.error_tipo_duracion}")
                if self.error_fecha_fin:
                    errores.append(f"Fecha fin: {self.error_fecha_fin}")

            mensaje_errores = "; ".join(errores) if errores else "Verifique los campos del formulario"
            yield rx.toast.error(
                mensaje_errores,
                position="top-center",
                duration=5000
            )
            return  # Salir sin continuar

        self.saving = True
        yield  # Forzar actualización de UI para mostrar spinner

        try:
            if self.es_edicion:
                mensaje = await self._actualizar_contrato()
            elif self.form_requisicion_id:
                mensaje = await self._crear_contrato_desde_requisicion()
            else:
                mensaje = await self._crear_contrato()

            self.cerrar_modal_contrato()
            await self._fetch_contratos()

            yield rx.toast.success(
                mensaje,
                position="top-center",
                duration=3000
            )

        except DuplicateError as e:
            self.error_codigo = f"El código '{self.form_codigo}' ya existe"
            yield self.manejar_error_con_toast(e, "al guardar contrato")
        except Exception as e:
            yield self.manejar_error_con_toast(e, "al guardar contrato")
        finally:
            self.saving = False

    async def _crear_contrato(self):
        """Crear nuevo contrato"""
        # Obtener datos de empresa y tipo de servicio para generar código
        codigo_empresa = ""
        clave_servicio = ""

        for e in self.empresas:
            if str(e["id"]) == self.form_empresa_id:
                codigo_empresa = e.get("codigo_corto") or "XXX"
                break

        # Para ADQUISICION usar "ADQ", para SERVICIOS usar la clave del tipo de servicio
        if self.form_tipo_contrato == TipoContrato.ADQUISICION.value:
            clave_servicio = "ADQ"
        else:
            for t in self.tipos_servicio:
                if str(t["id"]) == self.form_tipo_servicio_id:
                    clave_servicio = t.get("clave") or "XX"
                    break

        contrato_create = self._preparar_contrato_desde_formulario()

        # Crear con código autogenerado
        contrato_creado = await contrato_service.crear_con_codigo_auto(
            contrato_create,
            codigo_empresa,
            clave_servicio
        )

        # Guardar configuración de entregables si hay tipos configurados
        if self.config_entregables:
            for config in self.config_entregables:
                tipo_config = ContratoTipoEntregableCreate(
                    contrato_id=contrato_creado.id,
                    tipo_entregable=TipoEntregable(config["tipo_entregable"]),
                    periodicidad=PeriodicidadEntregable(config["periodicidad"]),
                    requerido=config["requerido"],
                    descripcion=config.get("descripcion"),
                    instrucciones=config.get("instrucciones"),
                )
                await entregable_service.configurar_tipo_entregable(tipo_config)

        return f"Contrato '{contrato_creado.codigo}' creado exitosamente"

    async def _actualizar_contrato(self) -> str:
        """Actualizar contrato existente con lógica condicional"""
        if not self.contrato_seleccionado:
            raise BusinessRuleError("No hay contrato seleccionado para actualizar")

        codigo = self.contrato_seleccionado.get("codigo", "")
        es_adquisicion = self.form_tipo_contrato == TipoContrato.ADQUISICION.value

        # tipo_duracion: solo para SERVICIOS
        tipo_duracion = None
        if self.form_tipo_duracion and not es_adquisicion:
            tipo_duracion = TipoDuracion(self.form_tipo_duracion)

        # monto_minimo: solo para SERVICIOS
        monto_minimo = None
        if not es_adquisicion and self.form_monto_minimo:
            monto_minimo = self._parse_decimal(self.form_monto_minimo)

        # tiene_personal: False para ADQUISICION
        tiene_personal = False if es_adquisicion else self.form_tiene_personal

        contrato_update = ContratoUpdate(
            empresa_id=self.parse_id(self.form_empresa_id),
            tipo_servicio_id=self.parse_id(self.form_tipo_servicio_id) if self.form_tipo_servicio_id and not es_adquisicion else None,
            numero_folio_buap=self.form_folio_buap.strip() or None,
            tipo_contrato=TipoContrato(self.form_tipo_contrato) if self.form_tipo_contrato else None,
            modalidad_adjudicacion=ModalidadAdjudicacion(self.form_modalidad_adjudicacion) if self.form_modalidad_adjudicacion else None,
            tipo_duracion=tipo_duracion,
            fecha_inicio=date.fromisoformat(self.form_fecha_inicio) if self.form_fecha_inicio else None,
            fecha_fin=date.fromisoformat(self.form_fecha_fin) if self.form_fecha_fin else None,
            descripcion_objeto=self.form_descripcion_objeto.strip(),  # Ahora es obligatorio
            monto_minimo=monto_minimo,
            monto_maximo=self._parse_decimal(self.form_monto_maximo),
            incluye_iva=self.form_incluye_iva,
            origen_recurso=self.form_origen_recurso.strip() or None,
            segmento_asignacion=self.form_segmento_asignacion.strip() or None,
            sede_campus=self.form_sede_campus.strip() or None,
            requiere_poliza=self.form_requiere_poliza,
            poliza_detalle=self.form_poliza_detalle.strip() or None,
            tiene_personal=tiene_personal,
            estatus=EstatusContrato(self.form_estatus) if self.form_estatus else None,
            notas=self.form_notas.strip() or None,
        )

        await contrato_service.actualizar(
            self.contrato_seleccionado["id"],
            contrato_update
        )

        return f"Contrato '{codigo}' actualizado exitosamente"

    # ========================
    # CREAR DESDE REQUISICIÓN
    # ========================

    # Mapeo TipoContratacion -> TipoContrato
    TIPO_CONTRATACION_A_CONTRATO = {
        TipoContratacion.ADQUISICION.value: TipoContrato.ADQUISICION.value,
        TipoContratacion.ARRENDAMIENTO.value: TipoContrato.ADQUISICION.value,
        TipoContratacion.SERVICIO.value: TipoContrato.SERVICIOS.value,
    }

    async def abrir_desde_requisicion(self, requisicion_id: int):
        """
        Pre-llena el formulario de contrato desde una requisición ADJUDICADA.

        1. Carga datos de la requisición
        2. Pre-llena: empresa_id, tipo_contrato, descripcion_objeto
        3. Si ADQUISICION: carga items de requisición en form_contrato_items
        4. Abre modal de creación
        """
        try:
            requisicion = await requisicion_service.obtener_por_id(requisicion_id)

            if requisicion.estado != EstadoRequisicion.ADJUDICADA:
                self.mostrar_mensaje(
                    f"Solo se pueden crear contratos desde requisiciones ADJUDICADAS. Estado actual: {requisicion.estado}",
                    "error"
                )
                return

            # Limpiar formulario
            self._limpiar_formulario()

            # Pre-llenar datos desde requisición
            self.form_requisicion_id = str(requisicion.id)
            self.form_numero_requisicion = requisicion.numero_requisicion

            if requisicion.empresa_id:
                self.form_empresa_id = str(requisicion.empresa_id)

            # Mapear tipo de contratación
            tipo_contrato = self.TIPO_CONTRATACION_A_CONTRATO.get(
                requisicion.tipo_contratacion,
                TipoContrato.ADQUISICION.value
            )
            self.form_tipo_contrato = tipo_contrato

            # Descripción del objeto
            self.form_descripcion_objeto = requisicion.objeto_contratacion or ""

            # Para ADQUISICION, cargar items de la requisición
            es_adquisicion = tipo_contrato == TipoContrato.ADQUISICION.value
            if es_adquisicion and requisicion.items:
                items_form = []
                for item in requisicion.items:
                    items_form.append({
                        "requisicion_item_id": item.id,
                        "numero_item": item.numero_item,
                        "unidad_medida": item.unidad_medida,
                        "cantidad": str(item.cantidad),
                        "descripcion": item.descripcion,
                        "precio_unitario": "",  # Debe llenarse por el usuario
                        "especificaciones_tecnicas": item.especificaciones_tecnicas or "",
                        "incluir": True,
                    })
                self.form_contrato_items = items_form

            # tiene_personal: False para ADQUISICION
            self.form_tiene_personal = not es_adquisicion

            # Abrir modal
            self.es_edicion = False
            self.mostrar_modal_contrato = True

        except Exception as e:
            self.manejar_error(e, "al cargar datos de requisición")

    async def _crear_contrato_desde_requisicion(self) -> str:
        """
        Crea contrato vinculado a requisición con items de contrato.
        Se usa cuando form_requisicion_id está presente.
        """
        requisicion_id = self.parse_id(self.form_requisicion_id)

        # Obtener datos de empresa para código
        codigo_empresa = ""
        clave_servicio = ""

        for e in self.empresas:
            if str(e["id"]) == self.form_empresa_id:
                codigo_empresa = e.get("codigo_corto") or "XXX"
                break

        # Para ADQUISICION usar "ADQ", para SERVICIOS usar la clave del tipo de servicio
        if self.form_tipo_contrato == TipoContrato.ADQUISICION.value:
            clave_servicio = "ADQ"
        else:
            for t in self.tipos_servicio:
                if str(t["id"]) == self.form_tipo_servicio_id:
                    clave_servicio = t.get("clave") or "XX"
                    break

        contrato_create = self._preparar_contrato_desde_formulario()

        # Preparar items de contrato si es ADQUISICION
        items_contrato = None
        if self.form_contrato_items:
            items_contrato = []
            for item in self.form_contrato_items:
                if not item.get("incluir", True):
                    continue
                precio = item.get("precio_unitario", "0")
                if not precio or precio.strip() == "":
                    continue
                items_contrato.append(ContratoItemCreate(
                    requisicion_item_id=item.get("requisicion_item_id"),
                    numero_item=item.get("numero_item", 1),
                    unidad_medida=item.get("unidad_medida", "Pieza"),
                    cantidad=Decimal(str(item.get("cantidad", "1")).replace(',', '') or "1"),
                    descripcion=item.get("descripcion", ""),
                    precio_unitario=Decimal(str(precio).replace(',', '')),
                    especificaciones_tecnicas=item.get("especificaciones_tecnicas") or None,
                ))

        contrato_creado = await contrato_service.crear_desde_requisicion(
            requisicion_id=requisicion_id,
            contrato_create=contrato_create,
            codigo_empresa=codigo_empresa,
            clave_servicio=clave_servicio,
            items_contrato=items_contrato,
        )

        # Guardar configuración de entregables si hay tipos configurados
        if self.config_entregables:
            for config in self.config_entregables:
                tipo_config = ContratoTipoEntregableCreate(
                    contrato_id=contrato_creado.id,
                    tipo_entregable=TipoEntregable(config["tipo_entregable"]),
                    periodicidad=PeriodicidadEntregable(config["periodicidad"]),
                    requerido=config["requerido"],
                    descripcion=config.get("descripcion"),
                    instrucciones=config.get("instrucciones"),
                )
                await entregable_service.configurar_tipo_entregable(tipo_config)

        return f"Contrato '{contrato_creado.codigo}' creado desde requisición"

    async def cancelar_contrato(self):
        """Cancelar (soft delete) un contrato"""
        if not self.contrato_seleccionado:
            return

        codigo = self.contrato_seleccionado["codigo"]
        contrato_id = self.contrato_seleccionado["id"]

        self.saving = True

        yield rx.toast.info(
            f"Cancelando contrato '{codigo}'...",
            position="top-center",
            duration=2000
        )

        try:
            await contrato_service.cancelar(contrato_id)
            self.cerrar_confirmar_cancelar()
            await self._fetch_contratos()

            yield rx.toast.success(
                f"Contrato '{codigo}' cancelado exitosamente",
                position="top-center",
                duration=3000
            )

        except Exception as e:
            yield self.manejar_error_con_toast(e, "al cancelar contrato")
        finally:
            self.saving = False

    async def activar_contrato(self, contrato: dict):
        """Activar un contrato en borrador"""
        codigo = contrato["codigo"]

        # Mostrar toast de proceso
        yield rx.toast.info(
            f"Activando contrato '{codigo}'...",
            position="top-center",
            duration=2000
        )

        try:
            await contrato_service.activar(contrato["id"])
            await self._fetch_contratos()

            yield rx.toast.success(
                f"Contrato '{codigo}' activado exitosamente",
                position="top-center",
                duration=3000
            )

        except Exception as e:
            yield self.manejar_error_con_toast(e, "al activar contrato")

    async def suspender_contrato(self, contrato: dict):
        """Suspender un contrato activo"""
        codigo = contrato["codigo"]

        yield rx.toast.info(
            f"Suspendiendo contrato '{codigo}'...",
            position="top-center",
            duration=2000
        )

        try:
            await contrato_service.suspender(contrato["id"])
            await self._fetch_contratos()

            yield rx.toast.success(
                f"Contrato '{codigo}' suspendido exitosamente",
                position="top-center",
                duration=3000
            )

        except Exception as e:
            yield self.manejar_error_con_toast(e, "al suspender contrato")

    async def reactivar_contrato(self, contrato: dict):
        """Reactivar un contrato suspendido"""
        codigo = contrato["codigo"]

        yield rx.toast.info(
            f"Reactivando contrato '{codigo}'...",
            position="top-center",
            duration=2000
        )

        try:
            await contrato_service.reactivar(contrato["id"])
            await self._fetch_contratos()

            yield rx.toast.success(
                f"Contrato '{codigo}' reactivado exitosamente",
                position="top-center",
                duration=3000
            )

        except Exception as e:
            yield self.manejar_error_con_toast(e, "al reactivar contrato")

    # ========================
    # CONFIGURACIÓN DE ENTREGABLES
    # ========================
    def agregar_tipo_entregable(self):
        """Agregar tipo de entregable a la configuración"""
        if not self.form_tipo_entregable:
            return

        # Verificar si ya existe este tipo
        for config in self.config_entregables:
            if config["tipo_entregable"] == self.form_tipo_entregable:
                return rx.toast.warning("Este tipo de entregable ya está configurado")

        # Obtener descripción del enum
        try:
            tipo_enum = TipoEntregable(self.form_tipo_entregable)
            tipo_label = tipo_enum.descripcion
        except ValueError:
            tipo_label = self.form_tipo_entregable

        try:
            periodicidad_enum = PeriodicidadEntregable(self.form_periodicidad_entregable)
            periodicidad_label = periodicidad_enum.descripcion
        except ValueError:
            periodicidad_label = self.form_periodicidad_entregable

        nuevo_config = {
            "tipo_entregable": self.form_tipo_entregable,
            "tipo_label": tipo_label,
            "periodicidad": self.form_periodicidad_entregable,
            "periodicidad_label": periodicidad_label,
            "requerido": self.form_entregable_requerido,
            "descripcion": self.form_entregable_descripcion.strip() or None,
            "instrucciones": self.form_entregable_instrucciones.strip() or None,
        }

        self.config_entregables = self.config_entregables + [nuevo_config]
        self._limpiar_form_entregable()

    def eliminar_tipo_entregable(self, tipo: str):
        """Eliminar tipo de entregable de la configuración por tipo"""
        self.config_entregables = [
            c for c in self.config_entregables if c["tipo_entregable"] != tipo
        ]

    def _limpiar_form_entregable(self):
        """Limpiar formulario de entregable"""
        self.form_tipo_entregable = ""
        self.form_periodicidad_entregable = PeriodicidadEntregable.MENSUAL.value
        self.form_entregable_requerido = True
        self.form_entregable_descripcion = ""
        self.form_entregable_instrucciones = ""

    # ========================
    # HELPERS
    # ========================
    def _limpiar_formulario(self):
        """Limpia campos del formulario"""
        for campo, default in FORM_DEFAULTS.items():
            setattr(self, f"form_{campo}", default)
        self._limpiar_errores()
        self._limpiar_form_entregable()
        self.config_entregables = []
        self.form_contrato_items = []
        self.contrato_seleccionado = None
        self.es_edicion = False

    def _limpiar_errores(self):
        """Limpia todos los errores de validación"""
        for campo in CAMPOS_VALIDACION:
            setattr(self, f"error_{campo}", "")
        self.error_empresa_id = ""
        self.error_tipo_servicio_id = ""
        self.error_tipo_contrato = ""
        self.error_modalidad_adjudicacion = ""
        self.error_tipo_duracion = ""
        self.error_fecha_inicio = ""
        self.error_fecha_fin = ""

    def _cargar_contrato_en_formulario(self, contrato: dict):
        """Carga datos de contrato en el formulario"""
        self.form_empresa_id = str(contrato.get("empresa_id", ""))
        self.form_tipo_servicio_id = str(contrato.get("tipo_servicio_id", ""))
        self.form_codigo = contrato.get("codigo", "")
        self.form_folio_buap = contrato.get("numero_folio_buap", "") or ""
        self.form_tipo_contrato = contrato.get("tipo_contrato", "")
        self.form_modalidad_adjudicacion = contrato.get("modalidad_adjudicacion", "")
        self.form_tipo_duracion = contrato.get("tipo_duracion", "") or ""

        # Fechas
        fecha_inicio = contrato.get("fecha_inicio")
        self.form_fecha_inicio = str(fecha_inicio) if fecha_inicio else ""
        fecha_fin = contrato.get("fecha_fin")
        self.form_fecha_fin = str(fecha_fin) if fecha_fin else ""

        self.form_descripcion_objeto = contrato.get("descripcion_objeto", "") or ""

        # Montos
        monto_min = contrato.get("monto_minimo")
        self.form_monto_minimo = str(monto_min) if monto_min else ""
        monto_max = contrato.get("monto_maximo")
        self.form_monto_maximo = str(monto_max) if monto_max else ""

        self.form_incluye_iva = contrato.get("incluye_iva", False)
        self.form_origen_recurso = contrato.get("origen_recurso", "") or ""
        self.form_segmento_asignacion = contrato.get("segmento_asignacion", "") or ""
        self.form_sede_campus = contrato.get("sede_campus", "") or ""
        self.form_requiere_poliza = contrato.get("requiere_poliza", False)
        self.form_poliza_detalle = contrato.get("poliza_detalle", "") or ""
        self.form_tiene_personal = contrato.get("tiene_personal", True)
        self.form_estatus = contrato.get("estatus", EstatusContrato.BORRADOR.value)
        self.form_notas = contrato.get("notas", "") or ""

        # Requisición origen
        req_id = contrato.get("requisicion_id")
        self.form_requisicion_id = str(req_id) if req_id else ""
        self.form_numero_requisicion = contrato.get("numero_requisicion", "") or ""

    def _preparar_contrato_desde_formulario(self) -> ContratoCreate:
        """Prepara objeto ContratoCreate desde formulario con lógica condicional"""
        es_adquisicion = self.form_tipo_contrato == TipoContrato.ADQUISICION.value

        # tipo_servicio_id: requerido para SERVICIOS, opcional para ADQUISICION
        tipo_servicio_id = None
        if self.form_tipo_servicio_id:
            tipo_servicio_id = self.parse_id(self.form_tipo_servicio_id)
        elif not es_adquisicion:
            # Solo error si es SERVICIOS y no tiene tipo_servicio
            raise ValueError("Tipo de servicio es requerido para contratos de servicios")

        # tipo_duracion: requerido para SERVICIOS, no aplica para ADQUISICION
        tipo_duracion = None
        if self.form_tipo_duracion:
            tipo_duracion = TipoDuracion(self.form_tipo_duracion)

        # fecha_fin: según tipo_duracion
        fecha_fin = None
        if self.form_fecha_fin:
            fecha_fin = date.fromisoformat(self.form_fecha_fin)

        # monto_minimo: solo para SERVICIOS
        monto_minimo = None
        if not es_adquisicion and self.form_monto_minimo:
            monto_minimo = self._parse_decimal(self.form_monto_minimo)

        # tiene_personal: False para ADQUISICION, configurable para SERVICIOS
        tiene_personal = False if es_adquisicion else self.form_tiene_personal

        # requisicion_id (si viene del flujo Requisicion -> Contrato)
        requisicion_id = None
        if self.form_requisicion_id:
            requisicion_id = self.parse_id(self.form_requisicion_id)

        return ContratoCreate(
            empresa_id=self.parse_id(self.form_empresa_id),
            tipo_servicio_id=tipo_servicio_id,
            requisicion_id=requisicion_id,
            codigo="TEMP",  # Se sobrescribe con autogenerado
            numero_folio_buap=self.form_folio_buap.strip() or None,
            tipo_contrato=TipoContrato(self.form_tipo_contrato),
            modalidad_adjudicacion=ModalidadAdjudicacion(self.form_modalidad_adjudicacion),
            tipo_duracion=tipo_duracion,
            fecha_inicio=date.fromisoformat(self.form_fecha_inicio),
            fecha_fin=fecha_fin,
            descripcion_objeto=self.form_descripcion_objeto.strip(),  # Ahora es obligatorio
            monto_minimo=monto_minimo,
            monto_maximo=self._parse_decimal(self.form_monto_maximo),
            incluye_iva=self.form_incluye_iva,
            origen_recurso=self.form_origen_recurso.strip() or None,
            segmento_asignacion=self.form_segmento_asignacion.strip() or None,
            sede_campus=self.form_sede_campus.strip() or None,
            requiere_poliza=self.form_requiere_poliza,
            poliza_detalle=self.form_poliza_detalle.strip() or None,
            tiene_personal=tiene_personal,
            estatus=EstatusContrato(self.form_estatus) if self.form_estatus else EstatusContrato.BORRADOR,
            notas=self.form_notas.strip() or None,
        )

    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """Parsea string a Decimal, retorna None si vacío o inválido"""
        if not value or value.strip() == "":
            return None
        try:
            return Decimal(value.replace(",", "").replace("$", "").strip())
        except InvalidOperation:
            return None

    def obtener_nombre_empresa(self, empresa_id: int) -> str:
        """Obtener nombre de empresa por ID"""
        for empresa in self.empresas:
            if empresa["id"] == empresa_id:
                return f"{empresa['codigo_corto']} - {empresa['nombre_comercial']}"
        return "Desconocida"

    def obtener_nombre_tipo_servicio(self, tipo_servicio_id: int) -> str:
        """Obtener nombre de tipo de servicio por ID"""
        for tipo in self.tipos_servicio:
            if tipo["id"] == tipo_servicio_id:
                return f"{tipo['clave']} - {tipo['nombre']}"
        return "Desconocido"
