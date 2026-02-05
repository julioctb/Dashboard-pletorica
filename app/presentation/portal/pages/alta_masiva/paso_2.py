"""
Paso 2: Preview de validacion.
"""
import reflex as rx

from .state import AltaMasivaState
from .components import card_resumen, badge_resultado


ENCABEZADOS_PREVIEW = [
    {"nombre": "Fila", "ancho": "60px"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Resultado", "ancho": "120px"},
    {"nombre": "Mensaje", "ancho": "auto"},
]


def _fila_validacion(reg: dict) -> rx.Component:
    """Fila de la tabla de preview."""
    return rx.table.row(
        rx.table.cell(
            rx.text(reg["fila"], size="2"),
        ),
        rx.table.cell(
            rx.text(reg["curp"], size="2", weight="medium"),
        ),
        rx.table.cell(
            badge_resultado(reg["resultado"]),
        ),
        rx.table.cell(
            rx.text(reg["mensaje"], size="2", color="gray"),
        ),
    )


def paso_2_preview() -> rx.Component:
    """Paso 2: resumen de validacion y tabla de registros."""
    return rx.vstack(
        # Cards resumen
        rx.hstack(
            card_resumen(
                titulo="Validos",
                valor=AltaMasivaState.total_validos,
                color_scheme="green",
                icono="circle-check",
            ),
            card_resumen(
                titulo="Reingresos",
                valor=AltaMasivaState.total_reingresos,
                color_scheme="yellow",
                icono="rotate-ccw",
            ),
            card_resumen(
                titulo="Errores",
                valor=AltaMasivaState.total_errores,
                color_scheme="red",
                icono="circle-x",
            ),
            width="100%",
            spacing="4",
            flex_wrap="wrap",
        ),

        # Mensaje si no se puede procesar
        rx.cond(
            ~AltaMasivaState.puede_procesar,
            rx.callout(
                "No hay registros validos para procesar. Corrija los errores y vuelva a subir el archivo.",
                icon="triangle-alert",
                color_scheme="red",
                size="2",
                width="100%",
            ),
        ),

        # Tabla de registros
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.foreach(
                            ENCABEZADOS_PREVIEW,
                            lambda col: rx.table.column_header_cell(
                                col["nombre"],
                                width=col["ancho"],
                            ),
                        ),
                    ),
                ),
                rx.table.body(
                    rx.foreach(
                        AltaMasivaState.registros_preview,
                        _fila_validacion,
                    ),
                ),
                width="100%",
                variant="surface",
            ),
            width="100%",
            overflow_x="auto",
        ),

        rx.text(
            "Archivo: ",
            AltaMasivaState.archivo_nombre,
            " | Total filas: ",
            AltaMasivaState.validacion_total,
            size="2",
            color="gray",
        ),

        # Botones de accion
        rx.hstack(
            rx.button(
                rx.icon("arrow-left", size=16),
                "Cancelar",
                on_click=AltaMasivaState.volver_a_subir,
                variant="outline",
                size="2",
                disabled=AltaMasivaState.procesando,
            ),
            rx.spacer(),
            rx.button(
                rx.cond(
                    AltaMasivaState.procesando,
                    rx.hstack(
                        rx.spinner(size="1"),
                        rx.text("Procesando alta...", size="2"),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.icon("check", size=16),
                        rx.text("Confirmar alta", size="2"),
                        spacing="2",
                        align="center",
                    ),
                ),
                on_click=AltaMasivaState.confirmar_procesamiento,
                size="2",
                color_scheme="teal",
                disabled=~AltaMasivaState.puede_procesar | AltaMasivaState.procesando,
            ),
            width="100%",
        ),

        spacing="4",
        width="100%",
    )
