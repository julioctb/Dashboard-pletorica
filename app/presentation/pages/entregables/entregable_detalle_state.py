"""
Estado para la página de detalle de Entregable.
Gestiona visualización de archivos, detalle de personal, flujo de aprobación/rechazo.
"""

import reflex as rx
from typing import List
from decimal import Decimal
from uuid import UUID

from app.presentation.components.shared.auth_state import AuthState
from app.services import entregable_service, archivo_service
from app.entities.archivo import EntidadArchivo
from app.core.exceptions import NotFoundError, BusinessRuleError
from app.core.text_utils import formatear_moneda


class EntregableDetalleState(AuthState):
    """Estado para la página de detalle y revisión de entregable."""

    # =========================================================================
    # DATOS DEL ENTREGABLE
    # =========================================================================
    # Note: entregable_id is automatically provided by Reflex from route /entregables/[entregable_id]
    current_id: int = 0  # Internal ID for tracking
    entregable: dict = {}
    contrato_info: dict = {}
    archivos: List[dict] = []
    archivos_pago: List[dict] = []
    detalle_personal: List[dict] = []

    # =========================================================================
    # UI
    # =========================================================================
    procesando: bool = False
    mostrar_modal_aprobar: bool = False
    monto_a_aprobar: str = ""
    error_monto: str = ""
    mostrar_modal_rechazar: bool = False
    observaciones_rechazo: str = ""
    error_observaciones: str = ""
    imagen_seleccionada: str = ""
    mostrar_galeria: bool = False

    # --- Prefactura ---
    mostrar_modal_rechazar_prefactura: bool = False
    observaciones_prefactura: str = ""
    error_observaciones_prefactura: str = ""

    # --- Registrar Pago ---
    mostrar_modal_registrar_pago: bool = False
    fecha_pago: str = ""
    referencia_pago: str = ""
    error_fecha_pago: str = ""

    # =========================================================================
    # SETTERS
    # =========================================================================
    @staticmethod
    def _validar_observaciones_minimas(valor: str) -> str:
        texto = (valor or "").strip()
        if len(texto) < 10:
            return "Las observaciones deben tener al menos 10 caracteres"
        return ""

    @staticmethod
    def _validar_fecha_pago_requerida(valor: str) -> str:
        return "" if valor else "La fecha de pago es requerida"

    def set_monto_a_aprobar(self, value: str):
        self.monto_a_aprobar = formatear_moneda(value) if value else ""
        self.limpiar_errores_campos(["monto"])

    def set_observaciones_rechazo(self, value: str):
        self.observaciones_rechazo = value
        self.limpiar_errores_campos(["observaciones"])

    def set_observaciones_prefactura(self, value: str):
        self.observaciones_prefactura = value
        self.limpiar_errores_campos(["observaciones_prefactura"])

    def set_fecha_pago(self, value: str):
        self.fecha_pago = value
        self.limpiar_errores_campos(["fecha_pago"])

    def set_referencia_pago(self, value: str):
        self.referencia_pago = value

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

    @rx.var
    def puede_revisar_prefactura(self) -> bool:
        return self.entregable.get("estatus") == "PREFACTURA_ENVIADA"

    @rx.var
    def es_facturado(self) -> bool:
        return self.entregable.get("estatus") == "FACTURADO"

    @rx.var
    def es_prefactura_aprobada(self) -> bool:
        return self.entregable.get("estatus") == "PREFACTURA_APROBADA"

    @rx.var
    def es_pagado(self) -> bool:
        return self.entregable.get("estatus") == "PAGADO"

    @rx.var
    def tiene_archivos_pago(self) -> bool:
        return len(self.archivos_pago) > 0

    @rx.var
    def puede_guardar_rechazo_prefactura(self) -> bool:
        return len(self.observaciones_prefactura.strip()) >= 10

    @rx.var
    def puede_guardar_pago(self) -> bool:
        return bool(self.fecha_pago) and not self.error_fecha_pago

    @rx.var
    def folio_fiscal_entregable(self) -> str:
        return self.entregable.get("folio_fiscal", "") or ""

    @rx.var
    def observaciones_prefactura_texto(self) -> str:
        return self.entregable.get("observaciones_prefactura", "") or ""

    @rx.var
    def monto_aprobado_texto(self) -> str:
        return self.entregable.get("monto_aprobado", "") or "0"

    @rx.var
    def referencia_pago_entregable(self) -> str:
        return self.entregable.get("referencia_pago", "") or ""

    @rx.var
    def es_post_aprobacion(self) -> bool:
        """Si el entregable está en algún estado post-aprobación."""
        return self.entregable.get("estatus", "") in [
            "APROBADO", "PREFACTURA_ENVIADA", "PREFACTURA_RECHAZADA",
            "PREFACTURA_APROBADA", "FACTURADO", "PAGADO",
        ]

    # =========================================================================
    # CARGA DE DATOS
    # =========================================================================
    async def on_mount_detalle(self):
        """Carga el entregable desde el parámetro de ruta."""
        try:
            id_int = int(self.entregable_id) if self.entregable_id else 0
            if id_int > 0:
                self.current_id = id_int
                async for _ in self._montar_pagina(self._fetch_entregable):
                    yield
        except (ValueError, TypeError):
            self.mostrar_mensaje("ID de entregable inválido", "error")

    async def _fetch_entregable(self):
        """Carga datos del entregable sin manejo de loading."""
        try:
            entregable = await entregable_service.obtener_por_id(self.current_id)
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
                "pago_id": entregable.pago_id,
                # Campos de facturación
                "observaciones_prefactura": getattr(entregable, 'observaciones_prefactura', None),
                "fecha_prefactura": str(entregable.fecha_prefactura) if getattr(entregable, 'fecha_prefactura', None) else None,
                "fecha_factura": str(entregable.fecha_factura) if getattr(entregable, 'fecha_factura', None) else None,
                "fecha_pago_registrado": str(entregable.fecha_pago_registrado) if getattr(entregable, 'fecha_pago_registrado', None) else None,
                "folio_fiscal": getattr(entregable, 'folio_fiscal', None),
                "referencia_pago": getattr(entregable, 'referencia_pago', None),
            }
            if entregable.monto_calculado:
                self.monto_a_aprobar = str(entregable.monto_calculado)
            await self._cargar_info_contrato(entregable.contrato_id)
            await self._cargar_archivos()
            await self._cargar_archivos_pago()
            await self._cargar_detalle_personal()
        except NotFoundError:
            self.entregable = {}
            self.mostrar_mensaje("Entregable no encontrado", "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error al cargar: {str(e)}", "error")

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

    async def _cargar_archivos_pago(self):
        """Carga archivos de la entidad PAGO asociados al entregable (prefacturas, facturas)."""
        try:
            pago_id = self.entregable.get("pago_id")
            if pago_id:
                archivos = await archivo_service.obtener_archivos_entidad(EntidadArchivo.PAGO, int(pago_id))
                self.archivos_pago = [
                    {
                        "id": a.id,
                        "nombre": a.nombre_original,
                        "tipo_mime": a.tipo_mime,
                        "tamanio_mb": a.tamanio_mb,
                        "es_imagen": a.es_imagen,
                        "es_pdf": a.es_pdf,
                        "categoria": getattr(a, 'categoria', '') or '',
                    }
                    for a in archivos
                ]
            else:
                self.archivos_pago = []
        except Exception:
            self.archivos_pago = []

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
                return rx.redirect(url, is_external=True)
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
        if self.entregable.get("estatus") != "EN_REVISION":
            self.mostrar_mensaje("Este entregable no está en revisión", "warning")
            return
        raw = self.entregable.get("monto_calculado", "0")
        self.monto_a_aprobar = formatear_moneda(raw) if raw else ""
        self.limpiar_errores_campos(["monto"])
        self.mostrar_modal_aprobar = True

    def cerrar_modal_aprobar(self):
        self.mostrar_modal_aprobar = False
        self.monto_a_aprobar = ""
        self.limpiar_errores_campos(["monto"])

    def _limpiar_monto(self, valor: str) -> str:
        """Remueve formato de moneda para obtener valor numérico limpio."""
        return valor.replace(",", "").replace("$", "").strip()

    def validar_monto(self):
        def _validar(valor: str) -> str:
            if not valor:
                return "El monto es requerido"
            try:
                monto = Decimal(self._limpiar_monto(valor))
                if monto <= 0:
                    return "El monto debe ser mayor a cero"
            except Exception:
                return "Ingrese un monto válido"
            return ""

        self.validar_y_asignar_error(
            valor=self.monto_a_aprobar,
            validador=_validar,
            error_attr="error_monto",
        )

    async def confirmar_aprobacion(self):
        self.validar_monto()
        if self.error_monto:
            return
        self.procesando = True
        try:
            monto = Decimal(self._limpiar_monto(self.monto_a_aprobar))
            usuario_id = self._obtener_usuario_actual()
            await entregable_service.aprobar(
                entregable_id=self.current_id,
                monto_aprobado=monto,
                revisado_por=usuario_id,
            )
            self.cerrar_modal_aprobar()
            await self._fetch_entregable()
            return rx.toast.success("Entregable aprobado correctamente", position="top-center")
        except BusinessRuleError as e:
            return rx.toast.error(str(e), position="top-center")
        except Exception as e:
            return rx.toast.error(f"Error al aprobar: {str(e)}", position="top-center")
        finally:
            self.procesando = False

    # =========================================================================
    # FLUJO DE RECHAZO
    # =========================================================================
    def abrir_modal_rechazar(self):
        if self.entregable.get("estatus") != "EN_REVISION":
            self.mostrar_mensaje("Este entregable no está en revisión", "warning")
            return
        self.observaciones_rechazo = ""
        self.limpiar_errores_campos(["observaciones"])
        self.mostrar_modal_rechazar = True

    def cerrar_modal_rechazar(self):
        self.mostrar_modal_rechazar = False
        self.observaciones_rechazo = ""
        self.limpiar_errores_campos(["observaciones"])

    def validar_observaciones(self):
        self.validar_y_asignar_error(
            valor=self.observaciones_rechazo,
            validador=self._validar_observaciones_minimas,
            error_attr="error_observaciones",
        )

    async def confirmar_rechazo(self):
        self.validar_observaciones()
        if self.error_observaciones:
            return
        self.procesando = True
        try:
            usuario_id = self._obtener_usuario_actual()
            await entregable_service.rechazar(
                entregable_id=self.current_id,
                observaciones=self.observaciones_rechazo.strip(),
                revisado_por=usuario_id,
            )
            self.cerrar_modal_rechazar()
            await self._fetch_entregable()
            return rx.toast.success("Entregable rechazado", position="top-center")
        except BusinessRuleError as e:
            return rx.toast.error(str(e), position="top-center")
        except Exception as e:
            return rx.toast.error(f"Error al rechazar: {str(e)}", position="top-center")
        finally:
            self.procesando = False

    # =========================================================================
    # FLUJO DE PREFACTURA (ADMIN)
    # =========================================================================
    async def aprobar_prefactura(self):
        """Aprueba la prefactura del entregable."""
        self.procesando = True
        try:
            usuario_id = self._obtener_usuario_actual()
            await entregable_service.aprobar_prefactura(
                entregable_id=self.current_id,
                revisado_por=usuario_id,
            )
            await self._fetch_entregable()
            return rx.toast.success("Prefactura aprobada correctamente", position="top-center")
        except BusinessRuleError as e:
            return rx.toast.error(str(e), position="top-center")
        except Exception as e:
            return rx.toast.error(f"Error al aprobar prefactura: {str(e)}", position="top-center")
        finally:
            self.procesando = False

    def abrir_modal_rechazar_prefactura(self):
        if self.entregable.get("estatus") != "PREFACTURA_ENVIADA":
            self.mostrar_mensaje("Este entregable no tiene prefactura en revisión", "warning")
            return
        self.observaciones_prefactura = ""
        self.limpiar_errores_campos(["observaciones_prefactura"])
        self.mostrar_modal_rechazar_prefactura = True

    def cerrar_modal_rechazar_prefactura(self):
        self.mostrar_modal_rechazar_prefactura = False
        self.observaciones_prefactura = ""
        self.limpiar_errores_campos(["observaciones_prefactura"])

    def validar_observaciones_prefactura(self):
        self.validar_y_asignar_error(
            valor=self.observaciones_prefactura,
            validador=self._validar_observaciones_minimas,
            error_attr="error_observaciones_prefactura",
        )

    async def confirmar_rechazo_prefactura(self):
        self.validar_observaciones_prefactura()
        if self.error_observaciones_prefactura:
            return
        self.procesando = True
        try:
            usuario_id = self._obtener_usuario_actual()
            await entregable_service.rechazar_prefactura(
                entregable_id=self.current_id,
                observaciones=self.observaciones_prefactura.strip(),
                revisado_por=usuario_id,
            )
            self.cerrar_modal_rechazar_prefactura()
            await self._fetch_entregable()
            return rx.toast.success("Prefactura rechazada", position="top-center")
        except BusinessRuleError as e:
            return rx.toast.error(str(e), position="top-center")
        except Exception as e:
            return rx.toast.error(f"Error al rechazar prefactura: {str(e)}", position="top-center")
        finally:
            self.procesando = False

    # =========================================================================
    # REGISTRAR PAGO (ADMIN)
    # =========================================================================
    def abrir_modal_registrar_pago(self):
        if self.entregable.get("estatus") != "FACTURADO":
            self.mostrar_mensaje("Este entregable no está facturado", "warning")
            return
        self.fecha_pago = ""
        self.referencia_pago = ""
        self.limpiar_errores_campos(["fecha_pago"])
        self.mostrar_modal_registrar_pago = True

    def cerrar_modal_registrar_pago(self):
        self.mostrar_modal_registrar_pago = False
        self.fecha_pago = ""
        self.referencia_pago = ""
        self.limpiar_errores_campos(["fecha_pago"])

    def validar_fecha_pago(self):
        self.validar_y_asignar_error(
            valor=self.fecha_pago,
            validador=self._validar_fecha_pago_requerida,
            error_attr="error_fecha_pago",
        )

    async def confirmar_registrar_pago(self):
        self.validar_fecha_pago()
        if self.error_fecha_pago:
            return
        self.procesando = True
        try:
            from datetime import date as date_type
            fecha = date_type.fromisoformat(self.fecha_pago)
            usuario_id = self._obtener_usuario_actual()
            await entregable_service.registrar_pago(
                entregable_id=self.current_id,
                fecha_pago=fecha,
                referencia=self.referencia_pago.strip() if self.referencia_pago else "",
                revisado_por=usuario_id,
            )
            self.cerrar_modal_registrar_pago()
            await self._fetch_entregable()
            return rx.toast.success("Pago registrado correctamente", position="top-center")
        except BusinessRuleError as e:
            return rx.toast.error(str(e), position="top-center")
        except ValueError:
            self.error_fecha_pago = "Fecha inválida"
        except Exception as e:
            return rx.toast.error(f"Error al registrar pago: {str(e)}", position="top-center")
        finally:
            self.procesando = False

    # =========================================================================
    # DESCARGA ARCHIVOS PAGO
    # =========================================================================
    async def descargar_archivo_pago(self, archivo_id: int):
        """Descarga un archivo de pago (prefactura/factura)."""
        try:
            url = await archivo_service.obtener_url_temporal(archivo_id)
            if url:
                return rx.redirect(url, is_external=True)
            else:
                self.mostrar_mensaje("No se pudo obtener el archivo", "error")
        except Exception as e:
            self.mostrar_mensaje(f"Error al descargar: {str(e)}", "error")

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _obtener_usuario_actual(self) -> UUID:
        if not self.id_usuario:
            raise BusinessRuleError("No se pudo identificar al usuario actual. Inicie sesión nuevamente.")
        return UUID(self.id_usuario)

    def volver_a_listado(self):
        """Vuelve al listado de entregables."""
        return rx.redirect("/entregables")
