"""
Componente reutilizable para carga de archivos.

Provee una zona de drop/click para subir imagenes y PDFs,
con lista de archivos existentes y boton de eliminacion.

Uso:
    archivo_uploader(
        upload_id="archivos_requisicion",
        archivos=RequisicionesState.archivos_entidad,
        on_upload=RequisicionesState.handle_upload_archivo,
        on_delete=RequisicionesState.eliminar_archivo_entidad,
        subiendo=RequisicionesState.subiendo_archivo,
    )
"""

import reflex as rx

from app.presentation.theme import Colors, Radius, Spacing


def _archivo_card(archivo: dict, on_delete: callable) -> rx.Component:
    """Tarjeta individual de un archivo existente."""
    return rx.hstack(
        # Icono segun tipo
        rx.cond(
            archivo["tipo_mime"].to(str).contains("image"),
            rx.icon("image", size=18, color=Colors.INFO),
            rx.icon("file-text", size=18, color=Colors.ERROR),
        ),
        # Info del archivo
        rx.vstack(
            rx.text(
                archivo["nombre_original"].to(str),
                size="2",
                weight="medium",
                trim="both",
                style={"maxWidth": "200px", "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"},
            ),
            rx.text(
                rx.cond(
                    archivo["fue_comprimido"].to(bool),
                    rx.text.span(
                        "Comprimido",
                        color=Colors.SUCCESS,
                    ),
                    "",
                ),
                size="1",
                color=Colors.TEXT_SECONDARY,
            ),
            spacing="0",
        ),
        rx.spacer(),
        # Boton eliminar
        rx.tooltip(
            rx.icon_button(
                rx.icon("trash-2", size=14),
                size="1",
                variant="ghost",
                color_scheme="red",
                on_click=lambda: on_delete(archivo["id"].to(int)),
            ),
            content="Eliminar archivo",
        ),
        align="center",
        padding=Spacing.SM,
        border_radius=Radius.MD,
        background=Colors.BACKGROUND,
        width="100%",
    )


def _archivos_list(
    archivos: list,
    on_delete: callable,
) -> rx.Component:
    """Lista de archivos existentes."""
    return rx.cond(
        archivos.length() > 0,
        rx.vstack(
            rx.foreach(
                archivos,
                lambda archivo: _archivo_card(archivo, on_delete),
            ),
            spacing="2",
            width="100%",
        ),
    )


def archivo_uploader(
    upload_id: str,
    archivos: list,
    on_upload: callable,
    on_delete: callable,
    subiendo: bool = False,
    max_archivos: int = 5,
) -> rx.Component:
    """
    Componente reutilizable para carga de archivos.

    Args:
        upload_id: ID unico para la zona de upload
        archivos: Lista de archivos existentes (list[dict])
        on_upload: Handler del state para procesar archivos subidos
        on_delete: Handler del state para eliminar un archivo
        subiendo: Si se esta subiendo un archivo
        max_archivos: Maximo de archivos permitidos
    """
    return rx.vstack(
        # Archivos existentes
        _archivos_list(archivos, on_delete),

        # Zona de upload
        rx.upload(
            rx.vstack(
                rx.cond(
                    subiendo,
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text("Subiendo archivo...", size="2", color=Colors.TEXT_SECONDARY),
                        align="center",
                        spacing="2",
                    ),
                    rx.vstack(
                        rx.icon("upload", size=24, color=Colors.PRIMARY),
                        rx.text(
                            "Click o arrastra archivos aqui",
                            size="2",
                            weight="medium",
                        ),
                        rx.text(
                            "JPG, PNG o PDF",
                            size="1",
                            color=Colors.TEXT_SECONDARY,
                        ),
                        align="center",
                        spacing="1",
                    ),
                ),
                align="center",
                justify="center",
                padding=Spacing.LG,
                width="100%",
            ),
            id=upload_id,
            accept={
                "image/jpeg": [".jpg", ".jpeg"],
                "image/png": [".png"],
                "application/pdf": [".pdf"],
            },
            max_files=max_archivos,
            no_click=subiendo,
            no_drag=subiendo,
            border=f"2px dashed {Colors.BORDER_STRONG}",
            border_radius=Radius.MD,
            cursor=rx.cond(subiendo, "wait", "pointer"),
            _hover={"borderColor": Colors.PRIMARY, "background": Colors.PRIMARY_LIGHTER},
            width="100%",
        ),

        # Archivos seleccionados (pendientes de subir)
        rx.cond(
            rx.selected_files(upload_id).length() > 0,
            rx.vstack(
                rx.foreach(
                    rx.selected_files(upload_id),
                    lambda file: rx.text(file, size="1", color=Colors.TEXT_SECONDARY),
                ),
                rx.button(
                    rx.cond(
                        subiendo,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Cargando..."),
                            spacing="2",
                            align="center",
                        ),
                        "Subir archivos",
                    ),
                    on_click=on_upload(
                        rx.upload_files(upload_id=upload_id),
                    ),
                    disabled=subiendo,
                    size="2",
                    variant="soft",
                ),
                spacing="2",
                width="100%",
            ),
        ),

        spacing="3",
        width="100%",
    )


def _archivo_visor_card(archivo: dict, on_ver: callable) -> rx.Component:
    """Tarjeta readonly de un archivo con boton para ver."""
    return rx.hstack(
        # Icono segun tipo
        rx.cond(
            archivo["tipo_mime"].to(str).contains("image"),
            rx.icon("image", size=18, color=Colors.INFO),
            rx.icon("file-text", size=18, color=Colors.ERROR),
        ),
        # Info del archivo
        rx.vstack(
            rx.text(
                archivo["nombre_original"].to(str),
                size="2",
                weight="medium",
                trim="both",
                style={"maxWidth": "250px", "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"},
            ),
            rx.cond(
                archivo["fue_comprimido"].to(bool),
                rx.badge("Comprimido", color_scheme="green", size="1"),
                rx.fragment(),
            ),
            spacing="0",
        ),
        rx.spacer(),
        # Boton ver
        rx.tooltip(
            rx.icon_button(
                rx.icon("eye", size=14),
                size="1",
                variant="ghost",
                color_scheme="blue",
                on_click=lambda: on_ver(archivo),
            ),
            content="Ver archivo",
        ),
        align="center",
        padding=Spacing.SM,
        border_radius=Radius.MD,
        background=Colors.BACKGROUND,
        width="100%",
    )


def archivo_visor(
    archivos: list,
    on_ver: callable,
) -> rx.Component:
    """
    Visor readonly de archivos adjuntos (sin upload).

    Args:
        archivos: Lista de archivos existentes (list[dict])
        on_ver: Handler para ver/abrir un archivo
    """
    return rx.vstack(
        rx.cond(
            archivos.length() > 0,
            rx.vstack(
                rx.foreach(
                    archivos,
                    lambda archivo: _archivo_visor_card(archivo, on_ver),
                ),
                spacing="2",
                width="100%",
            ),
            rx.callout(
                "No hay archivos adjuntos en esta requisicion.",
                icon="info",
                color_scheme="gray",
                size="1",
            ),
        ),
        spacing="3",
        width="100%",
        pointer_events="auto",
    )
