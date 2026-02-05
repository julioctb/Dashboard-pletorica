"""
State para el wizard de alta masiva.
"""
import base64
import reflex as rx
from typing import List

from app.presentation.portal.state.portal_state import PortalState
from app.services import (
    alta_masiva_service,
    plantilla_service,
    reporte_alta_masiva_service,
)
from app.entities.alta_masiva import (
    ResultadoValidacion,
    ResultadoProcesamiento,
    RegistroValidado,
    DetalleResultado,
)


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
