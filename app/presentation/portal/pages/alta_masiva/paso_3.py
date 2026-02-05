"""
Paso 3: Resultados del procesamiento.
"""
import reflex as rx

from app.presentation.theme import Colors

from .state import AltaMasivaState
from .components import card_resumen, badge_resultado


ENCABEZADOS_RESULTADOS = [
    {"nombre": "Fila", "ancho": "60px"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Resultado", "ancho": "120px"},
    {"nombre": "Clave", "ancho": "120px"},
    {"nombre": "Mensaje", "ancho": "auto"},
]


def _fila_resultado(det: dict) -> rx.Component:
    """Fila de la tabla de resultados."""
    return rx.table.row(
        rx.table.cell(
            rx.text(det["fila"], size="2"),
        ),
        rx.table.cell(
            rx.text(det["curp"], size="2", weight="medium"),
        ),
        rx.table.cell(
            badge_resultado(det["resultado"]),
        ),
        rx.table.cell(
            rx.text(
                rx.cond(det["clave"], det["clave"], "-"),
                size="2",
                color=Colors.PORTAL_PRIMARY_TEXT,
                weight="medium",
            ),
        ),
        rx.table.cell(
            rx.text(det["mensaje"], size="2", color=Colors.TEXT_SECONDARY),
        ),
    )


def paso_3_resultados() -> rx.Component:
    """Paso 3: resultados del procesamiento."""
    return rx.vstack(
        # Cards resumen
        rx.hstack(
            card_resumen(
                titulo="Creados",
                valor=AltaMasivaState.resultado_creados,
                color_scheme="green",
                icono="user-plus",
            ),
            card_resumen(
                titulo="Reingresados",
                valor=AltaMasivaState.resultado_reingresados,
                color_scheme="yellow",
                icono="rotate-ccw",
            ),
            card_resumen(
                titulo="Errores",
                valor=AltaMasivaState.resultado_errores_count,
                color_scheme="red",
                icono="circle-x",
            ),
            width="100%",
            spacing="4",
            flex_wrap="wrap",
        ),

        # Tabla de detalles
        rx.cond(
            AltaMasivaState.resultado_detalles.length() > 0,
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.foreach(
                                ENCABEZADOS_RESULTADOS,
                                lambda col: rx.table.column_header_cell(
                                    col["nombre"],
                                    width=col["ancho"],
                                ),
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(
                            AltaMasivaState.resultado_detalles,
                            _fila_resultado,
                        ),
                    ),
                    width="100%",
                    variant="surface",
                ),
                width="100%",
                overflow_x="auto",
            ),
        ),

        # Botones
        rx.hstack(
            rx.button(
                rx.icon("download", size=16),
                "Descargar reporte",
                on_click=AltaMasivaState.descargar_reporte,
                variant="outline",
                size="2",
                color_scheme="blue",
            ),
            rx.spacer(),
            rx.button(
                rx.icon("upload", size=16),
                "Nueva carga",
                on_click=AltaMasivaState.volver_a_subir,
                size="2",
                color_scheme="teal",
            ),
            width="100%",
        ),

        spacing="4",
        width="100%",
    )
