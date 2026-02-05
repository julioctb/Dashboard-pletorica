"""
Paso 1: Subir archivo CSV/Excel.
"""
import reflex as rx

from app.presentation.theme import Colors

from .state import AltaMasivaState, UPLOAD_ID


def paso_1_subir() -> rx.Component:
    """Paso 1: zona de upload y botones de plantilla."""
    return rx.vstack(
        # Zona de upload
        rx.upload(
            rx.vstack(
                rx.cond(
                    AltaMasivaState.validando_archivo,
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text("Validando archivo...", size="2", color="gray"),
                        align="center",
                        spacing="2",
                    ),
                    rx.vstack(
                        rx.icon("upload", size=32, color="var(--teal-9)"),
                        rx.text(
                            "Click o arrastra tu archivo CSV o Excel",
                            size="3",
                            weight="medium",
                            color=Colors.TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Formatos: .csv, .xlsx, .xls | Maximo 500 filas, 5MB",
                            size="2",
                            color=Colors.TEXT_MUTED,
                        ),
                        align="center",
                        spacing="2",
                    ),
                ),
                align="center",
                justify="center",
                padding="40px",
                width="100%",
            ),
            id=UPLOAD_ID,
            accept={
                "text/csv": [".csv"],
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                "application/vnd.ms-excel": [".xls"],
            },
            max_files=1,
            no_click=AltaMasivaState.validando_archivo,
            no_drag=AltaMasivaState.validando_archivo,
            border=f"2px dashed var(--gray-6)",
            border_radius="8px",
            cursor=rx.cond(AltaMasivaState.validando_archivo, "wait", "pointer"),
            _hover={"borderColor": "var(--teal-8)", "background": "var(--teal-2)"},
            width="100%",
        ),

        # Archivos seleccionados + boton validar
        rx.cond(
            rx.selected_files(UPLOAD_ID).length() > 0,
            rx.vstack(
                rx.hstack(
                    rx.icon("file", size=16, color="var(--teal-9)"),
                    rx.foreach(
                        rx.selected_files(UPLOAD_ID),
                        lambda f: rx.text(f, size="2", color=Colors.TEXT_SECONDARY),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.button(
                    rx.cond(
                        AltaMasivaState.validando_archivo,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Validando archivo...", size="2"),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.icon("circle-check", size=16),
                            rx.text("Validar archivo", size="2"),
                            spacing="2",
                            align="center",
                        ),
                    ),
                    on_click=AltaMasivaState.handle_upload(
                        rx.upload_files(upload_id=UPLOAD_ID),
                    ),
                    disabled=AltaMasivaState.validando_archivo,
                    size="2",
                    color_scheme="teal",
                ),
                spacing="3",
                width="100%",
                align="start",
            ),
        ),

        # Error
        rx.cond(
            AltaMasivaState.archivo_error != "",
            rx.callout(
                AltaMasivaState.archivo_error,
                icon="triangle-alert",
                color_scheme="red",
                size="1",
                width="100%",
            ),
        ),

        # Separador
        rx.separator(),

        # Botones plantilla
        rx.vstack(
            rx.text(
                "Descargar plantilla",
                size="2",
                weight="bold",
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                "Usa estas plantillas para llenar los datos de tus empleados",
                size="2",
                color=Colors.TEXT_MUTED,
            ),
            rx.hstack(
                rx.button(
                    rx.icon("file-spreadsheet", size=16),
                    "Plantilla Excel",
                    on_click=AltaMasivaState.descargar_plantilla_excel,
                    variant="outline",
                    size="2",
                    color_scheme="green",
                ),
                rx.button(
                    rx.icon("file-text", size=16),
                    "Plantilla CSV",
                    on_click=AltaMasivaState.descargar_plantilla_csv,
                    variant="outline",
                    size="2",
                ),
                spacing="3",
            ),
            spacing="2",
        ),

        spacing="4",
        width="100%",
        max_width="600px",
        margin_x="auto",
    )
