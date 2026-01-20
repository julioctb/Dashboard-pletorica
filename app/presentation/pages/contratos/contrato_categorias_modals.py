"""
Modales para el módulo de Categorías de Contrato.
"""
import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_textarea
from app.presentation.components.ui.modals import modal_confirmar_eliminar as modal_eliminar_generico
from app.presentation.pages.contratos.contrato_categorias_state import ContratoCategoriaState


def resumen_personal() -> rx.Component:
    """Tarjeta con resumen de personal del contrato"""
    return rx.card(
        rx.hstack(
            # Categorías Asignadas
            rx.vstack(
                rx.text("Categorías", size="1", color="gray"),
                rx.text(ContratoCategoriaState.cantidad_categorias, weight="bold", size="3"),
                spacing="1",
                align="center",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Personal Mínimo
            rx.vstack(
                rx.text("Personal Mín.", size="1", color="gray"),
                rx.text(ContratoCategoriaState.total_minimo, weight="bold", size="3", color="blue"),
                spacing="1",
                align="center",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Personal Máximo
            rx.vstack(
                rx.text("Personal Máx.", size="1", color="gray"),
                rx.text(ContratoCategoriaState.total_maximo, weight="bold", size="3", color="green"),
                spacing="1",
                align="center",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Costo Mínimo
            rx.vstack(
                rx.text("Costo Mín.", size="1", color="gray"),
                rx.text(ContratoCategoriaState.costo_minimo_total, weight="bold", size="2", color="orange"),
                spacing="1",
                align="center",
            ),
            rx.separator(orientation="vertical", size="2"),
            # Costo Máximo
            rx.vstack(
                rx.text("Costo Máx.", size="1", color="gray"),
                rx.text(ContratoCategoriaState.costo_maximo_total, weight="bold", size="2", color="orange"),
                spacing="1",
                align="center",
            ),
            justify="between",
            width="100%",
            padding="3",
        ),
        width="100%",
    )


def fila_categoria(categoria: dict) -> rx.Component:
    """Fila de la tabla de categorías"""
    return rx.table.row(
        # Clave
        rx.table.cell(
            rx.text(categoria["categoria_clave"], size="2", weight="bold"),
        ),
        # Nombre
        rx.table.cell(
            rx.text(categoria["categoria_nombre"], size="2"),
        ),
        # Cantidad Mínima
        rx.table.cell(
            rx.text(categoria["cantidad_minima"], size="2", align="center"),
        ),
        # Cantidad Máxima
        rx.table.cell(
            rx.text(categoria["cantidad_maxima"], size="2", align="center"),
        ),
        # Costo Unitario
        rx.table.cell(
            rx.text(categoria["costo_unitario_fmt"], size="2", color="gray"),
        ),
        # Acciones
        rx.table.cell(
            rx.hstack(
                # Editar
                rx.icon_button(
                    rx.icon("pencil", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="blue",
                    on_click=lambda: ContratoCategoriaState.abrir_modal_editar_categoria(categoria),
                    title="Editar",
                ),
                # Eliminar
                rx.icon_button(
                    rx.icon("trash-2", size=14),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=lambda: ContratoCategoriaState.abrir_confirmar_eliminar(categoria),
                    title="Eliminar",
                ),
                spacing="1",
            ),
        ),
    )


def tabla_categorias() -> rx.Component:
    """Tabla de categorías asignadas al contrato"""
    return rx.cond(
        ContratoCategoriaState.cantidad_categorias > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    rx.table.column_header_cell("Clave", width="80px"),
                    rx.table.column_header_cell("Categoría", width="150px"),
                    rx.table.column_header_cell("Mín.", width="60px"),
                    rx.table.column_header_cell("Máx.", width="60px"),
                    rx.table.column_header_cell("Costo Unit.", width="100px"),
                    rx.table.column_header_cell("Acciones", width="80px"),
                ),
            ),
            rx.table.body(
                rx.foreach(ContratoCategoriaState.categorias_asignadas, fila_categoria),
            ),
            width="100%",
            size="1",
        ),
        rx.callout(
            "No hay categorías de personal asignadas a este contrato",
            icon="info",
            color_scheme="gray",
            size="2",
        ),
    )


def modal_categorias() -> rx.Component:
    """Modal principal para ver y gestionar categorías de un contrato"""
    return rx.dialog.root(
        rx.dialog.content(
            # Header
            rx.dialog.title(
                rx.hstack(
                    rx.icon("users", size=20),
                    rx.text("Personal del Contrato"),
                    rx.badge(ContratoCategoriaState.contrato_codigo, color_scheme="blue"),
                    spacing="2",
                    align="center",
                ),
            ),
            rx.dialog.description(
                "Gestione las categorías de personal y cantidades requeridas",
                margin_bottom="16px",
            ),

            # Contenido
            rx.vstack(
                # Resumen de personal
                resumen_personal(),

                # Barra de acciones
                rx.hstack(
                    rx.cond(
                        ContratoCategoriaState.tiene_categorias_disponibles,
                        rx.button(
                            rx.icon("plus", size=16),
                            "Agregar Categoría",
                            on_click=ContratoCategoriaState.abrir_modal_agregar_categoria,
                            color_scheme="blue",
                            size="2",
                        ),
                        rx.text(
                            "Todas las categorías ya están asignadas",
                            size="2",
                            color="gray",
                        ),
                    ),
                    rx.spacer(),
                    width="100%",
                    padding_y="3",
                ),

                # Tabla de categorías
                rx.cond(
                    ContratoCategoriaState.loading,
                    rx.center(
                        rx.spinner(size="3"),
                        padding="8",
                    ),
                    tabla_categorias(),
                ),

                spacing="4",
                width="100%",
            ),

            # Footer
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cerrar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ContratoCategoriaState.cerrar_modal_categorias,
                    ),
                ),
                justify="end",
                margin_top="4",
            ),

            max_width="700px",
            padding="6",
        ),
        open=ContratoCategoriaState.mostrar_modal_categorias,
    )


def modal_categoria_form() -> rx.Component:
    """Modal para crear/editar una categoría"""
    return rx.dialog.root(
        rx.dialog.content(
            # Header
            rx.dialog.title(
                rx.cond(
                    ContratoCategoriaState.es_edicion_categoria,
                    "Editar Categoría",
                    "Agregar Categoría"
                )
            ),
            rx.dialog.description(
                rx.cond(
                    ContratoCategoriaState.es_edicion_categoria,
                    "Modifique las cantidades de personal",
                    "Seleccione la categoría y defina las cantidades"
                ),
                margin_bottom="16px",
            ),

            # Formulario
            rx.vstack(
                # Selector de categoría (solo en creación)
                rx.cond(
                    ~ContratoCategoriaState.es_edicion_categoria,
                    rx.vstack(
                        rx.text("Categoría de Puesto *", size="2", color="gray"),
                        rx.select.root(
                            rx.select.trigger(
                                placeholder="Seleccione una categoría",
                                width="100%",
                            ),
                            rx.select.content(
                                rx.foreach(
                                    ContratoCategoriaState.opciones_categoria,
                                    lambda opt: rx.select.item(opt["label"], value=opt["value"])
                                ),
                            ),
                            value=ContratoCategoriaState.form_categoria_puesto_id,
                            on_change=ContratoCategoriaState.set_form_categoria_puesto_id,
                        ),
                        rx.cond(
                            ContratoCategoriaState.error_categoria_puesto_id != "",
                            rx.text(ContratoCategoriaState.error_categoria_puesto_id, color="red", size="1"),
                        ),
                        width="100%",
                        spacing="1",
                    ),
                ),

                # Cantidades mínima y máxima
                rx.hstack(
                    rx.vstack(
                        rx.text("Cantidad Mínima *", size="2", color="gray"),
                        form_input(
                            placeholder="0",
                            value=ContratoCategoriaState.form_cantidad_minima,
                            on_change=ContratoCategoriaState.set_form_cantidad_minima,
                            on_blur=ContratoCategoriaState.validar_cantidad_minima_campo,
                            error=ContratoCategoriaState.error_cantidad_minima,
                            type="number",
                        ),
                        width="50%",
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Cantidad Máxima *", size="2", color="gray"),
                        form_input(
                            placeholder="0",
                            value=ContratoCategoriaState.form_cantidad_maxima,
                            on_change=ContratoCategoriaState.set_form_cantidad_maxima,
                            on_blur=ContratoCategoriaState.validar_cantidad_maxima_campo,
                            error=ContratoCategoriaState.error_cantidad_maxima,
                            type="number",
                        ),
                        width="50%",
                        spacing="1",
                    ),
                    spacing="3",
                    width="100%",
                ),

                # Costo unitario
                rx.vstack(
                    rx.text("Costo Unitario (por persona/mes)", size="2", color="gray"),
                    form_input(
                        placeholder="$ 0.00",
                        value=ContratoCategoriaState.form_costo_unitario,
                        on_change=ContratoCategoriaState.set_form_costo_unitario,
                        on_blur=ContratoCategoriaState.validar_costo_unitario_campo,
                        error=ContratoCategoriaState.error_costo_unitario,
                    ),
                    width="100%",
                    spacing="1",
                ),

                # Notas
                rx.vstack(
                    rx.text("Notas", size="2", color="gray"),
                    form_textarea(
                        placeholder="Observaciones adicionales...",
                        value=ContratoCategoriaState.form_notas,
                        on_change=ContratoCategoriaState.set_form_notas,
                        on_blur=ContratoCategoriaState.validar_notas_campo,
                        error=ContratoCategoriaState.error_notas,
                        rows="2",
                    ),
                    width="100%",
                    spacing="1",
                ),

                spacing="4",
                width="100%",
            ),

            # Footer
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ContratoCategoriaState.cerrar_modal_categoria_form,
                    ),
                ),
                rx.button(
                    rx.cond(
                        ContratoCategoriaState.es_edicion_categoria,
                        "Guardar Cambios",
                        "Agregar Categoría"
                    ),
                    on_click=ContratoCategoriaState.guardar_categoria,
                    disabled=~ContratoCategoriaState.puede_guardar_categoria,
                    loading=ContratoCategoriaState.saving,
                    color_scheme="blue",
                ),
                justify="end",
                spacing="3",
                margin_top="4",
            ),

            max_width="450px",
            padding="6",
        ),
        open=ContratoCategoriaState.mostrar_modal_categoria_form,
    )


def modal_confirmar_eliminar_categoria() -> rx.Component:
    """Modal de confirmación para eliminar categoría (usa componente genérico)"""
    return modal_eliminar_generico(
        open=ContratoCategoriaState.mostrar_modal_confirmar_eliminar,
        titulo="Eliminar Categoría",
        mensaje="¿Está seguro de eliminar esta categoría del contrato?",
        detalle_contenido=rx.cond(
            ContratoCategoriaState.categoria_seleccionada,
            rx.vstack(
                rx.hstack(
                    rx.text("Categoría: ", weight="bold"),
                    rx.text(ContratoCategoriaState.categoria_seleccionada["categoria_nombre"]),
                    spacing="1",
                ),
                rx.hstack(
                    rx.text("Personal: ", size="2"),
                    rx.text(
                        f"{ContratoCategoriaState.categoria_seleccionada['cantidad_minima']} - {ContratoCategoriaState.categoria_seleccionada['cantidad_maxima']}",
                        size="2"
                    ),
                    spacing="1",
                ),
                spacing="1",
            ),
            rx.text(""),
        ),
        on_confirmar=ContratoCategoriaState.eliminar_categoria,
        on_cancelar=ContratoCategoriaState.cerrar_confirmar_eliminar,
        loading=ContratoCategoriaState.saving,
    )
