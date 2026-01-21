"""
Página principal de Empleados.
Muestra una tabla o cards con los empleados y acciones CRUD.
"""
import reflex as rx
from app.presentation.pages.empleados.empleados_state import EmpleadosState
from app.core.enums import EstatusEmpleado
from app.presentation.layout import (
    page_layout,
    page_header,
    page_toolbar,
)
from app.presentation.components.ui import (
    status_badge_reactive,
    tabla_vacia,
    skeleton_tabla,
)
from app.presentation.theme import Colors, Spacing, Shadows


# =============================================================================
# ACCIONES
# =============================================================================

def acciones_empleado(empleado: dict) -> rx.Component:
    """Acciones para cada empleado"""
    return rx.hstack(
        # Ver detalle
        rx.tooltip(
            rx.icon_button(
                rx.icon("eye", size=14),
                size="1",
                variant="ghost",
                color_scheme="gray",
                on_click=lambda: EmpleadosState.abrir_modal_detalle(empleado),
            ),
            content="Ver detalle",
        ),
        # Editar (si activo o suspendido)
        rx.cond(
            (empleado["estatus"] == "ACTIVO") | (empleado["estatus"] == "SUSPENDIDO"),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="blue",
                    on_click=lambda: EmpleadosState.abrir_modal_editar(empleado),
                ),
                content="Editar",
            ),
        ),
        # Suspender (si activo)
        rx.cond(
            empleado["estatus"] == "ACTIVO",
            rx.tooltip(
                rx.icon_button(
                    rx.icon("pause", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="amber",
                    on_click=lambda: EmpleadosState.suspender_desde_lista(empleado["id"]),
                ),
                content="Suspender",
            ),
        ),
        # Reactivar (si suspendido o inactivo)
        rx.cond(
            (empleado["estatus"] == "SUSPENDIDO") | (empleado["estatus"] == "INACTIVO"),
            rx.tooltip(
                rx.icon_button(
                    rx.icon("play", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="green",
                    on_click=lambda: EmpleadosState.reactivar_desde_lista(empleado["id"]),
                ),
                content="Reactivar",
            ),
        ),
        spacing="1",
    )


def estatus_badge(estatus: str) -> rx.Component:
    """Badge para estatus de empleado"""
    return rx.match(
        estatus,
        ("ACTIVO", rx.badge("ACTIVO", color_scheme="green", size="1")),
        ("INACTIVO", rx.badge("INACTIVO", color_scheme="red", size="1")),
        ("SUSPENDIDO", rx.badge("SUSPENDIDO", color_scheme="amber", size="1")),
        rx.badge(estatus, color_scheme="gray", size="1"),
    )


# =============================================================================
# TABLA
# =============================================================================

def fila_empleado(empleado: dict) -> rx.Component:
    """Fila de la tabla para un empleado"""
    return rx.table.row(
        # Clave
        rx.table.cell(
            rx.text(empleado["clave"], weight="bold", size="2"),
        ),
        # Nombre completo
        rx.table.cell(
            rx.text(empleado["nombre_completo"], size="2"),
        ),
        # CURP
        rx.table.cell(
            rx.text(empleado["curp"], size="2", color="gray"),
        ),
        # Empresa
        rx.table.cell(
            rx.text(empleado["empresa_nombre"], size="2"),
        ),
        # Estatus
        rx.table.cell(
            estatus_badge(empleado["estatus"]),
        ),
        # Acciones
        rx.table.cell(
            acciones_empleado(empleado),
        ),
        cursor="pointer",
        _hover={"background": Colors.SURFACE_HOVER},
        on_click=lambda: EmpleadosState.abrir_modal_detalle(empleado),
    )


ENCABEZADOS_EMPLEADOS = [
    {"nombre": "Clave", "ancho": "100px"},
    {"nombre": "Nombre", "ancho": "200px"},
    {"nombre": "CURP", "ancho": "180px"},
    {"nombre": "Empresa", "ancho": "150px"},
    {"nombre": "Estatus", "ancho": "100px"},
    {"nombre": "Acciones", "ancho": "120px"},
]


def tabla_empleados() -> rx.Component:
    """Vista de tabla de empleados"""
    return rx.cond(
        EmpleadosState.loading,
        skeleton_tabla(columnas=ENCABEZADOS_EMPLEADOS, filas=5),
        rx.cond(
            EmpleadosState.tiene_empleados,
            rx.vstack(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_EMPLEADOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            EmpleadosState.empleados_filtrados,
                            fila_empleado,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                # Contador
                rx.text(
                    "Mostrando ", EmpleadosState.total_empleados, " empleado(s)",
                    size="2",
                    color="gray",
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=EmpleadosState.abrir_modal_crear),
        ),
    )


# =============================================================================
# VISTA DE CARDS
# =============================================================================

def card_empleado(empleado: dict) -> rx.Component:
    """Card individual para un empleado"""
    return rx.card(
        rx.vstack(
            # Header con clave y estatus
            rx.hstack(
                rx.hstack(
                    rx.badge(empleado["clave"], variant="outline", size="2"),
                    spacing="2",
                ),
                rx.spacer(),
                estatus_badge(empleado["estatus"]),
                width="100%",
                align="center",
            ),

            # Nombre completo
            rx.text(empleado["nombre_completo"], weight="bold", size="3"),

            # CURP
            rx.hstack(
                rx.icon("fingerprint", size=14, color=Colors.TEXT_MUTED),
                rx.text(empleado["curp"], size="2", color=Colors.TEXT_SECONDARY),
                spacing="2",
                align="center",
            ),

            # Empresa
            rx.hstack(
                rx.icon("building-2", size=14, color=Colors.TEXT_MUTED),
                rx.text(empleado["empresa_nombre"], size="2"),
                spacing="2",
                align="center",
            ),

            # Email (si existe)
            rx.cond(
                empleado["email"],
                rx.hstack(
                    rx.icon("mail", size=14, color=Colors.TEXT_MUTED),
                    rx.text(empleado["email"], size="2"),
                    spacing="2",
                    align="center",
                ),
            ),

            # Teléfono (si existe)
            rx.cond(
                empleado["telefono"],
                rx.hstack(
                    rx.icon("phone", size=14, color=Colors.TEXT_MUTED),
                    rx.text(empleado["telefono"], size="2"),
                    spacing="2",
                    align="center",
                ),
            ),

            # Acciones
            rx.hstack(
                acciones_empleado(empleado),
                width="100%",
                justify="end",
            ),

            spacing="3",
            width="100%",
        ),
        width="100%",
        style={
            "transition": "all 0.2s ease",
            "cursor": "pointer",
            "_hover": {
                "box_shadow": Shadows.MD,
                "border_color": Colors.BORDER_STRONG,
            },
        },
        on_click=lambda: EmpleadosState.abrir_modal_detalle(empleado),
    )


def grid_empleados() -> rx.Component:
    """Vista de cards de empleados"""
    return rx.cond(
        EmpleadosState.loading,
        rx.center(rx.spinner(size="3"), padding="8"),
        rx.cond(
            EmpleadosState.tiene_empleados,
            rx.vstack(
                rx.box(
                    rx.foreach(
                        EmpleadosState.empleados_filtrados,
                        card_empleado,
                    ),
                    display="grid",
                    grid_template_columns="repeat(auto-fill, minmax(300px, 1fr))",
                    gap=Spacing.MD,
                    width="100%",
                ),
                # Contador
                rx.text(
                    "Mostrando ", EmpleadosState.total_empleados, " empleado(s)",
                    size="2",
                    color="gray",
                ),
                width="100%",
                spacing="3",
            ),
            tabla_vacia(onclick=EmpleadosState.abrir_modal_crear),
        ),
    )


# =============================================================================
# FILTROS
# =============================================================================

def filtros_empleados() -> rx.Component:
    """Filtros para empleados"""
    return rx.hstack(
        # Filtro por empresa
        rx.select.root(
            rx.select.trigger(placeholder="Empresa", width="180px"),
            rx.select.content(
                rx.select.item("Todas", value="TODAS"),
                rx.foreach(
                    EmpleadosState.opciones_empresas,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=EmpleadosState.filtro_empresa_id,
            on_change=EmpleadosState.set_filtro_empresa_id,
        ),
        # Filtro por estatus
        rx.select.root(
            rx.select.trigger(placeholder="Estatus", width="140px"),
            rx.select.content(
                rx.foreach(
                    EmpleadosState.opciones_estatus,
                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                ),
            ),
            value=EmpleadosState.filtro_estatus,
            on_change=EmpleadosState.set_filtro_estatus,
        ),
        # Botón aplicar filtros
        rx.button(
            rx.icon("search", size=14),
            "Filtrar",
            on_click=EmpleadosState.aplicar_filtros,
            variant="soft",
            size="2",
        ),
        # Botón limpiar filtros
        rx.button(
            rx.icon("x", size=14),
            "Limpiar",
            on_click=EmpleadosState.limpiar_filtros,
            variant="ghost",
            size="2",
        ),
        spacing="3",
        align="center",
    )


# =============================================================================
# MODALES (importados de componentes)
# =============================================================================

def modal_empleado() -> rx.Component:
    """Modal para crear/editar empleado"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(EmpleadosState.titulo_modal),
            rx.dialog.description("Complete los datos del empleado"),

            rx.vstack(
                # Empresa (obligatorio)
                rx.vstack(
                    rx.text("Empresa *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Seleccionar empresa...",
                            width="100%",
                        ),
                        rx.select.content(
                            rx.foreach(
                                EmpleadosState.opciones_empresas,
                                lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                            ),
                        ),
                        value=EmpleadosState.form_empresa_id,
                        on_change=EmpleadosState.set_form_empresa_id,
                    ),
                    rx.cond(
                        EmpleadosState.error_empresa_id != "",
                        rx.text(EmpleadosState.error_empresa_id, size="1", color="red"),
                    ),
                    width="100%",
                    spacing="1",
                ),

                # CURP (obligatorio, solo en creación)
                rx.cond(
                    ~EmpleadosState.es_edicion,
                    rx.vstack(
                        rx.text("CURP *", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_curp,
                            on_change=EmpleadosState.set_form_curp,
                            on_blur=EmpleadosState.validar_curp_blur,
                            placeholder="18 caracteres",
                            max_length=18,
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_curp != "",
                            rx.text(EmpleadosState.error_curp, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                ),

                # Nombre y apellidos
                rx.hstack(
                    rx.vstack(
                        rx.text("Nombre *", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_nombre,
                            on_change=EmpleadosState.set_form_nombre,
                            on_blur=EmpleadosState.validar_nombre_blur,
                            placeholder="Nombre(s)",
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_nombre != "",
                            rx.text(EmpleadosState.error_nombre, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Apellido Paterno *", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_apellido_paterno,
                            on_change=EmpleadosState.set_form_apellido_paterno,
                            on_blur=EmpleadosState.validar_apellido_paterno_blur,
                            placeholder="Apellido paterno",
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_apellido_paterno != "",
                            rx.text(EmpleadosState.error_apellido_paterno, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Apellido Materno", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_apellido_materno,
                            on_change=EmpleadosState.set_form_apellido_materno,
                            placeholder="Apellido materno (opcional)",
                            width="100%",
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # RFC y NSS
                rx.hstack(
                    rx.vstack(
                        rx.text("RFC", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_rfc,
                            on_change=EmpleadosState.set_form_rfc,
                            on_blur=EmpleadosState.validar_rfc_blur,
                            placeholder="13 caracteres",
                            max_length=13,
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_rfc != "",
                            rx.text(EmpleadosState.error_rfc, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("NSS", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_nss,
                            on_change=EmpleadosState.set_form_nss,
                            on_blur=EmpleadosState.validar_nss_blur,
                            placeholder="11 dígitos",
                            max_length=11,
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_nss != "",
                            rx.text(EmpleadosState.error_nss, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Fecha nacimiento y género
                rx.hstack(
                    rx.vstack(
                        rx.text("Fecha de Nacimiento", size="2", weight="medium"),
                        rx.input(
                            type="date",
                            value=EmpleadosState.form_fecha_nacimiento,
                            on_change=EmpleadosState.set_form_fecha_nacimiento,
                            width="100%",
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Género", size="2", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(
                                placeholder="Seleccionar...",
                                width="100%",
                            ),
                            rx.select.content(
                                rx.foreach(
                                    EmpleadosState.opciones_genero,
                                    lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                                ),
                            ),
                            value=EmpleadosState.form_genero,
                            on_change=EmpleadosState.set_form_genero,
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Teléfono y email
                rx.hstack(
                    rx.vstack(
                        rx.text("Teléfono", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_telefono,
                            on_change=EmpleadosState.set_form_telefono,
                            on_blur=EmpleadosState.validar_telefono_blur,
                            placeholder="10 dígitos",
                            max_length=15,
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_telefono != "",
                            rx.text(EmpleadosState.error_telefono, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Email", size="2", weight="medium"),
                        rx.input(
                            value=EmpleadosState.form_email,
                            on_change=EmpleadosState.set_form_email,
                            on_blur=EmpleadosState.validar_email_blur,
                            placeholder="correo@ejemplo.com",
                            width="100%",
                        ),
                        rx.cond(
                            EmpleadosState.error_email != "",
                            rx.text(EmpleadosState.error_email, size="1", color="red"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Dirección
                rx.vstack(
                    rx.text("Dirección", size="2", weight="medium"),
                    rx.text_area(
                        value=EmpleadosState.form_direccion,
                        on_change=EmpleadosState.set_form_direccion,
                        placeholder="Dirección completa",
                        width="100%",
                        rows="2",
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Contacto de emergencia
                rx.vstack(
                    rx.text("Contacto de Emergencia", size="2", weight="medium"),
                    rx.input(
                        value=EmpleadosState.form_contacto_emergencia,
                        on_change=EmpleadosState.set_form_contacto_emergencia,
                        placeholder="Nombre y teléfono",
                        width="100%",
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Notas
                rx.vstack(
                    rx.text("Notas", size="2", weight="medium"),
                    rx.text_area(
                        value=EmpleadosState.form_notas,
                        on_change=EmpleadosState.set_form_notas,
                        placeholder="Observaciones adicionales",
                        width="100%",
                        rows="2",
                    ),
                    width="100%",
                    spacing="1",
                ),

                spacing="4",
                width="100%",
                padding_y="4",
            ),

            # Botones de acción
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=EmpleadosState.cerrar_modal_empleado,
                    ),
                ),
                rx.button(
                    rx.cond(
                        EmpleadosState.saving,
                        rx.spinner(size="1"),
                        rx.icon("save", size=16),
                    ),
                    "Guardar",
                    on_click=EmpleadosState.guardar_empleado,
                    disabled=EmpleadosState.saving,
                    color_scheme="blue",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),

            max_width="600px",
        ),
        open=EmpleadosState.mostrar_modal_empleado,
        on_open_change=lambda open: rx.cond(~open, EmpleadosState.cerrar_modal_empleado(), None),
    )


def modal_detalle_empleado() -> rx.Component:
    """Modal de detalle del empleado"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(
                rx.hstack(
                    rx.icon("user", size=20),
                    EmpleadosState.nombre_completo_seleccionado,
                    spacing="2",
                    align="center",
                ),
            ),

            rx.vstack(
                # Información principal
                rx.cond(
                    EmpleadosState.empleado_seleccionado,
                    rx.vstack(
                        # Clave y estatus
                        rx.hstack(
                            rx.badge(
                                EmpleadosState.empleado_seleccionado["clave"],
                                variant="outline",
                                size="2",
                            ),
                            estatus_badge(EmpleadosState.empleado_seleccionado["estatus"]),
                            spacing="2",
                        ),

                        rx.divider(),

                        # Datos personales
                        rx.vstack(
                            rx.text("Datos Personales", weight="bold", size="3"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("CURP", size="1", color="gray"),
                                    rx.text(EmpleadosState.empleado_seleccionado["curp"], size="2"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("RFC", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["rfc"],
                                            EmpleadosState.empleado_seleccionado["rfc"],
                                            "No registrado",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("NSS", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["nss"],
                                            EmpleadosState.empleado_seleccionado["nss"],
                                            "No registrado",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="start",
                        ),

                        rx.divider(),

                        # Empresa y contacto
                        rx.vstack(
                            rx.text("Información Laboral", weight="bold", size="3"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Empresa", size="1", color="gray"),
                                    rx.text(EmpleadosState.empleado_seleccionado["empresa_nombre"], size="2"),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Fecha Ingreso", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["fecha_ingreso"],
                                            EmpleadosState.empleado_seleccionado["fecha_ingreso"],
                                            "No registrada",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="start",
                        ),

                        rx.divider(),

                        # Contacto
                        rx.vstack(
                            rx.text("Contacto", weight="bold", size="3"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Teléfono", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["telefono"],
                                            EmpleadosState.empleado_seleccionado["telefono"],
                                            "No registrado",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                rx.vstack(
                                    rx.text("Email", size="1", color="gray"),
                                    rx.text(
                                        rx.cond(
                                            EmpleadosState.empleado_seleccionado["email"],
                                            EmpleadosState.empleado_seleccionado["email"],
                                            "No registrado",
                                        ),
                                        size="2",
                                    ),
                                    spacing="1",
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="start",
                        ),

                        spacing="4",
                        width="100%",
                    ),
                ),

                spacing="4",
                width="100%",
                padding_y="4",
            ),

            # Botones de acción
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cerrar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=EmpleadosState.cerrar_modal_detalle,
                    ),
                ),
                rx.spacer(),
                # Editar (si activo o suspendido)
                rx.cond(
                    EmpleadosState.empleado_es_editable,
                    rx.button(
                        rx.icon("pencil", size=14),
                        "Editar",
                        variant="soft",
                        color_scheme="blue",
                        on_click=EmpleadosState.abrir_modal_editar_desde_detalle,
                    ),
                ),
                # Dar de baja (si activo)
                rx.cond(
                    EmpleadosState.empleado_esta_activo,
                    rx.button(
                        rx.icon("user-x", size=14),
                        "Dar de baja",
                        variant="soft",
                        color_scheme="red",
                        on_click=EmpleadosState.abrir_modal_baja,
                    ),
                ),
                # Reactivar (si inactivo)
                rx.cond(
                    EmpleadosState.empleado_esta_inactivo,
                    rx.button(
                        rx.icon("user-check", size=14),
                        "Reactivar",
                        variant="soft",
                        color_scheme="green",
                        on_click=EmpleadosState.reactivar_empleado,
                    ),
                ),
                spacing="3",
                width="100%",
            ),

            max_width="500px",
        ),
        open=EmpleadosState.mostrar_modal_detalle,
        on_open_change=lambda open: rx.cond(~open, EmpleadosState.cerrar_modal_detalle(), None),
    )


def modal_baja() -> rx.Component:
    """Modal para dar de baja a un empleado"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Dar de Baja"),
            rx.dialog.description(
                rx.text(
                    "¿Está seguro que desea dar de baja a ",
                    rx.text(EmpleadosState.nombre_completo_seleccionado, weight="bold"),
                    "?",
                ),
            ),

            rx.vstack(
                rx.vstack(
                    rx.text("Motivo de baja *", size="2", weight="medium"),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Seleccionar motivo...",
                            width="100%",
                        ),
                        rx.select.content(
                            rx.foreach(
                                EmpleadosState.opciones_motivo_baja,
                                lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                            ),
                        ),
                        value=EmpleadosState.form_motivo_baja,
                        on_change=EmpleadosState.set_form_motivo_baja,
                    ),
                    width="100%",
                    spacing="1",
                ),
                spacing="4",
                width="100%",
                padding_y="4",
            ),

            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=EmpleadosState.cerrar_modal_baja,
                    ),
                ),
                rx.button(
                    rx.cond(
                        EmpleadosState.saving,
                        rx.spinner(size="1"),
                        rx.icon("user-x", size=16),
                    ),
                    "Confirmar Baja",
                    on_click=EmpleadosState.dar_de_baja,
                    disabled=EmpleadosState.saving,
                    color_scheme="red",
                ),
                spacing="3",
                justify="end",
                width="100%",
            ),

            max_width="400px",
        ),
        open=EmpleadosState.mostrar_modal_baja,
        on_open_change=lambda open: rx.cond(~open, EmpleadosState.cerrar_modal_baja(), None),
    )


# =============================================================================
# PÁGINA PRINCIPAL
# =============================================================================

def empleados_page() -> rx.Component:
    """Página de Empleados usando el nuevo layout"""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Empleados",
                subtitulo="Administre los empleados del sistema",
                icono="users",
                accion_principal=rx.button(
                    rx.icon("plus", size=16),
                    "Nuevo Empleado",
                    on_click=EmpleadosState.abrir_modal_crear,
                    color_scheme="blue",
                ),
            ),
            toolbar=page_toolbar(
                search_value=EmpleadosState.search,
                search_placeholder="Buscar por nombre, CURP o clave...",
                on_search_change=EmpleadosState.set_search,
                on_search_clear=lambda: EmpleadosState.set_search(""),
                filters=filtros_empleados(),
                show_view_toggle=True,
                current_view=EmpleadosState.view_mode,
                on_view_table=EmpleadosState.set_view_table,
                on_view_cards=EmpleadosState.set_view_cards,
            ),
            content=rx.vstack(
                # Contenido según vista
                rx.cond(
                    EmpleadosState.is_table_view,
                    tabla_empleados(),
                    grid_empleados(),
                ),

                # Modales
                modal_empleado(),
                modal_detalle_empleado(),
                modal_baja(),

                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=EmpleadosState.on_mount,
    )
