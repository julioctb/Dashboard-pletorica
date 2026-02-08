"""
Estado de Reflex para el módulo de Requisiciones.
Maneja el estado de la UI y las operaciones CRUD.
"""
import reflex as rx
from typing import List, Optional
from datetime import date
from decimal import Decimal

from app.presentation.components.shared.auth_state import AuthState
from app.presentation.constants import FILTRO_TODOS
from app.services.requisicion_service import requisicion_service
from app.services.requisicion_pdf_service import requisicion_pdf_service
from app.services.empresa_service import empresa_service
from app.services.archivo_service import archivo_service, ArchivoValidationError
from app.entities.archivo import EntidadArchivo, TipoArchivo

from app.entities.requisicion import (
    RequisicionCreate,
    RequisicionUpdate,
    RequisicionAdjudicar,
    RequisicionItemCreate,
)
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
    "inicio_desde_firma": False,
    "fecha_entrega_inicio": "",
    "fecha_entrega_fin": "",
    "condiciones_entrega": "",
    "tipo_garantia": "",
    "garantia_vigencia": "",
    "requisitos_proveedor": "",
    "forma_pago": "",
    "transferencia_bancaria": True,
    "requiere_anticipo": False,
    "requiere_muestras": False,
    "requiere_visita": False,
    # PDI
    "pdi_eje": "",
    "pdi_objetivo": "",
    "pdi_estrategia": "",
    "pdi_meta": "",
    # Disponibilidad presupuestal
    "partida_presupuestaria": "",
    "origen_recurso": "",
    "oficio_suficiencia": "",
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
    "partida_presupuestal": "",
    "unidad_medida": "",
    "cantidad": "",
    "descripcion": "",
}

class RequisicionesState(AuthState):
    """Estado para el módulo de Requisiciones"""

    # ========================
    # ESTADO DE DATOS
    # ========================
    requisiciones: List[dict] = []
    requisicion_seleccionada: Optional[dict] = None
    total_registros: int = 0

    # Listas para dropdowns
    empresas_opciones: List[dict] = []
    lugares_entrega_opciones: List[dict] = []

    # Configuración defaults
    configuracion_defaults: dict = {}

    # ========================
    # ARCHIVOS
    # ========================
    archivos_entidad: list[dict] = []
    subiendo_archivo: bool = False

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
    es_auto_borrador: bool = False
    accion_estado_pendiente: str = ""
    id_requisicion_edicion: int = 0
    form_paso_actual: int = 1

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
    form_inicio_desde_firma: bool = False
    form_fecha_entrega_inicio: str = ""
    form_fecha_entrega_fin: str = ""
    form_condiciones_entrega: str = ""
    form_tipo_garantia: str = ""
    form_garantia_vigencia: str = ""
    form_requisitos_proveedor: str = ""
    form_forma_pago: str = ""
    form_transferencia_bancaria: bool = True
    form_requiere_anticipo: bool = False
    form_requiere_muestras: bool = False
    form_requiere_visita: bool = False

    # PDI
    form_pdi_eje: str = ""
    form_pdi_objetivo: str = ""
    form_pdi_estrategia: str = ""
    form_pdi_meta: str = ""

    # Disponibilidad presupuestal
    form_partida_presupuestaria: str = ""
    form_origen_recurso: str = ""
    form_oficio_suficiencia: str = ""

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

    # Items del formulario
    form_items: List[dict] = []

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

    def set_form_inicio_desde_firma(self, v: bool):
        self.form_inicio_desde_firma = v
        if v:
            self.form_fecha_entrega_inicio = ""

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

    def set_form_transferencia_bancaria(self, v: bool):
        self.form_transferencia_bancaria = v

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

    def set_form_partida_presupuestaria(self, v: str):
        self.form_partida_presupuestaria = v

    def set_form_origen_recurso(self, v: str):
        self.form_origen_recurso = v

    def set_form_oficio_suficiencia(self, v: str):
        self.form_oficio_suficiencia = v

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
    # SETTERS DE UI
    # ========================
    def set_mostrar_modal_detalle(self, v: bool):
        self.mostrar_modal_detalle = v

    def set_form_paso_actual(self, paso: int):
        """Navega a un paso especifico. Valida pasos anteriores."""
        if not (1 <= paso <= 8):
            return
        # Si va hacia adelante, validar todos los pasos intermedios
        if paso > self.form_paso_actual:
            for p in range(self.form_paso_actual, paso):
                error = self._validar_paso(p)
                if error:
                    self.form_paso_actual = p
                    self.mostrar_mensaje(error, "error")
                    return
        self.form_paso_actual = paso

    def ir_paso_siguiente(self):
        if self.form_paso_actual >= 8:
            return
        error = self._validar_paso(self.form_paso_actual)
        if error:
            self.mostrar_mensaje(error, "error")
            return
        self.form_paso_actual += 1

    def ir_paso_anterior(self):
        if self.form_paso_actual > 1:
            self.form_paso_actual -= 1

    def _validar_paso(self, paso: int) -> str:
        """Valida campos obligatorios del paso indicado. Retorna mensaje de error o ''."""
        if paso == 1:
            faltantes = []
            if not self.form_tipo_contratacion:
                faltantes.append("Tipo de contratacion")
            if not self.form_fecha_elaboracion:
                faltantes.append("Fecha de elaboracion")
            if not self.form_dependencia_requirente:
                faltantes.append("Dependencia requirente")
            if not self.form_titular_nombre:
                faltantes.append("Nombre del titular")
            if faltantes:
                return f"Campos obligatorios: {', '.join(faltantes)}"
        elif paso == 2:
            faltantes = []
            if not self.form_objeto_contratacion:
                faltantes.append("Objeto de la contratacion")
            if not self.form_lugar_entrega:
                faltantes.append("Lugar de entrega")
            if faltantes:
                return f"Campos obligatorios: {', '.join(faltantes)}"
        elif paso == 3:
            if not any(i.get("descripcion") for i in self.form_items):
                return "Agregue al menos un item con descripcion"
        elif paso == 4:
            if not self.form_justificacion:
                return "Campos obligatorios: Justificacion"
        elif paso == 7:
            faltantes = []
            if not self.form_elabora_nombre:
                faltantes.append("Nombre de quien elabora")
            if not self.form_solicita_nombre:
                faltantes.append("Nombre de quien solicita")
            if faltantes:
                return f"Campos obligatorios: {', '.join(faltantes)}"
        return ""

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
    def formulario_completo(self) -> bool:
        """Indica si todos los campos requeridos estan completos."""
        return bool(
            self.form_tipo_contratacion
            and self.form_fecha_elaboracion
            and self.form_objeto_contratacion
            and self.form_justificacion
            and self.form_dependencia_requirente
            and self.form_titular_nombre
            and self.form_lugar_entrega
            and self.form_elabora_nombre
            and self.form_solicita_nombre
            and any(i.get("descripcion") for i in self.form_items)
            and self.form_partida_presupuestaria
        )

    # ========================
    # CARGA DE DATOS
    # ========================
    async def on_mount(self):
        """Se ejecuta al montar la página."""
        async for _ in self.montar_pagina(
            self._fetch_requisiciones,
            self.cargar_configuracion,
            self.cargar_empresas,
            self.cargar_lugares_entrega,
        ):
            yield

    async def _fetch_requisiciones(self):
        """Fetch interno de requisiciones (sin manejar loading)."""
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

            self.requisiciones = []
            for r in resumenes:
                d = r.model_dump(mode='json')
                # Formatear fecha a DD-MM-YYYY para la tabla
                fe = d.get("fecha_elaboracion", "")
                if fe and len(fe) >= 10:
                    partes = fe[:10].split("-")
                    if len(partes) == 3:
                        d["fecha_elaboracion"] = f"{partes[2]}-{partes[1]}-{partes[0]}"
                self.requisiciones.append(d)
            self.total_registros = len(self.requisiciones)
        except DatabaseError as e:
            self.manejar_error(e, "al cargar requisiciones")
            self.requisiciones = []
        except Exception as e:
            self.manejar_error(e, "al cargar requisiciones")
            self.requisiciones = []

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

    async def cargar_lugares_entrega(self):
        """Carga lista de lugares de entrega para dropdown."""
        try:
            lugares = await requisicion_service.obtener_lugares_entrega()
            self.lugares_entrega_opciones = [
                {"value": l.nombre, "label": l.nombre}
                for l in lugares
            ]
        except Exception:
            self.lugares_entrega_opciones = []

    async def aplicar_filtros(self):
        """Aplica filtros y recarga."""
        async for _ in self.recargar_datos(self._fetch_requisiciones):
            yield

    async def limpiar_filtros(self):
        """Limpia todos los filtros."""
        self.filtro_busqueda = ""
        self.filtro_estado = FILTRO_TODOS
        self.filtro_tipo = FILTRO_TODOS
        async for _ in self.recargar_datos(self._fetch_requisiciones):
            yield

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
    # GESTIÓN DE ARCHIVOS
    # ========================
    async def handle_upload_archivo(self, files: list[rx.UploadFile]):
        """Procesa archivos subidos para la requisicion actual."""
        if not files:
            return
        if not self.id_requisicion_edicion:
            self.mostrar_mensaje("Guarde la requisicion primero antes de subir archivos", "error")
            return

        self.subiendo_archivo = True
        try:
            for file in files:
                contenido = await file.read()
                tipo_mime = file.content_type or "application/octet-stream"
                es_imagen = tipo_mime.startswith("image/")

                await archivo_service.subir_archivo(
                    contenido=contenido,
                    nombre_original=file.filename,
                    tipo_mime=tipo_mime,
                    entidad_tipo=EntidadArchivo.REQUISICION,
                    entidad_id=self.id_requisicion_edicion,
                    identificador_ruta=f"REQ-{self.id_requisicion_edicion}",
                    tipo_archivo=TipoArchivo.IMAGEN if es_imagen else TipoArchivo.DOCUMENTO,
                )

            await self.cargar_archivos_entidad()
            self.mostrar_mensaje("Archivos subidos correctamente", "success")
        except ArchivoValidationError as e:
            self.mostrar_mensaje(str(e), "error")
        except Exception as e:
            self.manejar_error(e, "al subir archivos")
        finally:
            self.subiendo_archivo = False

    async def eliminar_archivo_entidad(self, archivo_id: int):
        """Elimina un archivo de la requisicion."""
        try:
            await archivo_service.eliminar_archivo(archivo_id)
            await self.cargar_archivos_entidad()
            self.mostrar_mensaje("Archivo eliminado", "success")
        except Exception as e:
            self.manejar_error(e, "al eliminar archivo")

    async def cargar_archivos_entidad(self):
        """Carga archivos de la requisicion actual."""
        if not self.id_requisicion_edicion:
            self.archivos_entidad = []
            return
        try:
            archivos = await archivo_service.obtener_archivos_entidad(
                EntidadArchivo.REQUISICION,
                self.id_requisicion_edicion,
            )
            self.archivos_entidad = [
                {
                    "id": a.id,
                    "nombre_original": a.nombre_original,
                    "tipo_mime": a.tipo_mime,
                    "tamanio_bytes": a.tamanio_bytes,
                    "fue_comprimido": a.fue_comprimido,
                }
                for a in archivos
            ]
        except Exception:
            self.archivos_entidad = []

    # ========================
    # MODALES
    # ========================
    def _limpiar_formulario(self):
        """Limpia todos los campos del formulario."""
        for campo, valor in FORM_DEFAULTS.items():
            setattr(self, f"form_{campo}", valor)
        self.form_items = [dict(ITEM_DEFAULT)]
        self.archivos_entidad = []
        self.subiendo_archivo = False
        self.es_edicion = False
        self.es_auto_borrador = False
        self.id_requisicion_edicion = 0
        self.form_paso_actual = 1

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

    async def abrir_modal_crear(self):
        """Abre modal de creación con auto-borrador para permitir subir archivos."""
        self._limpiar_formulario()
        self._prellenar_defaults()

        # Crear auto-borrador silencioso para obtener ID y habilitar archivos
        try:
            create_data = RequisicionCreate(
                fecha_elaboracion=date.fromisoformat(self.form_fecha_elaboracion) if self.form_fecha_elaboracion else date.today(),
                tipo_contratacion="ADQUISICION",
                objeto_contratacion="(borrador)",
                justificacion="(borrador)",
                dependencia_requirente=self.form_dependencia_requirente or "(borrador)",
                titular_nombre=self.form_titular_nombre or "(borrador)",
                lugar_entrega=self.form_lugar_entrega or "(borrador)",
                elabora_nombre=self.form_elabora_nombre or "(borrador)",
                solicita_nombre=self.form_solicita_nombre or "(borrador)",
                items=[],
            )
            requisicion = await requisicion_service.crear(create_data, creado_por=self.id_usuario or None)
            self.id_requisicion_edicion = requisicion.id
            self.es_edicion = True
            self.es_auto_borrador = True
        except Exception as e:
            # Si falla el auto-borrador, el modal abre sin archivos
            import logging
            logging.getLogger(__name__).warning(f"Auto-borrador falló: {e}")
            self.id_requisicion_edicion = 0
            self.es_edicion = False
            self.es_auto_borrador = False

        self.mostrar_modal_crear = True

    async def cerrar_modal_crear(self):
        """Cierra modal de creación. Elimina el auto-borrador si no se guardó."""
        self.mostrar_modal_crear = False
        if self.es_auto_borrador and self.id_requisicion_edicion:
            try:
                await requisicion_service.eliminar(self.id_requisicion_edicion)
            except Exception:
                pass  # Ignorar si ya no existe
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
                    "partida_presupuestal": item.get("partida_presupuestal", "") or "",
                    "unidad_medida": item.get("unidad_medida", ""),
                    "cantidad": str(item.get("cantidad", "")),
                    "descripcion": item.get("descripcion", ""),
                }
                for i, item in enumerate(req_dict.get("items", []))
            ] or [dict(ITEM_DEFAULT)]

            # Cargar archivos asociados
            await self.cargar_archivos_entidad()

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
                    partida_presupuestal=item.get("partida_presupuestal") or None,
                    unidad_medida=item.get("unidad_medida", "Pieza"),
                    cantidad=Decimal(str(item.get("cantidad", "1")).replace(',', '') or "1"),
                    descripcion=item["descripcion"],
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
                    inicio_desde_firma=self.form_inicio_desde_firma,
                    fecha_entrega_inicio=date.fromisoformat(self.form_fecha_entrega_inicio) if self.form_fecha_entrega_inicio and not self.form_inicio_desde_firma else None,
                    fecha_entrega_fin=date.fromisoformat(self.form_fecha_entrega_fin) if self.form_fecha_entrega_fin else None,
                    condiciones_entrega=self.form_condiciones_entrega or None,
                    tipo_garantia=self.form_tipo_garantia or None,
                    garantia_vigencia=self.form_garantia_vigencia or None,
                    requisitos_proveedor=self.form_requisitos_proveedor or None,
                    forma_pago=self.form_forma_pago or None,
                    transferencia_bancaria=self.form_transferencia_bancaria,
                    requiere_anticipo=self.form_requiere_anticipo,
                    requiere_muestras=self.form_requiere_muestras,
                    requiere_visita=self.form_requiere_visita,
                    pdi_eje=self.form_pdi_eje or None,
                    pdi_objetivo=self.form_pdi_objetivo or None,
                    pdi_estrategia=self.form_pdi_estrategia or None,
                    pdi_meta=self.form_pdi_meta or None,
                    partida_presupuestaria=self.form_partida_presupuestaria or None,
                    origen_recurso=self.form_origen_recurso or None,
                    oficio_suficiencia=self.form_oficio_suficiencia or None,
                    existencia_almacen=self.form_existencia_almacen or None,
                    observaciones=self.form_observaciones or None,
                    validacion_asesor=self.form_validacion_asesor or None,
                    elabora_nombre=self.form_elabora_nombre or None,
                    elabora_cargo=self.form_elabora_cargo or None,
                    solicita_nombre=self.form_solicita_nombre or None,
                    solicita_cargo=self.form_solicita_cargo or None,
                )

                await requisicion_service.actualizar(self.id_requisicion_edicion, update_data)

                # Reemplazar items
                if items_create:
                    await requisicion_service.reemplazar_items(self.id_requisicion_edicion, items_create)

                if self.es_auto_borrador:
                    # Auto-borrador guardado: desactivar flag para que cancel no lo elimine
                    self.es_auto_borrador = False
                    self.mostrar_modal_crear = False
                    self._limpiar_formulario()
                    es_borrador = not items_create
                    if es_borrador:
                        self.mostrar_mensaje("Borrador guardado correctamente", "success")
                    else:
                        self.mostrar_mensaje("Requisición creada correctamente", "success")
                else:
                    self.cerrar_modal_editar()
                    self.mostrar_mensaje("Requisición actualizada correctamente", "success")

            await self._fetch_requisiciones()

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
            await self._fetch_requisiciones()
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
                await requisicion_service.aprobar(req_id, aprobado_por=self.id_usuario or None)
            elif accion == "devolver":
                await requisicion_service.devolver(req_id)
            elif accion == "cancelar":
                await requisicion_service.cancelar(req_id)

            self.cerrar_confirmar_estado()
            self.mostrar_mensaje("Estado actualizado correctamente", "success")
            await self._fetch_requisiciones()
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
                empresa_id=self.parse_id(self.form_adjudicar_empresa_id),
                fecha_adjudicacion=date.fromisoformat(self.form_adjudicar_fecha),
            )
            await requisicion_service.adjudicar(req_id, data)
            self.cerrar_modal_adjudicar()
            self.mostrar_mensaje("Requisición adjudicada correctamente", "success")
            await self._fetch_requisiciones()
        except (BusinessRuleError, NotFoundError, DatabaseError) as e:
            self.manejar_error(e, "al adjudicar requisición")
        except Exception as e:
            self.manejar_error(e, "al adjudicar requisición")
        finally:
            self.saving = False

    # ========================
    # GENERACIÓN DE PDF
    # ========================
    async def descargar_pdf(self, requisicion_id: int):
        """
        Genera y descarga el PDF de una requisición aprobada.
        Sube el PDF a Supabase Storage temporal y retorna URL para descarga.
        """
        self.saving = True
        try:
            # Generar PDF
            pdf_bytes = await requisicion_pdf_service.generar_pdf(requisicion_id)

            # Obtener datos para nombrar archivo
            requisicion = await requisicion_service.obtener_por_id(requisicion_id)
            filename = f"{requisicion.numero_requisicion or f'REQ-BORRADOR-{requisicion_id}'}.pdf"

            # Subir a Supabase Storage
            from app.database import db_manager
            supabase = db_manager.get_client()
            storage_path = f"requisiciones/pdf/{filename}"

            try:
                supabase.storage.from_('archivos').remove([storage_path])
            except Exception:
                pass  # Ignorar si no existe

            supabase.storage.from_('archivos').upload(
                storage_path,
                pdf_bytes,
                file_options={'content-type': 'application/pdf'}
            )

            url = supabase.storage.from_('archivos').get_public_url(storage_path)

            self.mostrar_mensaje("PDF generado correctamente", "success")
            return rx.redirect(url, external=True)

        except (BusinessRuleError, Exception) as e:
            self.manejar_error(e, "al generar PDF")
        finally:
            self.saving = False
