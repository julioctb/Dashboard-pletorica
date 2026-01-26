"""
Estado de Reflex para el módulo de Requisiciones.
Maneja el estado de la UI y las operaciones CRUD.
"""
import reflex as rx
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.presentation.components.shared.base_state import BaseState
from app.presentation.constants import FILTRO_TODOS
from app.services.requisicion_service import requisicion_service
from app.services.empresa_service import empresa_service

from app.entities.requisicion import (
    RequisicionCreate,
    RequisicionUpdate,
    RequisicionAdjudicar,
    RequisicionItemCreate,
    RequisicionPartidaCreate,
)
from app.core.enums import EstadoRequisicion, TipoContratacion
from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    DatabaseError,
    BusinessRuleError,
)


# ============================================================================
# VALORES POR DEFECTO DEL FORMULARIO
# ============================================================================

FORM_DEFAULTS = {
    # Datos generales
    "fecha_elaboracion": "",
    "tipo_contratacion": "",
    "objeto_contratacion": "",
    "justificacion": "",
    # Área requirente
    "dependencia_requirente": "",
    "domicilio": "",
    "titular_nombre": "",
    "titular_cargo": "",
    "titular_telefono": "",
    "titular_email": "",
    "coordinador_nombre": "",
    "coordinador_telefono": "",
    "coordinador_email": "",
    "asesor_nombre": "",
    "asesor_telefono": "",
    "asesor_email": "",
    # Bien/Servicio
    "lugar_entrega": "",
    "fecha_entrega_inicio": "",
    "fecha_entrega_fin": "",
    "condiciones_entrega": "",
    "tipo_garantia": "",
    "garantia_vigencia": "",
    "requisitos_proveedor": "",
    "forma_pago": "",
    "requiere_anticipo": False,
    "requiere_muestras": False,
    "requiere_visita": False,
    # PDI
    "pdi_eje": "",
    "pdi_objetivo": "",
    "pdi_estrategia": "",
    "pdi_meta": "",
    # Otros
    "existencia_almacen": "",
    "observaciones": "",
    # Firmas
    "validacion_asesor": "",
    "elabora_nombre": "",
    "elabora_cargo": "",
    "solicita_nombre": "",
    "solicita_cargo": "",
    # Adjudicación
    "adjudicar_empresa_id": "",
    "adjudicar_fecha": "",
}

# Item por defecto vacío
ITEM_DEFAULT = {
    "numero_item": 1,
    "unidad_medida": "",
    "cantidad": "",
    "descripcion": "",
    "precio_unitario_estimado": "",
    "especificaciones_tecnicas": "",
}

# Partida por defecto vacía
PARTIDA_DEFAULT = {
    "partida_presupuestaria": "",
    "area_destino": "",
    "origen_recurso": "",
    "oficio_suficiencia": "",
    "presupuesto_autorizado": "",
    "descripcion": "",
}


class RequisicionesState(BaseState):
    """Estado para el módulo de Requisiciones"""

    # ========================
    # ESTADO DE DATOS
    # ========================
    requisiciones: List[dict] = []
    requisicion_seleccionada: Optional[dict] = None
    total_registros: int = 0

    # Listas para dropdowns
    empresas_opciones: List[dict] = []

    # Configuración defaults
    configuracion_defaults: dict = {}

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_crear: bool = False
    mostrar_modal_editar: bool = False
    mostrar_modal_detalle: bool = False
    mostrar_modal_adjudicar: bool = False
    mostrar_modal_confirmar_eliminar: bool = False
    mostrar_modal_confirmar_estado: bool = False
    es_edicion: bool = False
    accion_estado_pendiente: str = ""
    id_requisicion_edicion: int = 0

    # ========================
    # ESTADO DE VISTA
    # ========================
    view_mode: str = "table"

    # ========================
    # FILTROS
    # ========================
    filtro_estado: str = FILTRO_TODOS
    filtro_tipo: str = FILTRO_TODOS

    # ========================
    # ESTADO DEL FORMULARIO
    # ========================
    # Datos generales
    form_fecha_elaboracion: str = ""
    form_tipo_contratacion: str = ""
    form_objeto_contratacion: str = ""
    form_justificacion: str = ""

    # Área requirente
    form_dependencia_requirente: str = ""
    form_domicilio: str = ""
    form_titular_nombre: str = ""
    form_titular_cargo: str = ""
    form_titular_telefono: str = ""
    form_titular_email: str = ""
    form_coordinador_nombre: str = ""
    form_coordinador_telefono: str = ""
    form_coordinador_email: str = ""
    form_asesor_nombre: str = ""
    form_asesor_telefono: str = ""
    form_asesor_email: str = ""

    # Bien/Servicio
    form_lugar_entrega: str = ""
    form_fecha_entrega_inicio: str = ""
    form_fecha_entrega_fin: str = ""
    form_condiciones_entrega: str = ""
    form_tipo_garantia: str = ""
    form_garantia_vigencia: str = ""
    form_requisitos_proveedor: str = ""
    form_forma_pago: str = ""
    form_requiere_anticipo: bool = False
    form_requiere_muestras: bool = False
    form_requiere_visita: bool = False

    # PDI
    form_pdi_eje: str = ""
    form_pdi_objetivo: str = ""
    form_pdi_estrategia: str = ""
    form_pdi_meta: str = ""

    # Otros
    form_existencia_almacen: str = ""
    form_observaciones: str = ""

    # Firmas
    form_validacion_asesor: str = ""
    form_elabora_nombre: str = ""
    form_elabora_cargo: str = ""
    form_solicita_nombre: str = ""
    form_solicita_cargo: str = ""

    # Adjudicación
    form_adjudicar_empresa_id: str = ""
    form_adjudicar_fecha: str = ""

    # Items y partidas del formulario
    form_items: List[dict] = []
    form_partidas: List[dict] = []

    # ========================
    # SETTERS DE FORMULARIO
    # ========================
    def set_form_fecha_elaboracion(self, v: str):
        self.form_fecha_elaboracion = v

    def set_form_tipo_contratacion(self, v: str):
        self.form_tipo_contratacion = v

    def set_form_objeto_contratacion(self, v: str):
        self.form_objeto_contratacion = v

    def set_form_justificacion(self, v: str):
        self.form_justificacion = v

    def set_form_dependencia_requirente(self, v: str):
        self.form_dependencia_requirente = v

    def set_form_domicilio(self, v: str):
        self.form_domicilio = v

    def set_form_titular_nombre(self, v: str):
        self.form_titular_nombre = v

    def set_form_titular_cargo(self, v: str):
        self.form_titular_cargo = v

    def set_form_titular_telefono(self, v: str):
        self.form_titular_telefono = v

    def set_form_titular_email(self, v: str):
        self.form_titular_email = v

    def set_form_coordinador_nombre(self, v: str):
        self.form_coordinador_nombre = v

    def set_form_coordinador_telefono(self, v: str):
        self.form_coordinador_telefono = v

    def set_form_coordinador_email(self, v: str):
        self.form_coordinador_email = v

    def set_form_asesor_nombre(self, v: str):
        self.form_asesor_nombre = v

    def set_form_asesor_telefono(self, v: str):
        self.form_asesor_telefono = v

    def set_form_asesor_email(self, v: str):
        self.form_asesor_email = v

    def set_form_lugar_entrega(self, v: str):
        self.form_lugar_entrega = v

    def set_form_fecha_entrega_inicio(self, v: str):
        self.form_fecha_entrega_inicio = v

    def set_form_fecha_entrega_fin(self, v: str):
        self.form_fecha_entrega_fin = v

    def set_form_condiciones_entrega(self, v: str):
        self.form_condiciones_entrega = v

    def set_form_tipo_garantia(self, v: str):
        self.form_tipo_garantia = v

    def set_form_garantia_vigencia(self, v: str):
        self.form_garantia_vigencia = v

    def set_form_requisitos_proveedor(self, v: str):
        self.form_requisitos_proveedor = v

    def set_form_forma_pago(self, v: str):
        self.form_forma_pago = v

    def set_form_requiere_anticipo(self, v: bool):
        self.form_requiere_anticipo = v

    def set_form_requiere_muestras(self, v: bool):
        self.form_requiere_muestras = v

    def set_form_requiere_visita(self, v: bool):
        self.form_requiere_visita = v

    def set_form_pdi_eje(self, v: str):
        self.form_pdi_eje = v

    def set_form_pdi_objetivo(self, v: str):
        self.form_pdi_objetivo = v

    def set_form_pdi_estrategia(self, v: str):
        self.form_pdi_estrategia = v

    def set_form_pdi_meta(self, v: str):
        self.form_pdi_meta = v

    def set_form_existencia_almacen(self, v: str):
        self.form_existencia_almacen = v

    def set_form_observaciones(self, v: str):
        self.form_observaciones = v

    def set_form_validacion_asesor(self, v: str):
        self.form_validacion_asesor = v

    def set_form_elabora_nombre(self, v: str):
        self.form_elabora_nombre = v

    def set_form_elabora_cargo(self, v: str):
        self.form_elabora_cargo = v

    def set_form_solicita_nombre(self, v: str):
        self.form_solicita_nombre = v

    def set_form_solicita_cargo(self, v: str):
        self.form_solicita_cargo = v

    def set_form_adjudicar_empresa_id(self, v: str):
        self.form_adjudicar_empresa_id = v

    def set_form_adjudicar_fecha(self, v: str):
        self.form_adjudicar_fecha = v

    # ========================
    # SETTERS DE FILTROS
    # ========================
    def set_filtro_estado(self, v: str):
        self.filtro_estado = v if v else FILTRO_TODOS

    def set_filtro_tipo(self, v: str):
        self.filtro_tipo = v if v else FILTRO_TODOS

    # ========================
    # SETTERS DE VISTA
    # ========================
    def set_view_table(self):
        self.view_mode = "table"

    def set_view_cards(self):
        self.view_mode = "cards"

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def is_table_view(self) -> bool:
        return self.view_mode == "table"

    @rx.var
    def tiene_requisiciones(self) -> bool:
        return len(self.requisiciones) > 0

    @rx.var
    def requisiciones_filtradas(self) -> List[dict]:
        """Filtra requisiciones por búsqueda en memoria."""
        if not self.filtro_busqueda:
            return self.requisiciones

        termino = self.filtro_busqueda.lower()
        return [
            r for r in self.requisiciones
            if termino in (r.get("numero_requisicion") or "").lower()
            or termino in (r.get("objeto_contratacion") or "").lower()
            or termino in (r.get("dependencia_requirente") or "").lower()
            or termino in (r.get("empresa_nombre") or "").lower()
        ]

    @rx.var
    def total_filtrado(self) -> int:
        return len(self.requisiciones_filtradas)

    @rx.var
    def opciones_estado(self) -> List[dict]:
        return [
            {"value": FILTRO_TODOS, "label": "Todos"},
            {"value": "BORRADOR", "label": "Borrador"},
            {"value": "ENVIADA", "label": "Enviada"},
            {"value": "EN_REVISION", "label": "En revisión"},
            {"value": "APROBADA", "label": "Aprobada"},
            {"value": "ADJUDICADA", "label": "Adjudicada"},
            {"value": "CONTRATADA", "label": "Contratada"},
            {"value": "CANCELADA", "label": "Cancelada"},
        ]

    @rx.var
    def opciones_tipo_contratacion(self) -> List[dict]:
        return [
            {"value": FILTRO_TODOS, "label": "Todos"},
            {"value": "ADQUISICION", "label": "Adquisición"},
            {"value": "ARRENDAMIENTO", "label": "Arrendamiento"},
            {"value": "SERVICIO", "label": "Servicio"},
        ]

    @rx.var
    def opciones_tipo_form(self) -> List[dict]:
        """Opciones de tipo sin 'Todos' para el formulario."""
        return [
            {"value": "ADQUISICION", "label": "Adquisición"},
            {"value": "ARRENDAMIENTO", "label": "Arrendamiento"},
            {"value": "SERVICIO", "label": "Servicio"},
        ]

    @rx.var
    def total_presupuesto_partidas(self) -> str:
        """Suma total de presupuesto de las partidas del formulario."""
        total = Decimal('0')
        for p in self.form_partidas:
            try:
                monto = p.get("presupuesto_autorizado", "0")
                if monto:
                    total += Decimal(str(monto).replace(',', ''))
            except Exception:
                pass
        return f"${total:,.2f}"

    @rx.var
    def total_estimado_items(self) -> str:
        """Suma total estimada de los items del formulario."""
        total = Decimal('0')
        for item in self.form_items:
            try:
                cantidad = item.get("cantidad", "0")
                precio = item.get("precio_unitario_estimado", "0")
                if cantidad and precio:
                    total += Decimal(str(cantidad).replace(',', '')) * Decimal(str(precio).replace(',', ''))
            except Exception:
                pass
        return f"${total:,.2f}"

    # ========================
    # CARGA DE DATOS
    # ========================
    async def on_mount(self):
        """Se ejecuta al montar la página."""
        await self.cargar_requisiciones()
        await self.cargar_configuracion()
        await self.cargar_empresas()

    async def cargar_requisiciones(self):
        """Carga las requisiciones con filtros aplicados."""
        self.loading = True
        try:
            estado = self.filtro_estado if self.filtro_estado != FILTRO_TODOS else None
            tipo = self.filtro_tipo if self.filtro_tipo != FILTRO_TODOS else None

            resumenes = await requisicion_service.obtener_resumen(
                estado=estado,
                tipo_contratacion=tipo,
                incluir_canceladas=True,
                limite=100,
                offset=0,
            )

            self.requisiciones = [
                r.model_dump(mode='json') for r in resumenes
            ]
            self.total_registros = len(self.requisiciones)
        except DatabaseError as e:
            self.manejar_error(e, "al cargar requisiciones")
            self.requisiciones = []
        except Exception as e:
            self.manejar_error(e, "al cargar requisiciones")
            self.requisiciones = []
        finally:
            self.loading = False

    async def cargar_configuracion(self):
        """Carga los valores default de configuración."""
        try:
            self.configuracion_defaults = await requisicion_service.obtener_valores_default()
        except Exception:
            self.configuracion_defaults = {}

    async def cargar_empresas(self):
        """Carga lista de empresas para dropdowns."""
        try:
            empresas = await empresa_service.obtener_todas(incluir_inactivas=False)
            self.empresas_opciones = [
                {"value": str(e.id), "label": e.nombre_comercial}
                for e in empresas
            ]
        except Exception:
            self.empresas_opciones = []

    async def aplicar_filtros(self):
        """Aplica filtros y recarga."""
        await self.cargar_requisiciones()

    async def limpiar_filtros(self):
        """Limpia todos los filtros."""
        self.filtro_busqueda = ""
        self.filtro_estado = FILTRO_TODOS
        self.filtro_tipo = FILTRO_TODOS
        await self.cargar_requisiciones()

    # ========================
    # GESTIÓN DE ITEMS EN FORMULARIO
    # ========================
    def agregar_item(self):
        """Agrega un item vacío al formulario."""
        nuevo = dict(ITEM_DEFAULT)
        nuevo["numero_item"] = len(self.form_items) + 1
        self.form_items = self.form_items + [nuevo]

    def eliminar_item(self, index: int):
        """Elimina un item del formulario por índice."""
        items = list(self.form_items)
        if 0 <= index < len(items):
            items.pop(index)
            # Renumerar
            for i, item in enumerate(items):
                item["numero_item"] = i + 1
            self.form_items = items

    def actualizar_item_campo(self, index: int, campo: str, valor: str):
        """Actualiza un campo de un item del formulario."""
        items = list(self.form_items)
        if 0 <= index < len(items):
            items[index] = {**items[index], campo: valor}
            self.form_items = items

    # ========================
    # GESTIÓN DE PARTIDAS EN FORMULARIO
    # ========================
    def agregar_partida(self):
        """Agrega una partida vacía al formulario."""
        self.form_partidas = self.form_partidas + [dict(PARTIDA_DEFAULT)]

    def eliminar_partida(self, index: int):
        """Elimina una partida del formulario por índice."""
        partidas = list(self.form_partidas)
        if 0 <= index < len(partidas):
            partidas.pop(index)
            self.form_partidas = partidas

    def actualizar_partida_campo(self, index: int, campo: str, valor: str):
        """Actualiza un campo de una partida del formulario."""
        partidas = list(self.form_partidas)
        if 0 <= index < len(partidas):
            partidas[index] = {**partidas[index], campo: valor}
            self.form_partidas = partidas

    # ========================
    # MODALES
    # ========================
    def _limpiar_formulario(self):
        """Limpia todos los campos del formulario."""
        for campo, valor in FORM_DEFAULTS.items():
            setattr(self, f"form_{campo}", valor)
        self.form_items = [dict(ITEM_DEFAULT)]
        self.form_partidas = [dict(PARTIDA_DEFAULT)]
        self.es_edicion = False
        self.id_requisicion_edicion = 0

    def _prellenar_defaults(self):
        """Pre-llena campos del formulario con valores de configuración."""
        defaults = self.configuracion_defaults
        if not defaults:
            return

        mapping = {
            "dependencia_requirente": "dependencia_requirente",
            "domicilio": "domicilio",
            "titular_nombre": "titular_nombre",
            "titular_cargo": "titular_cargo",
            "titular_telefono": "titular_telefono",
            "titular_email": "titular_email",
            "coordinador_nombre": "coordinador_nombre",
            "coordinador_telefono": "coordinador_telefono",
            "coordinador_email": "coordinador_email",
            "asesor_nombre": "asesor_nombre",
            "asesor_telefono": "asesor_telefono",
            "asesor_email": "asesor_email",
            "lugar_entrega": "lugar_entrega",
            "validacion_asesor": "validacion_asesor",
            "elabora_nombre": "elabora_nombre",
            "elabora_cargo": "elabora_cargo",
            "solicita_nombre": "solicita_nombre",
            "solicita_cargo": "solicita_cargo",
        }

        for config_clave, form_campo in mapping.items():
            if config_clave in defaults:
                setattr(self, f"form_{form_campo}", defaults[config_clave])

        # Fecha de elaboración: hoy
        self.form_fecha_elaboracion = date.today().isoformat()

    def abrir_modal_crear(self):
        """Abre modal de creación con campos pre-llenados."""
        self._limpiar_formulario()
        self._prellenar_defaults()
        self.mostrar_modal_crear = True

    def cerrar_modal_crear(self):
        """Cierra modal de creación."""
        self.mostrar_modal_crear = False
        self._limpiar_formulario()

    async def abrir_modal_editar(self, requisicion: dict):
        """Abre modal de edición con datos de la requisición."""
        self._limpiar_formulario()
        self.es_edicion = True
        self.id_requisicion_edicion = requisicion.get("id", 0)

        try:
            # Cargar requisición completa con items y partidas
            req = await requisicion_service.obtener_por_id(self.id_requisicion_edicion)
            req_dict = req.model_dump(mode='json')

            # Llenar campos del formulario
            for campo in FORM_DEFAULTS:
                if campo in req_dict and req_dict[campo] is not None:
                    setattr(self, f"form_{campo}", str(req_dict[campo]) if not isinstance(req_dict[campo], bool) else req_dict[campo])

            # Cargar items
            self.form_items = [
                {
                    "numero_item": item.get("numero_item", i + 1),
                    "unidad_medida": item.get("unidad_medida", ""),
                    "cantidad": str(item.get("cantidad", "")),
                    "descripcion": item.get("descripcion", ""),
                    "precio_unitario_estimado": str(item.get("precio_unitario_estimado", "")) if item.get("precio_unitario_estimado") else "",
                    "especificaciones_tecnicas": item.get("especificaciones_tecnicas", "") or "",
                }
                for i, item in enumerate(req_dict.get("items", []))
            ] or [dict(ITEM_DEFAULT)]

            # Cargar partidas
            self.form_partidas = [
                {
                    "partida_presupuestaria": p.get("partida_presupuestaria", ""),
                    "area_destino": p.get("area_destino", ""),
                    "origen_recurso": p.get("origen_recurso", ""),
                    "oficio_suficiencia": p.get("oficio_suficiencia", "") or "",
                    "presupuesto_autorizado": str(p.get("presupuesto_autorizado", "")),
                    "descripcion": p.get("descripcion", "") or "",
                }
                for p in req_dict.get("partidas", [])
            ] or [dict(PARTIDA_DEFAULT)]

            self.mostrar_modal_editar = True
        except Exception as e:
            self.manejar_error(e, "al cargar requisición para editar")

    def cerrar_modal_editar(self):
        """Cierra modal de edición."""
        self.mostrar_modal_editar = False
        self._limpiar_formulario()

    def abrir_modal_detalle(self, requisicion: dict):
        """Abre modal de detalle."""
        self.requisicion_seleccionada = requisicion
        self.mostrar_modal_detalle = True

    def cerrar_modal_detalle(self):
        """Cierra modal de detalle."""
        self.mostrar_modal_detalle = False
        self.requisicion_seleccionada = None

    def abrir_modal_adjudicar(self, requisicion: dict):
        """Abre modal de adjudicación."""
        self.requisicion_seleccionada = requisicion
        self.form_adjudicar_empresa_id = ""
        self.form_adjudicar_fecha = date.today().isoformat()
        self.mostrar_modal_adjudicar = True

    def cerrar_modal_adjudicar(self):
        """Cierra modal de adjudicación."""
        self.mostrar_modal_adjudicar = False
        self.requisicion_seleccionada = None

    def abrir_confirmar_eliminar(self, requisicion: dict):
        """Abre confirmación de eliminación."""
        self.requisicion_seleccionada = requisicion
        self.mostrar_modal_confirmar_eliminar = True

    def cerrar_confirmar_eliminar(self):
        """Cierra confirmación de eliminación."""
        self.mostrar_modal_confirmar_eliminar = False
        self.requisicion_seleccionada = None

    def abrir_confirmar_estado(self, requisicion: dict, accion: str):
        """Abre confirmación de cambio de estado."""
        self.requisicion_seleccionada = requisicion
        self.accion_estado_pendiente = accion
        self.mostrar_modal_confirmar_estado = True

    def cerrar_confirmar_estado(self):
        """Cierra confirmación de cambio de estado."""
        self.mostrar_modal_confirmar_estado = False
        self.requisicion_seleccionada = None
        self.accion_estado_pendiente = ""

    # ========================
    # OPERACIONES CRUD
    # ========================
    async def guardar_requisicion(self):
        """Crea o actualiza una requisición."""
        self.saving = True
        try:
            # Construir items
            items_create = []
            for item in self.form_items:
                if not item.get("descripcion"):
                    continue
                items_create.append(RequisicionItemCreate(
                    numero_item=item.get("numero_item", 1),
                    unidad_medida=item.get("unidad_medida", "Pieza"),
                    cantidad=Decimal(str(item.get("cantidad", "1")).replace(',', '') or "1"),
                    descripcion=item["descripcion"],
                    precio_unitario_estimado=Decimal(str(item.get("precio_unitario_estimado", "0")).replace(',', '') or "0") if item.get("precio_unitario_estimado") else None,
                    especificaciones_tecnicas=item.get("especificaciones_tecnicas") or None,
                ))

            # Construir partidas
            partidas_create = []
            for p in self.form_partidas:
                if not p.get("partida_presupuestaria"):
                    continue
                partidas_create.append(RequisicionPartidaCreate(
                    partida_presupuestaria=p["partida_presupuestaria"],
                    area_destino=p.get("area_destino", ""),
                    origen_recurso=p.get("origen_recurso", ""),
                    oficio_suficiencia=p.get("oficio_suficiencia") or None,
                    presupuesto_autorizado=Decimal(str(p.get("presupuesto_autorizado", "0")).replace(',', '') or "0"),
                    descripcion=p.get("descripcion") or None,
                ))

            if self.es_edicion and self.id_requisicion_edicion:
                # Actualizar requisición
                update_data = RequisicionUpdate(
                    fecha_elaboracion=date.fromisoformat(self.form_fecha_elaboracion) if self.form_fecha_elaboracion else None,
                    tipo_contratacion=self.form_tipo_contratacion or None,
                    objeto_contratacion=self.form_objeto_contratacion or None,
                    justificacion=self.form_justificacion or None,
                    dependencia_requirente=self.form_dependencia_requirente or None,
                    domicilio=self.form_domicilio or None,
                    titular_nombre=self.form_titular_nombre or None,
                    titular_cargo=self.form_titular_cargo or None,
                    titular_telefono=self.form_titular_telefono or None,
                    titular_email=self.form_titular_email or None,
                    coordinador_nombre=self.form_coordinador_nombre or None,
                    coordinador_telefono=self.form_coordinador_telefono or None,
                    coordinador_email=self.form_coordinador_email or None,
                    asesor_nombre=self.form_asesor_nombre or None,
                    asesor_telefono=self.form_asesor_telefono or None,
                    asesor_email=self.form_asesor_email or None,
                    lugar_entrega=self.form_lugar_entrega or None,
                    fecha_entrega_inicio=date.fromisoformat(self.form_fecha_entrega_inicio) if self.form_fecha_entrega_inicio else None,
                    fecha_entrega_fin=date.fromisoformat(self.form_fecha_entrega_fin) if self.form_fecha_entrega_fin else None,
                    condiciones_entrega=self.form_condiciones_entrega or None,
                    tipo_garantia=self.form_tipo_garantia or None,
                    garantia_vigencia=self.form_garantia_vigencia or None,
                    requisitos_proveedor=self.form_requisitos_proveedor or None,
                    forma_pago=self.form_forma_pago or None,
                    requiere_anticipo=self.form_requiere_anticipo,
                    requiere_muestras=self.form_requiere_muestras,
                    requiere_visita=self.form_requiere_visita,
                    pdi_eje=self.form_pdi_eje or None,
                    pdi_objetivo=self.form_pdi_objetivo or None,
                    pdi_estrategia=self.form_pdi_estrategia or None,
                    pdi_meta=self.form_pdi_meta or None,
                    existencia_almacen=self.form_existencia_almacen or None,
                    observaciones=self.form_observaciones or None,
                    validacion_asesor=self.form_validacion_asesor or None,
                    elabora_nombre=self.form_elabora_nombre or None,
                    elabora_cargo=self.form_elabora_cargo or None,
                    solicita_nombre=self.form_solicita_nombre or None,
                    solicita_cargo=self.form_solicita_cargo or None,
                )

                await requisicion_service.actualizar(self.id_requisicion_edicion, update_data)

                # Reemplazar items y partidas
                if items_create:
                    await requisicion_service.reemplazar_items(self.id_requisicion_edicion, items_create)
                if partidas_create:
                    await requisicion_service.reemplazar_partidas(self.id_requisicion_edicion, partidas_create)

                self.cerrar_modal_editar()
                self.mostrar_mensaje("Requisición actualizada correctamente", "success")
            else:
                # Crear nueva requisición
                create_data = RequisicionCreate(
                    fecha_elaboracion=date.fromisoformat(self.form_fecha_elaboracion) if self.form_fecha_elaboracion else date.today(),
                    tipo_contratacion=self.form_tipo_contratacion,
                    objeto_contratacion=self.form_objeto_contratacion,
                    justificacion=self.form_justificacion,
                    dependencia_requirente=self.form_dependencia_requirente,
                    domicilio=self.form_domicilio,
                    titular_nombre=self.form_titular_nombre,
                    titular_cargo=self.form_titular_cargo,
                    titular_telefono=self.form_titular_telefono or None,
                    titular_email=self.form_titular_email or None,
                    coordinador_nombre=self.form_coordinador_nombre or None,
                    coordinador_telefono=self.form_coordinador_telefono or None,
                    coordinador_email=self.form_coordinador_email or None,
                    asesor_nombre=self.form_asesor_nombre or None,
                    asesor_telefono=self.form_asesor_telefono or None,
                    asesor_email=self.form_asesor_email or None,
                    lugar_entrega=self.form_lugar_entrega,
                    fecha_entrega_inicio=date.fromisoformat(self.form_fecha_entrega_inicio) if self.form_fecha_entrega_inicio else None,
                    fecha_entrega_fin=date.fromisoformat(self.form_fecha_entrega_fin) if self.form_fecha_entrega_fin else None,
                    condiciones_entrega=self.form_condiciones_entrega or None,
                    tipo_garantia=self.form_tipo_garantia or None,
                    garantia_vigencia=self.form_garantia_vigencia or None,
                    requisitos_proveedor=self.form_requisitos_proveedor or None,
                    forma_pago=self.form_forma_pago or None,
                    requiere_anticipo=self.form_requiere_anticipo,
                    requiere_muestras=self.form_requiere_muestras,
                    requiere_visita=self.form_requiere_visita,
                    pdi_eje=self.form_pdi_eje or None,
                    pdi_objetivo=self.form_pdi_objetivo or None,
                    pdi_estrategia=self.form_pdi_estrategia or None,
                    pdi_meta=self.form_pdi_meta or None,
                    existencia_almacen=self.form_existencia_almacen or None,
                    observaciones=self.form_observaciones or None,
                    validacion_asesor=self.form_validacion_asesor or None,
                    elabora_nombre=self.form_elabora_nombre,
                    elabora_cargo=self.form_elabora_cargo,
                    solicita_nombre=self.form_solicita_nombre,
                    solicita_cargo=self.form_solicita_cargo,
                    items=items_create,
                    partidas=partidas_create,
                )

                await requisicion_service.crear(create_data)
                self.cerrar_modal_crear()
                self.mostrar_mensaje("Requisición creada correctamente", "success")

            await self.cargar_requisiciones()

        except (DuplicateError, BusinessRuleError, DatabaseError) as e:
            self.manejar_error(e, "al guardar requisición")
        except Exception as e:
            self.manejar_error(e, "al guardar requisición")
        finally:
            self.saving = False

    async def eliminar_requisicion(self):
        """Elimina la requisición seleccionada."""
        if not self.requisicion_seleccionada:
            return

        self.saving = True
        try:
            req_id = self.requisicion_seleccionada.get("id")
            await requisicion_service.eliminar(req_id)
            self.cerrar_confirmar_eliminar()
            self.mostrar_mensaje("Requisición eliminada correctamente", "success")
            await self.cargar_requisiciones()
        except (BusinessRuleError, NotFoundError, DatabaseError) as e:
            self.manejar_error(e, "al eliminar requisición")
        except Exception as e:
            self.manejar_error(e, "al eliminar requisición")
        finally:
            self.saving = False

    # ========================
    # TRANSICIONES DE ESTADO
    # ========================
    async def confirmar_cambio_estado(self):
        """Ejecuta la transición de estado pendiente."""
        if not self.requisicion_seleccionada or not self.accion_estado_pendiente:
            return

        self.saving = True
        try:
            req_id = self.requisicion_seleccionada.get("id")
            accion = self.accion_estado_pendiente

            if accion == "enviar":
                await requisicion_service.enviar(req_id)
            elif accion == "revisar":
                await requisicion_service.iniciar_revision(req_id)
            elif accion == "aprobar":
                await requisicion_service.aprobar(req_id)
            elif accion == "devolver":
                await requisicion_service.devolver(req_id)
            elif accion == "cancelar":
                await requisicion_service.cancelar(req_id)

            self.cerrar_confirmar_estado()
            self.mostrar_mensaje("Estado actualizado correctamente", "success")
            await self.cargar_requisiciones()
        except (BusinessRuleError, NotFoundError, DatabaseError) as e:
            self.manejar_error(e, "al cambiar estado")
        except Exception as e:
            self.manejar_error(e, "al cambiar estado")
        finally:
            self.saving = False

    async def adjudicar_requisicion(self):
        """Adjudica la requisición seleccionada a una empresa."""
        if not self.requisicion_seleccionada:
            return

        self.saving = True
        try:
            req_id = self.requisicion_seleccionada.get("id")
            data = RequisicionAdjudicar(
                empresa_id=int(self.form_adjudicar_empresa_id),
                fecha_adjudicacion=date.fromisoformat(self.form_adjudicar_fecha),
            )
            await requisicion_service.adjudicar(req_id, data)
            self.cerrar_modal_adjudicar()
            self.mostrar_mensaje("Requisición adjudicada correctamente", "success")
            await self.cargar_requisiciones()
        except (BusinessRuleError, NotFoundError, DatabaseError) as e:
            self.manejar_error(e, "al adjudicar requisición")
        except Exception as e:
            self.manejar_error(e, "al adjudicar requisición")
        finally:
            self.saving = False
