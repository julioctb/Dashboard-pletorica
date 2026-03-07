"""Mixin reusable para alta masiva de empleados en pantallas del portal."""

import base64
from typing import List

import reflex as rx

from app.entities.alta_masiva import (
    DetalleResultado,
    RegistroValidado,
    ResultadoProcesamiento,
    ResultadoValidacion,
)
from app.services import (
    alta_masiva_service,
    plantilla_service,
    reporte_alta_masiva_service,
)

EMPLOYEE_BULK_UPLOAD_ID = "employee_bulk_upload"


class EmployeeBulkUploadStateMixin:
    """Contrato compartido para flujos inline de alta masiva de empleados."""

    mostrar_panel_alta_masiva: bool = False
    alta_masiva_paso_actual: int = 1
    alta_masiva_archivo_nombre: str = ""
    alta_masiva_archivo_error: str = ""
    alta_masiva_validando_archivo: bool = False
    alta_masiva_validacion_total: int = 0
    alta_masiva_validacion_validos: List[dict] = []
    alta_masiva_validacion_reingresos: List[dict] = []
    alta_masiva_validacion_errores: List[dict] = []
    alta_masiva_procesando: bool = False
    alta_masiva_resultado_creados: int = 0
    alta_masiva_resultado_reingresados: int = 0
    alta_masiva_resultado_errores_count: int = 0
    alta_masiva_resultado_detalles: List[dict] = []
    _alta_masiva_cache_validos: List[dict] = []
    _alta_masiva_cache_reingresos: List[dict] = []

    @staticmethod
    def _descargar_bytes(data: bytes, media_type: str, filename: str):
        """Convierte bytes a data URL para descarga directa."""
        b64 = base64.b64encode(data).decode()
        return rx.download(url=f"data:{media_type};base64,{b64}", filename=filename)

    @staticmethod
    def _serializar_registros(registros: list) -> List[dict]:
        """Serializa entidades Pydantic del flujo de alta masiva."""
        return [registro.model_dump(mode="json") for registro in registros]

    def _query_solicita_alta_masiva(self) -> bool:
        """Indica si la URL actual pide abrir la sección de alta masiva."""
        query_params = self.router_data.get("query", {}) or {}
        valor = str(query_params.get("alta_masiva", "")).strip().lower()
        return valor in {"1", "true", "si", "yes"}

    @staticmethod
    def build_alta_masiva_reset_values(
        *,
        mantener_panel_abierto: bool,
    ) -> dict[str, object]:
        """Valores base para reiniciar el flujo inline de alta masiva."""
        return {
            "mostrar_panel_alta_masiva": mantener_panel_abierto,
            "alta_masiva_paso_actual": 1,
            "alta_masiva_archivo_nombre": "",
            "alta_masiva_archivo_error": "",
            "alta_masiva_validando_archivo": False,
            "alta_masiva_validacion_total": 0,
            "alta_masiva_validacion_validos": [],
            "alta_masiva_validacion_reingresos": [],
            "alta_masiva_validacion_errores": [],
            "alta_masiva_procesando": False,
            "alta_masiva_resultado_creados": 0,
            "alta_masiva_resultado_reingresados": 0,
            "alta_masiva_resultado_errores_count": 0,
            "alta_masiva_resultado_detalles": [],
            "_alta_masiva_cache_validos": [],
            "_alta_masiva_cache_reingresos": [],
        }

    async def handle_upload_alta_masiva(self, files: list[rx.UploadFile]):
        """Recibe el archivo, lo valida y construye el preview inline."""
        if not files:
            self.alta_masiva_archivo_error = "No se selecciono ningun archivo"
            return

        self.alta_masiva_archivo_error = ""
        self.alta_masiva_validando_archivo = True
        yield

        try:
            file = files[0]
            contenido = await file.read()
            nombre = file.filename or "empleados"

            if len(contenido) > 5 * 1024 * 1024:
                self.alta_masiva_archivo_error = "El archivo excede el limite de 5MB"
                return

            resultado = await alta_masiva_service.validar_archivo(
                contenido=contenido,
                nombre_archivo=nombre,
                empresa_id=self.id_empresa_actual,
            )

            self.alta_masiva_archivo_nombre = nombre
            self.alta_masiva_validacion_total = resultado.total_filas
            self.alta_masiva_validacion_validos = self._serializar_registros(
                resultado.validos
            )
            self.alta_masiva_validacion_reingresos = self._serializar_registros(
                resultado.reingresos
            )
            self.alta_masiva_validacion_errores = self._serializar_registros(
                resultado.errores
            )
            self._alta_masiva_cache_validos = self.alta_masiva_validacion_validos
            self._alta_masiva_cache_reingresos = self.alta_masiva_validacion_reingresos
            self.alta_masiva_paso_actual = 2
        except Exception as e:
            self.alta_masiva_archivo_error = f"Error procesando archivo: {str(e)}"
        finally:
            self.alta_masiva_validando_archivo = False

    def _reconstruir_validacion_alta_masiva(self) -> ResultadoValidacion:
        """Reconstruye el DTO de validación para el paso de procesamiento."""
        return ResultadoValidacion(
            total_filas=self.alta_masiva_validacion_total,
            validos=[RegistroValidado(**d) for d in self._alta_masiva_cache_validos],
            reingresos=[
                RegistroValidado(**d) for d in self._alta_masiva_cache_reingresos
            ],
            errores=[],
        )

    async def _post_procesamiento_alta_masiva(self):
        """Hook opcional para recargar contexto después de procesar."""
        return None

    async def confirmar_alta_masiva(self):
        """Procesa el archivo validado y muestra resultados inline."""
        self.alta_masiva_procesando = True
        yield

        try:
            resultado = await alta_masiva_service.procesar(
                resultado_validacion=self._reconstruir_validacion_alta_masiva(),
                empresa_id=self.id_empresa_actual,
            )

            self.alta_masiva_resultado_creados = resultado.creados
            self.alta_masiva_resultado_reingresados = resultado.reingresados
            self.alta_masiva_resultado_errores_count = resultado.errores
            self.alta_masiva_resultado_detalles = self._serializar_registros(
                resultado.detalles
            )
            await self._post_procesamiento_alta_masiva()
            self.alta_masiva_paso_actual = 3
        except Exception as e:
            yield rx.toast.error(
                f"Error al procesar: {str(e)}",
                position="top-center",
            )
        finally:
            self.alta_masiva_procesando = False

    def descargar_plantilla_excel_alta_masiva(self):
        """Descarga la plantilla Excel para la carga masiva."""
        try:
            return EmployeeBulkUploadStateMixin._descargar_bytes(
                plantilla_service.generar_excel(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "plantilla_alta_masiva.xlsx",
            )
        except Exception as e:
            return rx.toast.error(
                f"Error generando plantilla: {str(e)}",
                position="top-center",
            )

    def descargar_plantilla_csv_alta_masiva(self):
        """Descarga la plantilla CSV para la carga masiva."""
        try:
            return EmployeeBulkUploadStateMixin._descargar_bytes(
                plantilla_service.generar_csv(),
                "text/csv",
                "plantilla_alta_masiva.csv",
            )
        except Exception as e:
            return rx.toast.error(
                f"Error generando plantilla: {str(e)}",
                position="top-center",
            )

    def descargar_reporte_alta_masiva(self):
        """Descarga el reporte del último procesamiento masivo."""
        try:
            resultado = ResultadoProcesamiento(
                creados=self.alta_masiva_resultado_creados,
                reingresados=self.alta_masiva_resultado_reingresados,
                errores=self.alta_masiva_resultado_errores_count,
                detalles=[
                    DetalleResultado(**d) for d in self.alta_masiva_resultado_detalles
                ],
            )
            data = reporte_alta_masiva_service.generar_reporte_procesamiento(
                resultado=resultado,
                empresa_nombre=self.nombre_empresa_actual,
            )
            return EmployeeBulkUploadStateMixin._descargar_bytes(
                data,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "reporte_alta_masiva.xlsx",
            )
        except Exception as e:
            return rx.toast.error(
                f"Error generando reporte: {str(e)}",
                position="top-center",
            )

    @rx.var
    def alta_masiva_total_validos(self) -> int:
        return len(self.alta_masiva_validacion_validos)

    @rx.var
    def alta_masiva_total_reingresos(self) -> int:
        return len(self.alta_masiva_validacion_reingresos)

    @rx.var
    def alta_masiva_total_errores(self) -> int:
        return len(self.alta_masiva_validacion_errores)

    @rx.var
    def alta_masiva_puede_procesar(self) -> bool:
        return (
            len(self.alta_masiva_validacion_validos) > 0
            or len(self.alta_masiva_validacion_reingresos) > 0
        )

    @rx.var
    def alta_masiva_registros_preview(self) -> List[dict]:
        """Lista combinada y ordenada para la tabla de preview."""
        todos = list(self.alta_masiva_validacion_validos)
        todos.extend(self.alta_masiva_validacion_reingresos)
        todos.extend(self.alta_masiva_validacion_errores)
        todos.sort(key=lambda item: item.get("fila", 0))
        return todos
