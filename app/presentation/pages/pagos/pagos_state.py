"""
Estado de Reflex para la pagina de Pagos.
Muestra todos los pagos del sistema con filtros.
"""
import reflex as rx
from typing import List, Optional
from decimal import Decimal
from datetime import date

from app.presentation.components.shared.base_state import BaseState
from app.services import pago_service, contrato_service
from app.core.text_utils import formatear_moneda, formatear_fecha
from app.core.ui_helpers import FILTRO_TODOS
from app.entities import PagoCreate, PagoUpdate


class PagosPageState(BaseState):
    """Estado para la pagina de Pagos."""

    # ========================
    # DATOS
    # ========================
    pagos: List[dict] = []
    total_registros: int = 0

    # Catalogos
    contratos_opciones: List[dict] = []

    # ========================
    # FILTROS
    # ========================
    filtro_contrato_id: str = FILTRO_TODOS
    filtro_fecha_desde: str = ""
    filtro_fecha_hasta: str = ""

    # ========================
    # UI
    # ========================
    mostrar_modal_pago: bool = False
    mostrar_modal_eliminar: bool = False
    es_edicion: bool = False
    pago_seleccionado: Optional[dict] = None

    # ========================
    # FORMULARIO
    # ========================
    form_contrato_id: str = ""
    form_fecha_pago: str = ""
    form_monto: str = ""
    form_concepto: str = ""
    form_numero_factura: str = ""
    form_comprobante: str = ""
    form_notas: str = ""

    # Errores
    error_contrato_id: str = ""
    error_fecha_pago: str = ""
    error_monto: str = ""
    error_concepto: str = ""

    # ========================
    # SETTERS
    # ========================
    def set_filtro_contrato_id(self, value: str):
        self.filtro_contrato_id = value

    def set_filtro_fecha_desde(self, value: str):
        self.filtro_fecha_desde = value

    def set_filtro_fecha_hasta(self, value: str):
        self.filtro_fecha_hasta = value

    def set_form_contrato_id(self, value: str):
        self.form_contrato_id = value
        self.error_contrato_id = ""

    def set_form_fecha_pago(self, value: str):
        self.form_fecha_pago = value
        self.error_fecha_pago = ""

    def set_form_monto(self, value: str):
        self.form_monto = value
        self.error_monto = ""

    def set_form_concepto(self, value: str):
        self.form_concepto = value
        self.error_concepto = ""

    def set_form_numero_factura(self, value: str):
        self.form_numero_factura = value.upper() if value else ""

    def set_form_comprobante(self, value: str):
        self.form_comprobante = value

    def set_form_notas(self, value: str):
        self.form_notas = value

    # ========================
    # CARGA
    # ========================
    async def on_mount(self):
        """Se ejecuta al montar la pagina."""
        async for _ in self._montar_pagina(
            self._fetch_pagos,
            self._cargar_contratos,
        ):
            yield

    async def _fetch_pagos(self):
        """Carga los pagos con filtros."""
        try:
            contrato_id = None
            if self.filtro_contrato_id and self.filtro_contrato_id != FILTRO_TODOS:
                contrato_id = int(self.filtro_contrato_id)

            fecha_desde = self.filtro_fecha_desde or None
            fecha_hasta = self.filtro_fecha_hasta or None

            pagos_data = await pago_service.obtener_todos(
                contrato_id=contrato_id,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                limite=100,
                offset=0,
            )

            # Formatear para la tabla
            self.pagos = []
            for p in pagos_data:
                fecha = p.get("fecha_pago", "")
                if fecha and len(str(fecha)) >= 10:
                    partes = str(fecha)[:10].split("-")
                    if len(partes) == 3:
                        fecha = f"{partes[2]}/{partes[1]}/{partes[0]}"

                monto = p.get("monto", 0)
                self.pagos.append({
                    "id": p.get("id"),
                    "contrato_id": p.get("contrato_id"),
                    "contrato_codigo": p.get("contrato_codigo", ""),
                    "empresa_nombre": p.get("empresa_nombre", ""),
                    "fecha_pago": p.get("fecha_pago", ""),
                    "fecha_pago_fmt": fecha,
                    "monto": monto,
                    "monto_fmt": formatear_moneda(str(monto)),
                    "concepto": p.get("concepto", ""),
                    "numero_factura": p.get("numero_factura", ""),
                })

            self.total_registros = len(self.pagos)
        except Exception as e:
            self.manejar_error(e, "al cargar pagos")
            self.pagos = []

    async def _cargar_contratos(self):
        """Carga el catalogo de contratos para filtros."""
        try:
            contratos = await contrato_service.obtener_todos(limite=500)
            self.contratos_opciones = [
                {"label": "Todos", "value": FILTRO_TODOS}
            ]
            for c in contratos:
                self.contratos_opciones.append({
                    "label": c.codigo,
                    "value": str(c.id),
                })
        except Exception:
            self.contratos_opciones = [{"label": "Todos", "value": FILTRO_TODOS}]

    # ========================
    # FILTROS
    # ========================
    async def aplicar_filtros(self):
        """Aplica los filtros y recarga."""
        self.loading = True
        yield
        await self._fetch_pagos()
        self.loading = False

    def limpiar_filtros(self):
        """Limpia todos los filtros."""
        self.filtro_contrato_id = FILTRO_TODOS
        self.filtro_fecha_desde = ""
        self.filtro_fecha_hasta = ""

    # ========================
    # MODAL CREAR/EDITAR
    # ========================
    def abrir_modal_crear(self):
        """Abre el modal para crear pago."""
        self._limpiar_formulario()
        self.es_edicion = False
        self.mostrar_modal_pago = True

    def abrir_modal_editar(self, pago: dict):
        """Abre el modal para editar pago."""
        self.pago_seleccionado = pago
        self.es_edicion = True
        self.form_contrato_id = str(pago.get("contrato_id", ""))
        self.form_fecha_pago = str(pago.get("fecha_pago", ""))
        self.form_monto = str(pago.get("monto", ""))
        self.form_concepto = pago.get("concepto", "")
        self.form_numero_factura = pago.get("numero_factura", "") or ""
        self.form_comprobante = pago.get("comprobante", "") or ""
        self.form_notas = pago.get("notas", "") or ""
        self._limpiar_errores()
        self.mostrar_modal_pago = True

    def cerrar_modal_pago(self):
        """Cierra el modal de pago."""
        self.mostrar_modal_pago = False
        self._limpiar_formulario()

    def _limpiar_formulario(self):
        """Limpia el formulario."""
        self.form_contrato_id = ""
        self.form_fecha_pago = ""
        self.form_monto = ""
        self.form_concepto = ""
        self.form_numero_factura = ""
        self.form_comprobante = ""
        self.form_notas = ""
        self._limpiar_errores()
        self.pago_seleccionado = None

    def _limpiar_errores(self):
        """Limpia los errores."""
        self.error_contrato_id = ""
        self.error_fecha_pago = ""
        self.error_monto = ""
        self.error_concepto = ""

    def _validar_formulario(self) -> bool:
        """Valida el formulario. Retorna True si hay errores."""
        hay_error = False

        if not self.form_contrato_id:
            self.error_contrato_id = "Seleccione un contrato"
            hay_error = True

        if not self.form_fecha_pago:
            self.error_fecha_pago = "La fecha es obligatoria"
            hay_error = True

        if not self.form_monto:
            self.error_monto = "El monto es obligatorio"
            hay_error = True
        else:
            try:
                monto = Decimal(self.form_monto.replace(",", "").replace("$", "").strip())
                if monto <= 0:
                    self.error_monto = "El monto debe ser mayor a 0"
                    hay_error = True
            except Exception:
                self.error_monto = "Monto invalido"
                hay_error = True

        if not self.form_concepto or len(self.form_concepto.strip()) < 3:
            self.error_concepto = "El concepto debe tener al menos 3 caracteres"
            hay_error = True

        return hay_error

    async def guardar_pago(self):
        """Guarda el pago (crear o editar)."""
        if self._validar_formulario():
            return

        self.saving = True
        try:
            monto = Decimal(self.form_monto.replace(",", "").replace("$", "").strip())

            if self.es_edicion and self.pago_seleccionado:
                update = PagoUpdate(
                    fecha_pago=self.form_fecha_pago,
                    monto=monto,
                    concepto=self.form_concepto.strip(),
                    numero_factura=self.form_numero_factura.strip() or None,
                    comprobante=self.form_comprobante.strip() or None,
                    notas=self.form_notas.strip() or None,
                )
                await pago_service.actualizar(self.pago_seleccionado["id"], update)
                self.cerrar_modal_pago()
                await self._fetch_pagos()
                return rx.toast.success("Pago actualizado", position="top-center")
            else:
                create = PagoCreate(
                    contrato_id=int(self.form_contrato_id),
                    fecha_pago=self.form_fecha_pago,
                    monto=monto,
                    concepto=self.form_concepto.strip(),
                    numero_factura=self.form_numero_factura.strip() or None,
                    comprobante=self.form_comprobante.strip() or None,
                    notas=self.form_notas.strip() or None,
                )
                await pago_service.crear(create)
                self.cerrar_modal_pago()
                await self._fetch_pagos()
                return rx.toast.success("Pago registrado", position="top-center")
        except Exception as e:
            return self.manejar_error_con_toast(e, "al guardar pago")
        finally:
            self.saving = False

    # ========================
    # ELIMINAR
    # ========================
    def abrir_modal_eliminar(self, pago: dict):
        """Abre el modal de confirmacion."""
        self.pago_seleccionado = pago
        self.mostrar_modal_eliminar = True

    def cerrar_modal_eliminar(self):
        """Cierra el modal de confirmacion."""
        self.mostrar_modal_eliminar = False
        self.pago_seleccionado = None

    async def eliminar_pago(self):
        """Elimina el pago seleccionado."""
        if not self.pago_seleccionado:
            return

        self.saving = True
        try:
            await pago_service.eliminar(self.pago_seleccionado["id"])
            self.cerrar_modal_eliminar()
            await self._fetch_pagos()
            return rx.toast.success("Pago eliminado", position="top-center")
        except Exception as e:
            return self.manejar_error_con_toast(e, "al eliminar pago")
        finally:
            self.saving = False

    # ========================
    # COMPUTED
    # ========================
    @rx.var
    def tiene_pagos(self) -> bool:
        return len(self.pagos) > 0
