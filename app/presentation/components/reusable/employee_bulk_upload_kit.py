"""Kit reusable para alta masiva inline de empleados."""

import reflex as rx

from app.presentation.components.shared.employee_bulk_upload_state_mixin import (
    EMPLOYEE_BULK_UPLOAD_ID,
)
from app.presentation.components.ui import (
    table_cell_text_sm,
    table_shell,
)
from app.presentation.theme import Colors, Radius, Spacing, Typography


_ENCABEZADOS_PREVIEW = [
    {"nombre": "Fila", "ancho": "72px", "header_align": "center"},
    {"nombre": "CURP", "ancho": "180px"},
    {"nombre": "Resultado", "ancho": "120px", "header_align": "center"},
    {"nombre": "Mensaje", "ancho": "auto"},
]

_ENCABEZADOS_RESULTADOS = [
    {"nombre": "Fila", "ancho": "72px", "header_align": "center"},
    {"nombre": "CURP", "ancho": "180px"},
    {"nombre": "Resultado", "ancho": "120px", "header_align": "center"},
    {"nombre": "Clave", "ancho": "110px", "header_align": "center"},
    {"nombre": "Mensaje", "ancho": "auto"},
]


def _badge_resultado(resultado: str) -> rx.Component:
    """Badge de resultado de validación/procesamiento."""
    return rx.match(
        resultado,
        ("VALIDO", rx.badge("Valido", color_scheme="green", variant="soft", size="1")),
        ("REINGRESO", rx.badge("Reingreso", color_scheme="yellow", variant="soft", size="1")),
        ("ERROR", rx.badge("Error", color_scheme="red", variant="soft", size="1")),
        rx.badge(resultado, size="1"),
    )


def _card_resumen(titulo: str, valor, color_scheme: str, icono: str) -> rx.Component:
    """Card compacta de resumen para el flujo inline."""
    color_map = {
        "green": ("var(--green-3)", "var(--green-9)", "var(--green-11)"),
        "yellow": ("var(--yellow-3)", "var(--yellow-9)", "var(--yellow-11)"),
        "red": ("var(--red-3)", "var(--red-9)", "var(--red-11)"),
        "blue": ("var(--blue-3)", "var(--blue-9)", "var(--blue-11)"),
    }
    background, icon_color, text_color = color_map.get(
        color_scheme,
        color_map["blue"],
    )

    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(icono, size=18, color=icon_color),
                width="38px",
                height="38px",
                border_radius="10px",
                background=background,
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(
                    titulo,
                    font_size=Typography.SIZE_XS,
                    font_weight=Typography.WEIGHT_MEDIUM,
                    color=Colors.TEXT_MUTED,
                ),
                rx.text(
                    valor,
                    font_size=Typography.SIZE_XL,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=text_color,
                ),
                spacing="0",
                align="start",
            ),
            spacing="3",
            align="center",
        ),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.LG,
        flex="1 1 170px",
        min_width="170px",
    )


def _indicador_pasos(current_step) -> rx.Component:
    """Indicador visual compacto del flujo de 3 pasos."""

    def _paso(numero: int, titulo: str) -> rx.Component:
        es_activo = current_step >= numero
        es_actual = current_step == numero

        return rx.hstack(
            rx.center(
                rx.text(
                    str(numero),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                width="30px",
                height="30px",
                border_radius="999px",
                background=rx.cond(
                    es_activo,
                    Colors.PORTAL_PRIMARY,
                    Colors.SURFACE,
                ),
                border=f"1px solid {Colors.BORDER}",
                color=rx.cond(es_activo, Colors.TEXT_INVERSE, Colors.TEXT_SECONDARY),
                flex_shrink="0",
            ),
            rx.text(
                titulo,
                font_size=Typography.SIZE_SM,
                font_weight=rx.cond(
                    es_actual,
                    Typography.WEIGHT_BOLD,
                    Typography.WEIGHT_MEDIUM,
                ),
                color=rx.cond(es_activo, Colors.TEXT_PRIMARY, Colors.TEXT_MUTED),
                display=rx.breakpoints(initial="none", md="block"),
            ),
            spacing="2",
            align="center",
        )

    def _conector() -> rx.Component:
        return rx.box(
            flex="1",
            min_width="32px",
            max_width="90px",
            height="1px",
            background=Colors.BORDER,
        )

    return rx.hstack(
        _paso(1, "Subir archivo"),
        _conector(),
        _paso(2, "Validacion"),
        _conector(),
        _paso(3, "Resultados"),
        width="100%",
        justify="center",
        align="center",
        spacing="3",
    )


def _fila_preview(reg: dict) -> rx.Component:
    """Fila para la tabla de validación previa."""
    return rx.table.row(
        rx.table.cell(
            rx.center(
                rx.text(reg["fila"], font_size=Typography.SIZE_SM),
                width="100%",
            ),
        ),
        table_cell_text_sm(
            reg["curp"],
            weight=Typography.WEIGHT_MEDIUM,
        ),
        rx.table.cell(
            rx.center(
                _badge_resultado(reg["resultado"]),
                width="100%",
            ),
        ),
        table_cell_text_sm(
            reg["mensaje"],
            tone="secondary",
        ),
    )


def _fila_resultado(det: dict) -> rx.Component:
    """Fila para la tabla de resultados finales."""
    return rx.table.row(
        rx.table.cell(
            rx.center(
                rx.text(det["fila"], font_size=Typography.SIZE_SM),
                width="100%",
            ),
        ),
        table_cell_text_sm(
            det["curp"],
            weight=Typography.WEIGHT_MEDIUM,
        ),
        rx.table.cell(
            rx.center(
                _badge_resultado(det["resultado"]),
                width="100%",
            ),
        ),
        rx.table.cell(
            rx.center(
                rx.text(
                    rx.cond(det["clave"], det["clave"], "-"),
                    font_size=Typography.SIZE_SM,
                    color=Colors.PORTAL_PRIMARY_TEXT,
                    font_weight=Typography.WEIGHT_MEDIUM,
                ),
                width="100%",
            ),
        ),
        table_cell_text_sm(
            det["mensaje"],
            tone="secondary",
        ),
    )


def _paso_subir(state, upload_id: str) -> rx.Component:
    """Paso 1 del flujo inline: selección y validación del archivo."""
    return rx.vstack(
        rx.upload(
            rx.vstack(
                rx.cond(
                    state.alta_masiva_validando_archivo,
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text(
                            "Validando archivo...",
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.vstack(
                        rx.icon(
                            "upload",
                            size=30,
                            color=Colors.PORTAL_PRIMARY_TEXT,
                        ),
                        rx.text(
                            "Arrastre o seleccione un archivo CSV o Excel",
                            font_size=Typography.SIZE_BASE,
                            font_weight=Typography.WEIGHT_MEDIUM,
                            color=Colors.TEXT_PRIMARY,
                            text_align="center",
                        ),
                        rx.text(
                            "Formatos .csv, .xlsx o .xls. Maximo 500 filas y 5 MB.",
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_MUTED,
                            text_align="center",
                        ),
                        spacing="2",
                        align="center",
                    ),
                ),
                width="100%",
                align="center",
                justify="center",
                padding_y=Spacing.XL,
                padding_x=Spacing.LG,
            ),
            id=upload_id,
            accept={
                "text/csv": [".csv"],
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                "application/vnd.ms-excel": [".xls"],
            },
            max_files=1,
            no_click=state.alta_masiva_validando_archivo,
            no_drag=state.alta_masiva_validando_archivo,
            border=f"2px dashed {Colors.BORDER_STRONG}",
            border_radius=Radius.LG,
            width="100%",
            cursor=rx.cond(state.alta_masiva_validando_archivo, "wait", "pointer"),
            background=Colors.SURFACE,
            style={
                "_hover": {
                    "border_color": Colors.PORTAL_PRIMARY,
                    "background": Colors.PORTAL_PRIMARY_LIGHTER,
                }
            },
        ),
        rx.cond(
            rx.selected_files(upload_id).length() > 0,
            rx.hstack(
                rx.hstack(
                    rx.icon("file", size=16, color=Colors.PORTAL_PRIMARY_TEXT),
                    rx.foreach(
                        rx.selected_files(upload_id),
                        lambda archivo: rx.text(
                            archivo,
                            font_size=Typography.SIZE_SM,
                            color=Colors.TEXT_SECONDARY,
                        ),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.cond(
                        state.alta_masiva_validando_archivo,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Validando...", font_size=Typography.SIZE_SM),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.icon("circle-check", size=16),
                            rx.text("Validar archivo", font_size=Typography.SIZE_SM),
                            spacing="2",
                            align="center",
                        ),
                    ),
                    on_click=state.handle_upload_alta_masiva(
                        rx.upload_files(upload_id=upload_id),
                    ),
                    disabled=state.alta_masiva_validando_archivo,
                    color_scheme="teal",
                    size="2",
                ),
                width="100%",
                align="center",
                spacing="3",
            ),
            rx.fragment(),
        ),
        rx.cond(
            state.alta_masiva_archivo_error != "",
            rx.callout(
                state.alta_masiva_archivo_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.box(
            width="100%",
            height="1px",
            background=Colors.BORDER,
        ),
        rx.vstack(
            rx.text(
                "Plantillas",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_BOLD,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                "Use el formato oficial para evitar errores de validación.",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_SECONDARY,
            ),
            rx.hstack(
                rx.button(
                    rx.icon("file-spreadsheet", size=16),
                    "Plantilla Excel",
                    on_click=state.descargar_plantilla_excel_alta_masiva,
                    variant="outline",
                    color_scheme="green",
                    size="2",
                ),
                rx.button(
                    rx.icon("file-text", size=16),
                    "Plantilla CSV",
                    on_click=state.descargar_plantilla_csv_alta_masiva,
                    variant="outline",
                    size="2",
                ),
                spacing="3",
                flex_wrap="wrap",
            ),
            spacing="2",
            width="100%",
            align="start",
        ),
        width="100%",
        spacing="4",
    )


def _paso_preview(state) -> rx.Component:
    """Paso 2 del flujo inline: preview de validación."""
    return rx.vstack(
        rx.flex(
            _card_resumen(
                "Validos",
                state.alta_masiva_total_validos,
                "green",
                "circle-check",
            ),
            _card_resumen(
                "Reingresos",
                state.alta_masiva_total_reingresos,
                "yellow",
                "rotate-ccw",
            ),
            _card_resumen(
                "Errores",
                state.alta_masiva_total_errores,
                "red",
                "circle-x",
            ),
            width="100%",
            wrap="wrap",
            gap=Spacing.SM,
        ),
        rx.cond(
            ~state.alta_masiva_puede_procesar,
            rx.callout(
                "No hay registros validos para procesar. Corrija el archivo y vuelva a cargarlo.",
                icon="triangle-alert",
                color_scheme="red",
                size="1",
                width="100%",
            ),
            rx.fragment(),
        ),
        table_shell(
            loading=False,
            headers=_ENCABEZADOS_PREVIEW,
            rows=state.alta_masiva_registros_preview,
            row_renderer=_fila_preview,
            has_rows=state.alta_masiva_registros_preview.length() > 0,
            empty_component=rx.fragment(),
            table_size="2",
        ),
        rx.text(
            "Archivo: ",
            state.alta_masiva_archivo_nombre,
            " | Total filas: ",
            state.alta_masiva_validacion_total,
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", size=16),
                "Cancelar",
                on_click=state.reiniciar_alta_masiva,
                variant="outline",
                size="2",
                disabled=state.alta_masiva_procesando,
            ),
            rx.spacer(),
            rx.button(
                rx.cond(
                    state.alta_masiva_procesando,
                    rx.hstack(
                        rx.spinner(size="1"),
                        rx.text("Procesando alta...", font_size=Typography.SIZE_SM),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.icon("check", size=16),
                        rx.text("Confirmar alta", font_size=Typography.SIZE_SM),
                        spacing="2",
                        align="center",
                    ),
                ),
                on_click=state.confirmar_alta_masiva,
                size="2",
                color_scheme="teal",
                disabled=~state.alta_masiva_puede_procesar | state.alta_masiva_procesando,
            ),
            width="100%",
            spacing="3",
            align="center",
        ),
        width="100%",
        spacing="4",
    )


def _paso_resultados(state) -> rx.Component:
    """Paso 3 del flujo inline: resumen final y reporte."""
    return rx.vstack(
        rx.flex(
            _card_resumen(
                "Creados",
                state.alta_masiva_resultado_creados,
                "green",
                "user-plus",
            ),
            _card_resumen(
                "Reingresados",
                state.alta_masiva_resultado_reingresados,
                "yellow",
                "rotate-ccw",
            ),
            _card_resumen(
                "Errores",
                state.alta_masiva_resultado_errores_count,
                "red",
                "circle-x",
            ),
            width="100%",
            wrap="wrap",
            gap=Spacing.SM,
        ),
        rx.cond(
            state.alta_masiva_resultado_detalles.length() > 0,
            table_shell(
                loading=False,
                headers=_ENCABEZADOS_RESULTADOS,
                rows=state.alta_masiva_resultado_detalles,
                row_renderer=_fila_resultado,
                has_rows=True,
                empty_component=rx.fragment(),
                table_size="2",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.button(
                rx.icon("download", size=16),
                "Descargar reporte",
                on_click=state.descargar_reporte_alta_masiva,
                variant="outline",
                color_scheme="blue",
                size="2",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("upload", size=16),
                "Nueva carga",
                on_click=state.reiniciar_alta_masiva,
                color_scheme="teal",
                size="2",
            ),
            width="100%",
            spacing="3",
            align="center",
        ),
        width="100%",
        spacing="4",
    )


def employee_bulk_upload_panel(
    state,
    *,
    upload_id: str = EMPLOYEE_BULK_UPLOAD_ID,
) -> rx.Component:
    """Panel inline reusable para alta masiva.

    Contrato:
    - `state` debe exponer el contrato definido por `EmployeeBulkUploadStateMixin`.
    - La apertura/cierre del panel se controla externamente con `mostrar_panel_alta_masiva`.
    """
    return rx.cond(
        state.mostrar_panel_alta_masiva,
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "Alta masiva de empleados",
                        font_size=Typography.SIZE_LG,
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Suba un archivo, revise la validación y procese la carga sin salir del listado.",
                        font_size=Typography.SIZE_SM,
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=14),
                    size="2",
                    variant="ghost",
                    color_scheme="gray",
                    on_click=state.cerrar_panel_alta_masiva,
                ),
                width="100%",
                align="start",
                spacing="3",
            ),
            _indicador_pasos(state.alta_masiva_paso_actual),
            rx.match(
                state.alta_masiva_paso_actual,
                (1, _paso_subir(state, upload_id)),
                (2, _paso_preview(state)),
                (3, _paso_resultados(state)),
                _paso_subir(state, upload_id),
            ),
            width="100%",
            spacing="4",
            padding=Spacing.LG,
            background=Colors.PORTAL_PRIMARY_LIGHTER,
            border=f"1px solid {Colors.PORTAL_PRIMARY_LIGHT}",
            border_radius=Radius.LG,
        ),
        rx.fragment(),
    )
