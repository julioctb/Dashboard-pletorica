"""
Pagina Alta Masiva del portal de cliente.

Wizard de 3 pasos para carga masiva de empleados:
1. Subir archivo CSV/Excel
2. Preview de validacion (validos, reingresos, errores)
3. Resultados del procesamiento
"""
import base64
import reflex as rx
from typing import List

from app.presentation.portal.state.portal_state import PortalState
from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Colors, Typography, Spacing
from app.services import (
    alta_masiva_service,
    plantilla_service,
    reporte_alta_masiva_service,
)
from app.entities.alta_masiva import (
    ResultadoValidacion,
    ResultadoProcesamiento,
    RegistroValidado,
    ResultadoFila,
)
from app.core.exceptions import DatabaseError


# =============================================================================
# STATE
# =============================================================================

UPLOAD_ID = "alta_masiva_upload"


class AltaMasivaState(PortalState):
    """State para el wizard de alta masiva."""

    # Paso actual: 1=subir, 2=preview, 3=resultados
    paso_actual: int = 1

    # --- Paso 1: Upload ---
    archivo_nombre: str = ""
    archivo_error: str = ""
    validando_archivo: bool = False

    # --- Paso 2: Preview (validacion) ---
    validacion_total: int = 0
    validacion_validos: List[dict] = []
    validacion_reingresos: List[dict] = []
    validacion_errores: List[dict] = []

    # --- Paso 3: Resultados ---
    procesando: bool = False
    resultado_creados: int = 0
    resultado_reingresados: int = 0
    resultado_errores_count: int = 0
    resultado_detalles: List[dict] = []

    # Cache interno para reconstruir ResultadoValidacion en paso 3
    _cache_validos: List[dict] = []
    _cache_reingresos: List[dict] = []

    # ========================
    # SETTERS
    # ========================
    def set_archivo_error(self, value: str):
        self.archivo_error = value

    # ========================
    # MONTAJE
    # ========================
    async def on_mount_alta_masiva(self):
        resultado = await self.on_mount_portal()
        if resultado:
            return resultado
        self._reset_wizard()

    def _reset_wizard(self):
        """Resetea todo el wizard al paso 1."""
        self.paso_actual = 1
        self.archivo_nombre = ""
        self.archivo_error = ""
        self.validando_archivo = False
        self.validacion_total = 0
        self.validacion_validos = []
        self.validacion_reingresos = []
        self.validacion_errores = []
        self.procesando = False
        self.resultado_creados = 0
        self.resultado_reingresados = 0
        self.resultado_errores_count = 0
        self.resultado_detalles = []
        self._cache_validos = []
        self._cache_reingresos = []

    # ========================
    # PASO 1: UPLOAD
    # ========================
    async def handle_upload(self, files: list[rx.UploadFile]):
        """Recibe el archivo, lo valida y pasa al paso 2."""
        if not files:
            self.archivo_error = "No se selecciono ningun archivo"
            return

        self.archivo_error = ""
        self.validando_archivo = True
        yield

        try:
            file = files[0]
            contenido = await file.read()
            nombre = file.filename

            # Validar tamano (5MB)
            if len(contenido) > 5 * 1024 * 1024:
                self.archivo_error = "El archivo excede el limite de 5MB"
                self.validando_archivo = False
                return

            self.archivo_nombre = nombre

            # Llamar servicio de validacion
            resultado = await alta_masiva_service.validar_archivo(
                contenido=contenido,
                nombre_archivo=nombre,
                empresa_id=self.id_empresa_actual,
            )

            # Serializar resultados para el state
            self.validacion_total = resultado.total_filas
            self.validacion_validos = [
                r.model_dump(mode='json') for r in resultado.validos
            ]
            self.validacion_reingresos = [
                r.model_dump(mode='json') for r in resultado.reingresos
            ]
            self.validacion_errores = [
                r.model_dump(mode='json') for r in resultado.errores
            ]

            # Cache para reconstruccion en paso 3
            self._cache_validos = self.validacion_validos
            self._cache_reingresos = self.validacion_reingresos

            # Pasar a paso 2
            self.paso_actual = 2

        except Exception as e:
            self.archivo_error = f"Error procesando archivo: {str(e)}"
        finally:
            self.validando_archivo = False

    # ========================
    # PASO 2 -> 3: PROCESAR
    # ========================
    async def confirmar_procesamiento(self):
        """Procesa los registros validados y pasa al paso 3."""
        self.procesando = True
        yield

        try:
            # Reconstruir ResultadoValidacion desde cache
            resultado_validacion = ResultadoValidacion(
                total_filas=self.validacion_total,
                validos=[RegistroValidado(**d) for d in self._cache_validos],
                reingresos=[RegistroValidado(**d) for d in self._cache_reingresos],
                errores=[],
            )

            resultado = await alta_masiva_service.procesar(
                resultado_validacion=resultado_validacion,
                empresa_id=self.id_empresa_actual,
            )

            # Guardar resultados
            self.resultado_creados = resultado.creados
            self.resultado_reingresados = resultado.reingresados
            self.resultado_errores_count = resultado.errores
            self.resultado_detalles = [
                d.model_dump(mode='json') for d in resultado.detalles
            ]

            # Pasar a paso 3
            self.paso_actual = 3

        except Exception as e:
            yield rx.toast.error(
                f"Error al procesar: {str(e)}",
                position="top-center",
            )
        finally:
            self.procesando = False

    # ========================
    # NAVEGACION
    # ========================
    def volver_a_subir(self):
        """Reset y volver al paso 1."""
        self._reset_wizard()

    # ========================
    # DESCARGAS
    # ========================
    def descargar_plantilla_excel(self):
        """Genera y descarga la plantilla Excel."""
        try:
            data = plantilla_service.generar_excel()
            b64 = base64.b64encode(data).decode()
            data_url = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}"
            return rx.download(url=data_url, filename="plantilla_alta_masiva.xlsx")
        except Exception as e:
            return rx.toast.error(
                f"Error generando plantilla: {str(e)}",
                position="top-center",
            )

    def descargar_plantilla_csv(self):
        """Genera y descarga la plantilla CSV."""
        try:
            data = plantilla_service.generar_csv()
            b64 = base64.b64encode(data).decode()
            data_url = f"data:text/csv;base64,{b64}"
            return rx.download(url=data_url, filename="plantilla_alta_masiva.csv")
        except Exception as e:
            return rx.toast.error(
                f"Error generando plantilla: {str(e)}",
                position="top-center",
            )

    def descargar_reporte(self):
        """Genera y descarga el reporte de resultados."""
        try:
            from app.entities.alta_masiva import DetalleResultado
            resultado = ResultadoProcesamiento(
                creados=self.resultado_creados,
                reingresados=self.resultado_reingresados,
                errores=self.resultado_errores_count,
                detalles=[DetalleResultado(**d) for d in self.resultado_detalles],
            )
            data = reporte_alta_masiva_service.generar_reporte_procesamiento(
                resultado=resultado,
                empresa_nombre=self.nombre_empresa_actual,
            )
            b64 = base64.b64encode(data).decode()
            data_url = f"data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}"
            return rx.download(url=data_url, filename="reporte_alta_masiva.xlsx")
        except Exception as e:
            return rx.toast.error(
                f"Error generando reporte: {str(e)}",
                position="top-center",
            )

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def total_validos(self) -> int:
        return len(self.validacion_validos)

    @rx.var
    def total_reingresos(self) -> int:
        return len(self.validacion_reingresos)

    @rx.var
    def total_errores(self) -> int:
        return len(self.validacion_errores)

    @rx.var
    def puede_procesar(self) -> bool:
        return len(self.validacion_validos) > 0 or len(self.validacion_reingresos) > 0

    @rx.var
    def registros_preview(self) -> List[dict]:
        """Todos los registros combinados y ordenados por fila para la tabla preview."""
        todos = []
        for r in self.validacion_validos:
            todos.append(r)
        for r in self.validacion_reingresos:
            todos.append(r)
        for r in self.validacion_errores:
            todos.append(r)
        todos.sort(key=lambda x: x.get("fila", 0))
        return todos


# =============================================================================
# COMPONENTES PRIVADOS
# =============================================================================

def _indicador_pasos() -> rx.Component:
    """Indicador visual de los 3 pasos del wizard."""

    def _paso(numero: int, titulo: str) -> rx.Component:
        es_activo = AltaMasivaState.paso_actual >= numero
        es_actual = AltaMasivaState.paso_actual == numero

        return rx.hstack(
            rx.center(
                rx.text(str(numero), size="2", weight="bold"),
                width="32px",
                height="32px",
                border_radius="50%",
                background=rx.cond(es_activo, "var(--teal-9)", "var(--gray-4)"),
                color=rx.cond(es_activo, "white", "var(--gray-9)"),
                flex_shrink="0",
            ),
            rx.text(
                titulo,
                size="2",
                weight=rx.cond(es_actual, "bold", "medium"),
                color=rx.cond(es_activo, Colors.TEXT_PRIMARY, Colors.TEXT_MUTED),
                display=rx.breakpoints(initial="none", sm="block"),
            ),
            spacing="2",
            align="center",
        )

    def _conector() -> rx.Component:
        return rx.box(
            height="2px",
            flex="1",
            max_width="80px",
            background="var(--gray-5)",
        )

    return rx.hstack(
        _paso(1, "Subir archivo"),
        _conector(),
        _paso(2, "Validacion"),
        _conector(),
        _paso(3, "Resultados"),
        width="100%",
        max_width="500px",
        justify="center",
        align="center",
        padding_y=Spacing.MD,
        margin_x="auto",
    )


def _card_resumen(
    titulo: str,
    valor: rx.Var,
    color_scheme: str,
    icono: str,
) -> rx.Component:
    """Card de resumen con contador."""
    color_map = {
        "green": ("var(--green-3)", "var(--green-9)", "var(--green-11)"),
        "yellow": ("var(--yellow-3)", "var(--yellow-9)", "var(--yellow-11)"),
        "red": ("var(--red-3)", "var(--red-9)", "var(--red-11)"),
        "blue": ("var(--blue-3)", "var(--blue-9)", "var(--blue-11)"),
    }
    bg, icon_color, text_color = color_map.get(color_scheme, color_map["blue"])

    return rx.box(
        rx.hstack(
            rx.center(
                rx.icon(icono, size=20, color=icon_color),
                width="40px",
                height="40px",
                border_radius="10px",
                background=bg,
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(titulo, size="1", color=Colors.TEXT_MUTED, weight="medium"),
                rx.text(valor, size="5", weight="bold", color=text_color),
                spacing="0",
            ),
            spacing="3",
            align="center",
        ),
        padding=Spacing.MD,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
        flex="1",
        min_width="140px",
    )


# =============================================================================
# PASO 1: SUBIR ARCHIVO
# =============================================================================

def _paso_1_subir() -> rx.Component:
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


# =============================================================================
# PASO 2: PREVIEW VALIDACION
# =============================================================================

def _badge_resultado(resultado: str) -> rx.Component:
    """Badge coloreado segun resultado de validacion."""
    return rx.match(
        resultado,
        ("VALIDO", rx.badge("Valido", color_scheme="green", variant="soft", size="1")),
        ("REINGRESO", rx.badge("Reingreso", color_scheme="yellow", variant="soft", size="1")),
        ("ERROR", rx.badge("Error", color_scheme="red", variant="soft", size="1")),
        rx.badge(resultado, size="1"),
    )


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
            _badge_resultado(reg["resultado"]),
        ),
        rx.table.cell(
            rx.text(reg["mensaje"], size="2", color="gray"),
        ),
    )


ENCABEZADOS_PREVIEW = [
    {"nombre": "Fila", "ancho": "60px"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Resultado", "ancho": "120px"},
    {"nombre": "Mensaje", "ancho": "auto"},
]


def _paso_2_preview() -> rx.Component:
    """Paso 2: resumen de validacion y tabla de registros."""
    return rx.vstack(
        # Cards resumen
        rx.hstack(
            _card_resumen(
                titulo="Validos",
                valor=AltaMasivaState.total_validos,
                color_scheme="green",
                icono="circle-check",
            ),
            _card_resumen(
                titulo="Reingresos",
                valor=AltaMasivaState.total_reingresos,
                color_scheme="yellow",
                icono="rotate-ccw",
            ),
            _card_resumen(
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


# =============================================================================
# PASO 3: RESULTADOS
# =============================================================================

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
            _badge_resultado(det["resultado"]),
        ),
        rx.table.cell(
            rx.text(
                rx.cond(det["clave"], det["clave"], "-"),
                size="2",
                color="var(--teal-11)",
                weight="medium",
            ),
        ),
        rx.table.cell(
            rx.text(det["mensaje"], size="2", color="gray"),
        ),
    )


ENCABEZADOS_RESULTADOS = [
    {"nombre": "Fila", "ancho": "60px"},
    {"nombre": "CURP", "ancho": "200px"},
    {"nombre": "Resultado", "ancho": "120px"},
    {"nombre": "Clave", "ancho": "120px"},
    {"nombre": "Mensaje", "ancho": "auto"},
]


def _paso_3_resultados() -> rx.Component:
    """Paso 3: resultados del procesamiento."""
    return rx.vstack(
        # Cards resumen
        rx.hstack(
            _card_resumen(
                titulo="Creados",
                valor=AltaMasivaState.resultado_creados,
                color_scheme="green",
                icono="user-plus",
            ),
            _card_resumen(
                titulo="Reingresados",
                valor=AltaMasivaState.resultado_reingresados,
                color_scheme="yellow",
                icono="rotate-ccw",
            ),
            _card_resumen(
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


# =============================================================================
# PAGINA
# =============================================================================

def alta_masiva_page() -> rx.Component:
    """Pagina de alta masiva de empleados."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Alta Masiva",
                subtitulo="Carga masiva de empleados desde archivo",
                icono="upload",
            ),
            content=rx.vstack(
                _indicador_pasos(),
                rx.match(
                    AltaMasivaState.paso_actual,
                    (1, _paso_1_subir()),
                    (2, _paso_2_preview()),
                    (3, _paso_3_resultados()),
                    _paso_1_subir(),
                ),
                width="100%",
                spacing="6",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=AltaMasivaState.on_mount_alta_masiva,
    )
