"""
Estado del Portal del Cliente - Mis Entregables.
Nuevo flujo: Vista global de todos los entregables del cliente.
Por defecto muestra Pendientes y Rechazados (lo que requiere acción).
"""

import reflex as rx
from typing import List, Optional

from app.presentation.portal.state.portal_state import PortalState
from app.services import entregable_service, archivo_service
from app.entities.archivo import EntidadArchivo, TipoArchivo, OrigenArchivo
from app.core.enums import EstatusEntregable
from app.core.exceptions import BusinessRuleError


class MisEntregablesState(PortalState):
    """Estado para la gestión de entregables del cliente - Vista Global."""

    # =========================================================================
    # DATOS
    # =========================================================================
    contratos: List[dict] = []
    entregables: List[dict] = []
    estadisticas: dict = {}
    entregable_actual: Optional[dict] = None
    archivos_entregable: List[dict] = []

    # =========================================================================
    # UI / FILTROS
    # =========================================================================
    cargando: bool = False
    subiendo_archivo: bool = False
    enviando: bool = False
    mostrar_modal_entregable: bool = False
    # Default: mostrar PENDIENTE y RECHAZADO (requieren acción del cliente)
    filtro_estatus: str = "accion_requerida"
    filtro_contrato_id: str = "all"
    filtro_busqueda: str = ""

    # =========================================================================
    # SETTERS
    # =========================================================================
    def set_filtro_busqueda(self, value: str):
        self.filtro_busqueda = value

    # =========================================================================
    # COMPUTED VARS
    # =========================================================================
    @rx.var
    def tiene_entregables(self) -> bool:
        return len(self.entregables) > 0

    @rx.var
    def entregables_filtrados(self) -> List[dict]:
        """Filtra por búsqueda de texto."""
        resultado = self.entregables
        if self.filtro_busqueda:
            termino = self.filtro_busqueda.lower()
            resultado = [
                e for e in resultado
                if termino in str(e.get("numero_periodo", "")).lower()
                or termino in (e.get("periodo_texto", "") or "").lower()
                or termino in (e.get("contrato_codigo", "") or "").lower()
            ]
        return resultado

    @rx.var
    def total_mostrados(self) -> int:
        return len(self.entregables_filtrados)

    @rx.var
    def opciones_contratos(self) -> List[dict]:
        return [{"value": "all", "label": "Todos los contratos"}] + [
            {"value": str(c["id"]), "label": c["codigo"]} for c in self.contratos
        ]

    # Estadísticas
    @rx.var
    def stats_total(self) -> int:
        return self.estadisticas.get("total", 0)

    @rx.var
    def stats_pendientes(self) -> int:
        return self.estadisticas.get("pendientes", 0)

    @rx.var
    def stats_en_revision(self) -> int:
        return self.estadisticas.get("en_revision", 0)

    @rx.var
    def stats_aprobados(self) -> int:
        return self.estadisticas.get("aprobados", 0)

    @rx.var
    def stats_rechazados(self) -> int:
        return self.estadisticas.get("rechazados", 0)

    @rx.var
    def stats_accion_requerida(self) -> int:
        """Pendientes + Rechazados = lo que requiere acción del cliente."""
        return self.stats_pendientes + self.stats_rechazados

    # Filtros activos
    @rx.var
    def filtro_es_accion_requerida(self) -> bool:
        return self.filtro_estatus == "accion_requerida"

    @rx.var
    def filtro_es_pendiente(self) -> bool:
        return self.filtro_estatus == "PENDIENTE"

    @rx.var
    def filtro_es_en_revision(self) -> bool:
        return self.filtro_estatus == "EN_REVISION"

    @rx.var
    def filtro_es_aprobado(self) -> bool:
        return self.filtro_estatus == "APROBADO"

    @rx.var
    def filtro_es_rechazado(self) -> bool:
        return self.filtro_estatus == "RECHAZADO"

    @rx.var
    def titulo_filtro_actual(self) -> str:
        if self.filtro_estatus == "accion_requerida":
            return "Requieren tu Acción"
        elif self.filtro_estatus == "PENDIENTE":
            return "Pendientes de Entrega"
        elif self.filtro_estatus == "EN_REVISION":
            return "En Revisión por BUAP"
        elif self.filtro_estatus == "APROBADO":
            return "Aprobados"
        elif self.filtro_estatus == "RECHAZADO":
            return "Rechazados - Requieren Corrección"
        return "Mis Entregables"

    # Modal
    @rx.var
    def puede_entregar(self) -> bool:
        if not self.entregable_actual:
            return False
        estatus = self.entregable_actual.get("estatus", "")
        tiene_archivos = len(self.archivos_entregable) > 0
        return estatus in ("PENDIENTE", "RECHAZADO") and tiene_archivos

    @rx.var
    def esta_en_revision(self) -> bool:
        if not self.entregable_actual:
            return False
        return self.entregable_actual.get("estatus") == "EN_REVISION"

    # =========================================================================
    # CARGA DE DATOS
    # =========================================================================
    async def on_load_mis_entregables(self):
        """Verificar auth y cargar entregables de la empresa."""
        resultado = await self.on_mount_portal()
        if resultado:
            return resultado
        if self.id_empresa_actual:
            await self._cargar_contratos()
            await self._cargar_estadisticas()
            await self._cargar_entregables()

    async def _cargar_contratos(self):
        """Carga lista de contratos para el filtro."""
        try:
            from app.services import contrato_service
            contratos = await contrato_service.obtener_por_empresa(self.id_empresa_actual)
            self.contratos = [
                {"id": c.id, "codigo": c.codigo}
                for c in contratos
            ]
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar contratos: {str(e)}", "error")

    async def _cargar_estadisticas(self):
        """Carga estadísticas globales para las cards."""
        try:
            self.estadisticas = await entregable_service.obtener_estadisticas_empresa(
                self.id_empresa_actual
            )
        except Exception:
            self.estadisticas = {
                "total": 0,
                "pendientes": 0,
                "en_revision": 0,
                "aprobados": 0,
                "rechazados": 0,
            }

    async def _cargar_entregables(self):
        """Carga entregables con los filtros actuales."""
        self.cargando = True
        try:
            # Determinar lista de estatus según filtro
            if self.filtro_estatus == "accion_requerida":
                estatus_list = ["PENDIENTE", "RECHAZADO"]
            elif self.filtro_estatus == "all":
                estatus_list = None
            else:
                estatus_list = [self.filtro_estatus]

            contrato_id = None if self.filtro_contrato_id == "all" else int(self.filtro_contrato_id)

            entregables = await entregable_service.obtener_por_empresa(
                empresa_id=self.id_empresa_actual,
                estatus_list=estatus_list,
                contrato_id=contrato_id,
                limite=100,
            )

            self.entregables = [
                {
                    "id": e.id,
                    "contrato_id": e.contrato_id,
                    "contrato_codigo": e.contrato_codigo,
                    "numero_periodo": e.numero_periodo,
                    "periodo_inicio": str(e.periodo_inicio),
                    "periodo_fin": str(e.periodo_fin),
                    "periodo_texto": e.periodo_texto,
                    "estatus": e.estatus.value if hasattr(e.estatus, 'value') else e.estatus,
                    "fecha_entrega": str(e.fecha_entrega) if e.fecha_entrega else None,
                    "monto_aprobado": str(e.monto_aprobado) if e.monto_aprobado else None,
                    "observaciones_rechazo": e.observaciones_rechazo,
                    "puede_editar": e.estatus in ("PENDIENTE", "RECHAZADO") or e.estatus == EstatusEntregable.PENDIENTE or e.estatus == EstatusEntregable.RECHAZADO,
                }
                for e in entregables
            ]
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar entregables: {str(e)}", "error")
        finally:
            self.cargando = False

    # =========================================================================
    # FILTROS (CLICK EN STAT CARDS)
    # =========================================================================
    async def filtrar_por_estatus(self, estatus: str):
        """Filtra por estatus al hacer click en una stat card."""
        self.filtro_estatus = estatus
        await self._cargar_entregables()

    async def filtrar_accion_requerida(self):
        """Filtra pendientes + rechazados (default)."""
        await self.filtrar_por_estatus("accion_requerida")

    async def filtrar_pendientes(self):
        await self.filtrar_por_estatus("PENDIENTE")

    async def filtrar_en_revision(self):
        await self.filtrar_por_estatus("EN_REVISION")

    async def filtrar_aprobados(self):
        await self.filtrar_por_estatus("APROBADO")

    async def filtrar_rechazados(self):
        await self.filtrar_por_estatus("RECHAZADO")

    async def set_filtro_contrato(self, contrato_id: str):
        """Cambia el filtro de contrato y recarga."""
        self.filtro_contrato_id = contrato_id if contrato_id else "all"
        await self._cargar_entregables()

    # =========================================================================
    # MODAL DE ENTREGABLE
    # =========================================================================
    async def abrir_entregable(self, entregable_id: int):
        entregable = next((e for e in self.entregables if e["id"] == entregable_id), None)
        if not entregable:
            return
        self.entregable_actual = entregable
        await self._cargar_archivos_entregable(entregable_id)
        self.mostrar_modal_entregable = True

    def cerrar_modal_entregable(self):
        self.mostrar_modal_entregable = False
        self.entregable_actual = None
        self.archivos_entregable = []

    def set_mostrar_modal(self, open: bool):
        """Handler para on_open_change - no hacer nada para evitar cierre accidental."""
        # Solo se cierra con el botón de cerrar
        pass

    async def _cargar_archivos_entregable(self, entregable_id: int):
        try:
            archivos = await archivo_service.obtener_archivos_entidad(
                EntidadArchivo.ENTREGABLE, entregable_id
            )
            self.archivos_entregable = [
                {
                    "id": a.id,
                    "nombre": a.nombre_original,
                    "tipo_mime": a.tipo_mime,
                    "tamanio_mb": a.tamanio_mb,
                    "es_imagen": a.es_imagen,
                    "fue_comprimido": a.fue_comprimido,
                }
                for a in archivos
            ]
        except Exception:
            self.archivos_entregable = []

    # =========================================================================
    # SUBIDA DE ARCHIVOS
    # =========================================================================
    async def subir_archivos(self, files: List[rx.UploadFile]):
        """Sube los archivos seleccionados."""
        if not self.entregable_actual:
            self.mostrar_mensaje("Seleccione un entregable primero", "warning")
            return
        if not files:
            self.mostrar_mensaje("No hay archivos seleccionados", "warning")
            return
        if not self.entregable_actual.get("puede_editar"):
            self.mostrar_mensaje("No se pueden subir archivos a este entregable", "warning")
            return

        self.subiendo_archivo = True
        archivos_subidos = 0

        try:
            for file in files:
                contenido = await file.read()
                tipo_mime = file.content_type or "application/octet-stream"
                es_imagen = tipo_mime.startswith("image/")
                await archivo_service.subir_archivo(
                    contenido=contenido,
                    nombre_original=file.filename,
                    tipo_mime=tipo_mime,
                    entidad_tipo=EntidadArchivo.ENTREGABLE,
                    entidad_id=self.entregable_actual["id"],
                    identificador_ruta=f"entregable-{self.entregable_actual['id']}",
                    tipo_archivo=TipoArchivo.IMAGEN if es_imagen else TipoArchivo.DOCUMENTO,
                    origen=OrigenArchivo.WEB,
                )
                archivos_subidos += 1

            await self._cargar_archivos_entregable(self.entregable_actual["id"])
            self.mostrar_mensaje(f"{archivos_subidos} archivo(s) subido(s)", "success")
        except Exception as e:
            self.mostrar_mensaje(f"Error al subir: {str(e)}", "error")
        finally:
            self.subiendo_archivo = False

        return rx.clear_selected_files("upload_entregable")

    async def eliminar_archivo(self, archivo_id):
        if not self.entregable_actual or not self.entregable_actual.get("puede_editar"):
            return
        try:
            archivo_id_int = int(archivo_id) if archivo_id else 0
            if not archivo_id_int:
                return
            await archivo_service.eliminar_archivo(archivo_id_int)
            await self._cargar_archivos_entregable(self.entregable_actual["id"])
            self.mostrar_mensaje("Archivo eliminado", "success")
        except Exception as e:
            self.mostrar_mensaje(f"Error al eliminar: {str(e)}", "error")

    # =========================================================================
    # ENVIAR PARA REVISIÓN
    # =========================================================================
    async def enviar_para_revision(self):
        if not self.entregable_actual or not self.puede_entregar:
            return
        self.enviando = True
        try:
            await entregable_service.entregar(
                entregable_id=self.entregable_actual["id"],
                monto_calculado=None,
            )
            self.mostrar_mensaje("Entregable enviado para revisión", "success")
            self.cerrar_modal_entregable()
            # Recargar estadísticas y lista
            await self._cargar_estadisticas()
            await self._cargar_entregables()
        except BusinessRuleError as e:
            self.mostrar_mensaje(str(e), "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error al enviar: {str(e)}", "error")
        finally:
            self.enviando = False
