"""Mixin reusable para alta masiva de empleados en pantallas del portal."""

from typing import List

import reflex as rx

from app.core.ui_helpers import rango_paginacion
from app.domain.models.alta_masiva import (
    DetalleResultado,
    RegistroValidado,
    ResultadoProcesamiento,
    ResultadoValidacion,
)
from app.modules.empleados.application import (
    alta_masiva_service,
    plantilla_service,
    reporte_alta_masiva_service,
)

EMPLOYEE_BULK_UPLOAD_ID = "employee_bulk_upload"
EMPLOYEE_BULK_UPLOAD_PAGE_SIZE = 20


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
    alta_masiva_preview_rows: List[dict] = []
    alta_masiva_preview_pagina: int = 1
    alta_masiva_procesando: bool = False
    alta_masiva_resultado_creados: int = 0
    alta_masiva_resultado_reingresados: int = 0
    alta_masiva_resultado_errores_count: int = 0
    alta_masiva_resultado_detalles: List[dict] = []
    alta_masiva_resultados_pagina: int = 1
    alta_masiva_por_pagina: int = EMPLOYEE_BULK_UPLOAD_PAGE_SIZE
    _alta_masiva_cache_validos: List[dict] = []
    _alta_masiva_cache_reingresos: List[dict] = []

    @staticmethod
    def _descargar_bytes(data: bytes, media_type: str, filename: str):
        """Descarga bytes generados en servidor con el MIME correcto."""
        return rx.download(data=data, filename=filename, mime_type=media_type)

    @staticmethod
    def _serializar_registros(registros: list) -> List[dict]:
        """Serializa entidades Pydantic del flujo de alta masiva."""
        return [
            EmployeeBulkUploadStateMixin._normalizar_registro_serializado(
                registro.model_dump(mode="json")
            )
            for registro in registros
        ]

    @staticmethod
    def _inferir_campo_error(mensaje: str) -> str:
        """Deriva un campo visible cuando la validación solo entrega texto."""
        texto = str(mensaje or "").lower()
        campos = [
            ("clabe", "CLABE Interbancaria"),
            ("curp", "CURP"),
            ("rfc", "RFC"),
            ("nss", "NSS"),
            ("fecha de nacimiento", "Fecha Nacimiento"),
            ("fecha nacimiento", "Fecha Nacimiento"),
            ("fecha de ingreso", "Fecha Ingreso"),
            ("fecha ingreso", "Fecha Ingreso"),
            ("codigo postal", "Codigo Postal"),
            ("código postal", "Codigo Postal"),
            ("cuenta bancaria", "Cuenta Bancaria"),
            ("banco", "Banco"),
            ("telefono", "Telefono"),
            ("teléfono", "Telefono"),
        ]
        for clave, campo in campos:
            if clave in texto:
                return campo
        return "Validacion"

    @staticmethod
    def _normalizar_registro_serializado(registro: dict) -> dict:
        """Asegura campos visibles y estables para mostrar errores en UI."""
        item = dict(registro or {})
        datos = item.get("datos") or {}
        errores = item.get("errores") or []

        nombre_completo = " ".join(
            parte
            for parte in [
                str(datos.get("nombre") or "").strip(),
                str(datos.get("apellido_paterno") or "").strip(),
                str(datos.get("apellido_materno") or "").strip(),
            ]
            if parte
        ).strip()
        mensaje = str(item.get("mensaje") or "").strip()
        if not mensaje and errores:
            mensaje = "; ".join(str(error) for error in errores if str(error).strip())
        if not mensaje:
            mensaje = "Error de validacion sin detalle"

        item["fila"] = item.get("fila") or "-"
        item["curp"] = str(item.get("curp") or datos.get("curp") or "").strip()
        item["nombre_completo"] = nombre_completo or "-"
        item["mensaje_display"] = mensaje
        item["campo_error_display"] = "-"
        if str(item.get("resultado") or "").upper() == "ERROR":
            item["campo_error_display"] = str(
                item.get("campo")
                or item.get("campo_error")
                or EmployeeBulkUploadStateMixin._inferir_campo_error(mensaje)
            ).strip()
        return item

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
            "alta_masiva_preview_rows": [],
            "alta_masiva_preview_pagina": 1,
            "alta_masiva_procesando": False,
            "alta_masiva_resultado_creados": 0,
            "alta_masiva_resultado_reingresados": 0,
            "alta_masiva_resultado_errores_count": 0,
            "alta_masiva_resultado_detalles": [],
            "alta_masiva_resultados_pagina": 1,
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
            self.alta_masiva_preview_pagina = 1
            self._actualizar_preview_paginado_alta_masiva()
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
        if not self._puede_procesar_alta_masiva():
            yield rx.toast.error(
                "Corrija los errores del archivo antes de confirmar la alta.",
                position="top-center",
            )
            return

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
            self.alta_masiva_resultados_pagina = 1
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
        tiene_procesables = (
            len(self.alta_masiva_validacion_validos) > 0
            or len(self.alta_masiva_validacion_reingresos) > 0
        )
        return tiene_procesables and len(self.alta_masiva_validacion_errores) == 0

    def _puede_procesar_alta_masiva(self) -> bool:
        """Permite confirmar solo si no hay errores y hay procesables."""
        tiene_procesables = (
            len(self.alta_masiva_validacion_validos) > 0
            or len(self.alta_masiva_validacion_reingresos) > 0
        )
        return tiene_procesables and len(self.alta_masiva_validacion_errores) == 0

    def _obtener_registros_preview_alta_masiva(self) -> List[dict]:
        """Devuelve errores serializados ordenados para el preview."""
        return sorted(
            self.alta_masiva_validacion_errores,
            key=lambda item: item.get("fila", 0),
        )

    def _actualizar_preview_paginado_alta_masiva(self) -> None:
        """Materializa filas visibles para evitar depender del render reactivo."""
        registros = self._obtener_registros_preview_alta_masiva()
        total_paginas = self._calcular_total_paginas_alta_masiva(
            len(registros),
            self.alta_masiva_por_pagina,
        )
        self.alta_masiva_preview_pagina = max(
            1,
            min(int(self.alta_masiva_preview_pagina or 1), total_paginas),
        )
        self.alta_masiva_preview_rows = self._paginar_alta_masiva(
            registros,
            self.alta_masiva_preview_pagina,
            self.alta_masiva_por_pagina,
        )

    @staticmethod
    def _calcular_total_paginas_alta_masiva(total_items: int, por_pagina: int) -> int:
        if total_items <= 0:
            return 1
        return ((total_items - 1) // max(1, por_pagina)) + 1

    @staticmethod
    def _paginar_alta_masiva(
        items: List[dict], pagina: int, por_pagina: int
    ) -> List[dict]:
        pagina_segura = max(1, int(pagina or 1))
        inicio = (pagina_segura - 1) * max(1, por_pagina)
        fin = inicio + max(1, por_pagina)
        return items[inicio:fin]

    def ir_a_pagina_alta_masiva_preview(self, pagina: int):
        self.alta_masiva_preview_pagina = max(
            1,
            min(int(pagina or 1), self.alta_masiva_total_paginas_preview),
        )
        self._actualizar_preview_paginado_alta_masiva()

    def pagina_anterior_alta_masiva_preview(self):
        self.ir_a_pagina_alta_masiva_preview(self.alta_masiva_preview_pagina - 1)

    def pagina_siguiente_alta_masiva_preview(self):
        self.ir_a_pagina_alta_masiva_preview(self.alta_masiva_preview_pagina + 1)

    def ir_a_pagina_alta_masiva_resultados(self, pagina: int):
        self.alta_masiva_resultados_pagina = max(
            1,
            min(int(pagina or 1), self.alta_masiva_total_paginas_resultados),
        )

    def pagina_anterior_alta_masiva_resultados(self):
        self.ir_a_pagina_alta_masiva_resultados(self.alta_masiva_resultados_pagina - 1)

    def pagina_siguiente_alta_masiva_resultados(self):
        self.ir_a_pagina_alta_masiva_resultados(self.alta_masiva_resultados_pagina + 1)

    @rx.var
    def alta_masiva_preview_pagina_actual(self) -> int:
        return max(
            1,
            min(
                self.alta_masiva_preview_pagina, self.alta_masiva_total_paginas_preview
            ),
        )

    @rx.var
    def alta_masiva_total_paginas_preview(self) -> int:
        return self._calcular_total_paginas_alta_masiva(
            len(self._obtener_registros_preview_alta_masiva()),
            self.alta_masiva_por_pagina,
        )

    @rx.var
    def alta_masiva_paginas_visibles_preview(self) -> List[int]:
        return rango_paginacion(
            self.alta_masiva_preview_pagina_actual,
            self.alta_masiva_total_paginas_preview,
            visible=5,
        )

    @rx.var
    def alta_masiva_resumen_paginacion_preview(self) -> str:
        total = len(self._obtener_registros_preview_alta_masiva())
        if total <= 0:
            return "Sin registros"
        inicio = (
            (self.alta_masiva_preview_pagina_actual - 1) * self.alta_masiva_por_pagina
        ) + 1
        fin = min(
            self.alta_masiva_preview_pagina_actual * self.alta_masiva_por_pagina, total
        )
        return f"Mostrando {inicio}-{fin} de {total} error(es)"

    @rx.var
    def alta_masiva_resultados_pagina_actual(self) -> int:
        return max(
            1,
            min(
                self.alta_masiva_resultados_pagina,
                self.alta_masiva_total_paginas_resultados,
            ),
        )

    @rx.var
    def alta_masiva_total_paginas_resultados(self) -> int:
        return self._calcular_total_paginas_alta_masiva(
            len(self.alta_masiva_resultado_detalles),
            self.alta_masiva_por_pagina,
        )

    @rx.var
    def alta_masiva_resultados_paginados(self) -> List[dict]:
        return self._paginar_alta_masiva(
            self.alta_masiva_resultado_detalles,
            self.alta_masiva_resultados_pagina_actual,
            self.alta_masiva_por_pagina,
        )

    @rx.var
    def alta_masiva_paginas_visibles_resultados(self) -> List[int]:
        return rango_paginacion(
            self.alta_masiva_resultados_pagina_actual,
            self.alta_masiva_total_paginas_resultados,
            visible=5,
        )

    @rx.var
    def alta_masiva_resumen_paginacion_resultados(self) -> str:
        total = len(self.alta_masiva_resultado_detalles)
        if total <= 0:
            return "Sin resultados"
        inicio = (
            (self.alta_masiva_resultados_pagina_actual - 1)
            * self.alta_masiva_por_pagina
        ) + 1
        fin = min(
            self.alta_masiva_resultados_pagina_actual * self.alta_masiva_por_pagina,
            total,
        )
        return f"Mostrando {inicio}-{fin} de {total} resultado(s)"
