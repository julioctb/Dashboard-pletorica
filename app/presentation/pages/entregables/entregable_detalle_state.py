"""
Estado para la página de detalle de Entregable.
Gestiona visualización de archivos, detalle de personal, flujo de aprobación/rechazo.
"""

import reflex as rx
from typing import List, Optional
from decimal import Decimal
from uuid import UUID

from app.presentation.components.shared.base_state import BaseState
from app.services import entregable_service, archivo_service
from app.entities.archivo import EntidadArchivo
from app.core.enums import EstatusEntregable
from app.core.exceptions import NotFoundError, BusinessRuleError


class EntregableDetalleState(BaseState):
    """Estado para la página de detalle y revisión de entregable."""

    # =========================================================================
    # DATOS DEL ENTREGABLE
    # =========================================================================
    # Note: entregable_id is automatically provided by Reflex from route /entregables/[entregable_id]
    current_id: int = 0  # Internal ID for tracking
    entregable: dict = {}
    contrato_info: dict = {}
    archivos: List[dict] = []
    detalle_personal: List[dict] = []

    # =========================================================================
    # UI
    # =========================================================================
    cargando: bool = False
    procesando: bool = False
    mostrar_modal_aprobar: bool = False
    monto_a_aprobar: str = ""
    error_monto: str = ""
    mostrar_modal_rechazar: bool = False
    observaciones_rechazo: str = ""
    error_observaciones: str = ""
    imagen_seleccionada: str = ""
    mostrar_galeria: bool = False

    # =========================================================================
    # SETTERS
    # =========================================================================
    def set_monto_a_aprobar(self, value: str):
        self.monto_a_aprobar = value
        self.error_monto = ""

    def set_observaciones_rechazo(self, value: str):
        self.observaciones_rechazo = value
        self.error_observaciones = ""

    # =========================================================================
    # COMPUTED VARS
    # =========================================================================
    @rx.var
    def tiene_entregable(self) -> bool:
        return bool(self.entregable)

    @rx.var
    def puede_revisar(self) -> bool:
        return self.entregable.get("estatus") == "EN_REVISION"

    @rx.var
    def estatus_actual(self) -> str:
        return self.entregable.get("estatus", "PENDIENTE")

    @rx.var
    def periodo_texto(self) -> str:
        return self.entregable.get("periodo_texto", "")

    @rx.var
    def numero_periodo(self) -> int:
        return self.entregable.get("numero_periodo", 0)

    @rx.var
    def tiene_archivos(self) -> bool:
        return len(self.archivos) > 0

    @rx.var
    def tiene_detalle_personal(self) -> bool:
        return len(self.detalle_personal) > 0

    @rx.var
    def archivos_imagenes(self) -> List[dict]:
        return [a for a in self.archivos if a.get("es_imagen", False)]

    @rx.var
    def archivos_documentos(self) -> List[dict]:
        return [a for a in self.archivos if not a.get("es_imagen", False)]

    @rx.var
    def monto_calculado_total(self) -> str:
        total = sum(Decimal(str(d.get("subtotal", "0"))) for d in self.detalle_personal)
        return str(total)

    @rx.var
    def puede_guardar_aprobacion(self) -> bool:
        return bool(self.monto_a_aprobar) and not self.error_monto

    @rx.var
    def puede_guardar_rechazo(self) -> bool:
        return len(self.observaciones_rechazo.strip()) >= 10

    # =========================================================================
    # CARGA DE DATOS
    # =========================================================================
    async def on_mount_detalle(self):
        """Carga el entregable desde el parámetro de ruta."""
        try:
            id_int = int(self.entregable_id) if self.entregable_id else 0
            if id_int > 0:
                await self.cargar_entregable(id_int)
        except (ValueError, TypeError):
            self.mostrar_mensaje("ID de entregable inválido", "error")

    async def cargar_entregable(self, entregable_id: int):
        self.current_id = entregable_id
        self.cargando = True
        try:
            entregable = await entregable_service.obtener_por_id(entregable_id)
            self.entregable = {
                "id": entregable.id,
                "contrato_id": entregable.contrato_id,
                "numero_periodo": entregable.numero_periodo,
                "periodo_inicio": str(entregable.periodo_inicio),
                "periodo_fin": str(entregable.periodo_fin),
                "periodo_texto": entregable.periodo_texto,
                "estatus": entregable.estatus.value if hasattr(entregable.estatus, 'value') else entregable.estatus,
                "fecha_entrega": str(entregable.fecha_entrega) if entregable.fecha_entrega else None,
                "fecha_revision": str(entregable.fecha_revision) if entregable.fecha_revision else None,
                "monto_calculado": str(entregable.monto_calculado) if entregable.monto_calculado else "0",
                "monto_aprobado": str(entregable.monto_aprobado) if entregable.monto_aprobado else None,
                "observaciones_rechazo": entregable.observaciones_rechazo,
                "puede_revisar": entregable.puede_revisar_admin,
                "tiene_pago": entregable.tiene_pago,
            }
            if entregable.monto_calculado:
                self.monto_a_aprobar = str(entregable.monto_calculado)
            await self._cargar_info_contrato(entregable.contrato_id)
            await self._cargar_archivos()
            await self._cargar_detalle_personal()
        except NotFoundError:
            self.mostrar_mensaje("Entregable no encontrado", "error")
            return rx.redirect("/entregables")
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar: {str(e)}", "error")
        finally:
            self.cargando = False

    async def _cargar_info_contrato(self, contrato_id: int):
        from app.services import contrato_service
        try:
            contrato = await contrato_service.obtener_por_id(contrato_id)
            self.contrato_info = {
                "id": contrato.id,
                "codigo": contrato.codigo,
                "empresa_nombre": getattr(contrato, 'empresa_nombre', ''),
            }
        except Exception:
            self.contrato_info = {"codigo": "---", "empresa_nombre": ""}

    async def _cargar_archivos(self):
        try:
            archivos = await archivo_service.obtener_archivos_entidad(EntidadArchivo.ENTREGABLE, self.current_id)
            self.archivos = [
                {
                    "id": a.id,
                    "nombre": a.nombre_original,
                    "tipo_mime": a.tipo_mime,
                    "tamanio_mb": a.tamanio_mb,
                    "es_imagen": a.es_imagen,
                    "es_pdf": a.es_pdf,
                    "url": "",
                    "fue_comprimido": a.fue_comprimido,
                }
                for a in archivos
            ]
        except Exception:
            self.archivos = []

    async def _cargar_detalle_personal(self):
        try:
            detalles = await entregable_service.obtener_detalle_personal(self.current_id)
            self.detalle_personal = [
                {
                    "id": d.id,
                    "categoria_clave": d.categoria_clave,
                    "categoria_nombre": d.categoria_nombre,
                    "cantidad_reportada": d.cantidad_reportada,
                    "cantidad_validada": d.cantidad_validada,
                    "cantidad_minima": d.cantidad_minima,
                    "cantidad_maxima": d.cantidad_maxima,
                    "tarifa_unitaria": str(d.tarifa_unitaria),
                    "subtotal": str(d.subtotal),
                    "cumple_minimo": d.cumple_minimo,
                    "excede_maximo": d.excede_maximo,
                }
                for d in detalles
            ]
        except Exception:
            self.detalle_personal = []

    # =========================================================================
    # VISUALIZACIÓN DE ARCHIVOS
    # =========================================================================
    async def ver_imagen(self, archivo_id: int):
        """Obtiene la URL temporal del archivo y abre la galería."""
        try:
            url = await archivo_service.obtener_url_temporal(archivo_id)
            if url:
                self.imagen_seleccionada = url
                self.mostrar_galeria = True
            else:
                self.mostrar_mensaje("No se pudo cargar la imagen", "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar imagen: {str(e)}", "error")

    async def descargar_documento(self, archivo_id: int):
        """Obtiene la URL temporal del documento para descarga."""
        try:
            url = await archivo_service.obtener_url_temporal(archivo_id)
            if url:
                return rx.redirect(url, external=True)
            else:
                self.mostrar_mensaje("No se pudo obtener el documento", "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error al descargar: {str(e)}", "error")

    def cerrar_galeria(self):
        self.mostrar_galeria = False
        self.imagen_seleccionada = ""

    # =========================================================================
    # FLUJO DE APROBACIÓN
    # =========================================================================
    def abrir_modal_aprobar(self):
        if not self.puede_revisar:
            self.mostrar_mensaje("Este entregable no está en revisión", "warning")
            return
        self.monto_a_aprobar = self.entregable.get("monto_calculado", "0")
        self.error_monto = ""
        self.mostrar_modal_aprobar = True

    def cerrar_modal_aprobar(self):
        self.mostrar_modal_aprobar = False
        self.monto_a_aprobar = ""
        self.error_monto = ""

    def validar_monto(self):
        if not self.monto_a_aprobar:
            self.error_monto = "El monto es requerido"
            return
        try:
            monto = Decimal(self.monto_a_aprobar.replace(",", "").replace("$", ""))
            if monto <= 0:
                self.error_monto = "El monto debe ser mayor a cero"
            else:
                self.error_monto = ""
        except Exception:
            self.error_monto = "Ingrese un monto válido"

    async def confirmar_aprobacion(self):
        self.validar_monto()
        if self.error_monto:
            return
        self.procesando = True
        try:
            monto = Decimal(self.monto_a_aprobar.replace(",", "").replace("$", ""))
            usuario_id = await self._obtener_usuario_actual()
            await entregable_service.aprobar(
                entregable_id=self.current_id,
                monto_aprobado=monto,
                revisado_por=usuario_id,
            )
            self.mostrar_mensaje("Entregable aprobado correctamente", "success")
            self.cerrar_modal_aprobar()
            await self.cargar_entregable(self.current_id)
        except BusinessRuleError as e:
            self.mostrar_mensaje(str(e), "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error al aprobar: {str(e)}", "error")
        finally:
            self.procesando = False

    # =========================================================================
    # FLUJO DE RECHAZO
    # =========================================================================
    def abrir_modal_rechazar(self):
        if not self.puede_revisar:
            self.mostrar_mensaje("Este entregable no está en revisión", "warning")
            return
        self.observaciones_rechazo = ""
        self.error_observaciones = ""
        self.mostrar_modal_rechazar = True

    def cerrar_modal_rechazar(self):
        self.mostrar_modal_rechazar = False
        self.observaciones_rechazo = ""
        self.error_observaciones = ""

    def validar_observaciones(self):
        if not self.observaciones_rechazo or len(self.observaciones_rechazo.strip()) < 10:
            self.error_observaciones = "Las observaciones deben tener al menos 10 caracteres"
        else:
            self.error_observaciones = ""

    async def confirmar_rechazo(self):
        self.validar_observaciones()
        if self.error_observaciones:
            return
        self.procesando = True
        try:
            usuario_id = await self._obtener_usuario_actual()
            await entregable_service.rechazar(
                entregable_id=self.current_id,
                observaciones=self.observaciones_rechazo.strip(),
                revisado_por=usuario_id,
            )
            self.mostrar_mensaje("Entregable rechazado", "warning")
            self.cerrar_modal_rechazar()
            await self.cargar_entregable(self.current_id)
        except BusinessRuleError as e:
            self.mostrar_mensaje(str(e), "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error al rechazar: {str(e)}", "error")
        finally:
            self.procesando = False

    # =========================================================================
    # HELPERS
    # =========================================================================
    async def _obtener_usuario_actual(self) -> UUID:
        import uuid
        return uuid.uuid4()

    def volver_a_listado(self):
        """Vuelve al listado de entregables."""
        return rx.redirect("/entregables")
