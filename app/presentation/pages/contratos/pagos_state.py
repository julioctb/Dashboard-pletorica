"""
Estado de Reflex para el módulo de Pagos de Contratos.
Maneja el estado de la UI para gestión de pagos.
"""
import reflex as rx
from typing import List, Optional
from decimal import Decimal, InvalidOperation
from datetime import date

from app.presentation.components.shared.base_state import BaseState
from app.services import pago_service
from app.core.text_utils import formatear_moneda, formatear_fecha

from app.entities import (
    PagoCreate,
    PagoUpdate,
    EstatusContrato,
)

# Las excepciones se manejan centralizadamente en BaseState
# BusinessRuleError se importa para lanzar errores de negocio
from app.core.exceptions import BusinessRuleError

from .pagos_validators import (
    validar_fecha_pago,
    validar_monto,
    validar_concepto,
    validar_numero_factura,
    validar_comprobante,
    validar_notas,
)


class PagosState(BaseState):
    """Estado para el módulo de Pagos"""

    # ========================
    # ESTADO DE DATOS
    # ========================
    pagos: List[dict] = []
    pago_seleccionado: Optional[dict] = None

    # Contrato actual
    contrato_id: int = 0
    contrato_codigo: str = ""
    contrato_monto_maximo: str = ""
    contrato_estatus: str = ""

    # Resumen de pagos
    total_pagado: str = "$ 0.00"
    saldo_pendiente: str = "$ 0.00"
    porcentaje_pagado: str = "0%"
    cantidad_pagos: int = 0

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_pagos: bool = False
    mostrar_modal_pago_form: bool = False
    mostrar_modal_confirmar_eliminar: bool = False
    es_edicion_pago: bool = False

    # ========================
    # ESTADO DEL FORMULARIO
    # ========================
    form_fecha_pago: str = ""
    form_monto: str = ""
    form_concepto: str = ""
    form_numero_factura: str = ""
    form_comprobante: str = ""
    form_notas: str = ""

    # ========================
    # ERRORES DE VALIDACIÓN
    # ========================
    error_fecha_pago: str = ""
    error_monto: str = ""
    error_concepto: str = ""
    error_numero_factura: str = ""
    error_comprobante: str = ""
    error_notas: str = ""

    # ========================
    # SETTERS
    # ========================
    def set_form_fecha_pago(self, value):
        self.form_fecha_pago = value if value else ""

    def set_form_monto(self, value):
        self.form_monto = formatear_moneda(value) if value else ""

    def set_form_concepto(self, value):
        self.form_concepto = value if value else ""

    def set_form_numero_factura(self, value):
        self.form_numero_factura = value.upper() if value else ""

    def set_form_comprobante(self, value):
        self.form_comprobante = value if value else ""

    def set_form_notas(self, value):
        self.form_notas = value if value else ""

    # ========================
    # VALIDACIÓN EN TIEMPO REAL
    # ========================
    def validar_fecha_pago_campo(self):
        self.error_fecha_pago = validar_fecha_pago(self.form_fecha_pago)

    def validar_monto_campo(self):
        self.error_monto = validar_monto(self.form_monto)

    def validar_concepto_campo(self):
        self.error_concepto = validar_concepto(self.form_concepto)

    def validar_numero_factura_campo(self):
        self.error_numero_factura = validar_numero_factura(self.form_numero_factura)

    def validar_comprobante_campo(self):
        self.error_comprobante = validar_comprobante(self.form_comprobante)

    def validar_notas_campo(self):
        self.error_notas = validar_notas(self.form_notas)

    def _validar_todos_los_campos(self):
        """Valida todos los campos del formulario"""
        self.validar_fecha_pago_campo()
        self.validar_monto_campo()
        self.validar_concepto_campo()
        self.validar_numero_factura_campo()
        self.validar_comprobante_campo()
        self.validar_notas_campo()

    @rx.var
    def tiene_errores_formulario(self) -> bool:
        """Verifica si hay errores de validación"""
        return bool(
            self.error_fecha_pago or
            self.error_monto or
            self.error_concepto or
            self.error_numero_factura or
            self.error_comprobante or
            self.error_notas
        )

    @rx.var
    def puede_guardar_pago(self) -> bool:
        """Verifica si se puede guardar el pago"""
        tiene_requeridos = bool(
            self.form_fecha_pago and
            self.form_monto and
            self.form_concepto.strip()
        )
        return tiene_requeridos and not self.tiene_errores_formulario and not self.saving

    @rx.var
    def puede_cerrar_contrato(self) -> bool:
        """Verifica si el contrato puede cerrarse"""
        # Puede cerrarse si está activo o vencido y tiene pagos
        return (
            self.contrato_estatus in [EstatusContrato.ACTIVO.value, EstatusContrato.VENCIDO.value] and
            self.cantidad_pagos > 0
        )

    @rx.var
    def contrato_esta_cerrado(self) -> bool:
        """Verifica si el contrato está cerrado"""
        return self.contrato_estatus == EstatusContrato.CERRADO.value

    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def abrir_modal_pagos(self, contrato: dict):
        """Abre el modal de pagos para un contrato"""
        self.contrato_id = contrato.get("id", 0)
        self.contrato_codigo = contrato.get("codigo", "")
        self.contrato_estatus = contrato.get("estatus", "")

        monto_max = contrato.get("monto_maximo")
        self.contrato_monto_maximo = formatear_moneda(str(monto_max)) if monto_max else "No definido"

        self.mostrar_modal_pagos = True
        await self.cargar_pagos()

    def cerrar_modal_pagos(self):
        """Cierra el modal de pagos"""
        self.mostrar_modal_pagos = False
        self._limpiar_estado()

    async def cargar_pagos(self):
        """Carga los pagos del contrato actual"""
        if not self.contrato_id:
            return

        self.loading = True
        try:
            # Obtener pagos
            pagos = await pago_service.obtener_por_contrato(self.contrato_id)
            self.pagos = []
            for p in pagos:
                pago_dict = p.model_dump()
                pago_dict["fecha_pago_fmt"] = formatear_fecha(p.fecha_pago)
                pago_dict["monto_fmt"] = formatear_moneda(str(p.monto))
                self.pagos.append(pago_dict)

            # Obtener resumen
            resumen = await pago_service.obtener_resumen_pagos_contrato(self.contrato_id)
            self.total_pagado = formatear_moneda(str(resumen.total_pagado))
            self.saldo_pendiente = formatear_moneda(str(resumen.saldo_pendiente))
            self.porcentaje_pagado = f"{resumen.porcentaje_pagado}%"
            self.cantidad_pagos = resumen.cantidad_pagos

        except Exception as e:
            self.manejar_error(e, "al cargar pagos")
            self.pagos = []
        finally:
            self.finalizar_carga()

    # ========================
    # CRUD DE PAGOS
    # ========================
    def abrir_modal_crear_pago(self):
        """Abre el modal para crear un nuevo pago"""
        self._limpiar_formulario()
        self.es_edicion_pago = False
        self.form_fecha_pago = date.today().isoformat()
        self.mostrar_modal_pago_form = True

    def abrir_modal_editar_pago(self, pago: dict):
        """Abre el modal para editar un pago"""
        self._limpiar_formulario()
        self.es_edicion_pago = True
        self.pago_seleccionado = pago
        self._cargar_pago_en_formulario(pago)
        self.mostrar_modal_pago_form = True

    def cerrar_modal_pago_form(self):
        """Cierra el modal de formulario de pago"""
        self.mostrar_modal_pago_form = False
        self._limpiar_formulario()

    async def guardar_pago(self):
        """Guarda el pago (crear o actualizar)"""
        self._validar_todos_los_campos()

        if self.tiene_errores_formulario:
            return rx.toast.error(
                "Por favor corrige los errores del formulario",
                position="top-center"
            )

        self.saving = True
        try:
            if self.es_edicion_pago:
                mensaje = await self._actualizar_pago()
            else:
                mensaje = await self._crear_pago()

            self.cerrar_modal_pago_form()
            await self.cargar_pagos()

            return rx.toast.success(mensaje, position="top-center")

        except Exception as e:
            return self.manejar_error_con_toast(e, "al guardar pago")
        finally:
            self.finalizar_guardado()

    async def _crear_pago(self) -> str:
        """Crea un nuevo pago"""
        pago_create = PagoCreate(
            contrato_id=self.contrato_id,
            fecha_pago=date.fromisoformat(self.form_fecha_pago),
            monto=self._parse_decimal(self.form_monto),
            concepto=self.form_concepto.strip(),
            numero_factura=self.form_numero_factura.strip() or None,
            comprobante=self.form_comprobante.strip() or None,
            notas=self.form_notas.strip() or None,
        )

        await pago_service.crear(pago_create)
        return "Pago registrado exitosamente"

    async def _actualizar_pago(self) -> str:
        """Actualiza un pago existente"""
        if not self.pago_seleccionado:
            raise BusinessRuleError("No hay pago seleccionado")

        pago_update = PagoUpdate(
            fecha_pago=date.fromisoformat(self.form_fecha_pago),
            monto=self._parse_decimal(self.form_monto),
            concepto=self.form_concepto.strip(),
            numero_factura=self.form_numero_factura.strip() or None,
            comprobante=self.form_comprobante.strip() or None,
            notas=self.form_notas.strip() or None,
        )

        await pago_service.actualizar(self.pago_seleccionado["id"], pago_update)
        return "Pago actualizado exitosamente"

    def abrir_confirmar_eliminar(self, pago: dict):
        """Abre el modal de confirmación para eliminar"""
        self.pago_seleccionado = pago
        self.mostrar_modal_confirmar_eliminar = True

    def cerrar_confirmar_eliminar(self):
        """Cierra el modal de confirmación"""
        self.mostrar_modal_confirmar_eliminar = False
        self.pago_seleccionado = None

    async def eliminar_pago(self):
        """Elimina el pago seleccionado"""
        if not self.pago_seleccionado:
            return

        self.saving = True
        try:
            await pago_service.eliminar(self.pago_seleccionado["id"])
            self.cerrar_confirmar_eliminar()
            await self.cargar_pagos()

            return rx.toast.success("Pago eliminado", position="top-center")

        except Exception as e:
            return self.manejar_error_con_toast(e, "al eliminar pago")
        finally:
            self.finalizar_guardado()

    # ========================
    # CERRAR CONTRATO
    # ========================
    async def cerrar_contrato_pagado(self):
        """Cierra el contrato actual"""
        if not self.contrato_id:
            return

        self.saving = True
        try:
            # forzar=True permite cerrar aunque no esté 100% pagado
            await pago_service.cerrar_contrato(self.contrato_id, forzar=True)
            self.contrato_estatus = EstatusContrato.CERRADO.value

            return rx.toast.success(
                f"Contrato {self.contrato_codigo} cerrado exitosamente",
                position="top-center"
            )

        except Exception as e:
            return self.manejar_error_con_toast(e, "al cerrar contrato")
        finally:
            self.finalizar_guardado()

    # ========================
    # HELPERS
    # ========================
    def _limpiar_estado(self):
        """Limpia todo el estado"""
        self.pagos = []
        self.pago_seleccionado = None
        self.contrato_id = 0
        self.contrato_codigo = ""
        self.contrato_monto_maximo = ""
        self.contrato_estatus = ""
        self.total_pagado = "$ 0.00"
        self.saldo_pendiente = "$ 0.00"
        self.porcentaje_pagado = "0%"
        self.cantidad_pagos = 0
        self._limpiar_formulario()

    def _limpiar_formulario(self):
        """Limpia el formulario de pago"""
        self.form_fecha_pago = ""
        self.form_monto = ""
        self.form_concepto = ""
        self.form_numero_factura = ""
        self.form_comprobante = ""
        self.form_notas = ""
        self._limpiar_errores()
        self.pago_seleccionado = None
        self.es_edicion_pago = False

    def _limpiar_errores(self):
        """Limpia los errores de validación"""
        self.error_fecha_pago = ""
        self.error_monto = ""
        self.error_concepto = ""
        self.error_numero_factura = ""
        self.error_comprobante = ""
        self.error_notas = ""

    def _cargar_pago_en_formulario(self, pago: dict):
        """Carga datos de un pago en el formulario"""
        fecha = pago.get("fecha_pago")
        self.form_fecha_pago = str(fecha) if fecha else ""

        monto = pago.get("monto")
        self.form_monto = formatear_moneda(str(monto)) if monto else ""

        self.form_concepto = pago.get("concepto", "") or ""
        self.form_numero_factura = pago.get("numero_factura", "") or ""
        self.form_comprobante = pago.get("comprobante", "") or ""
        self.form_notas = pago.get("notas", "") or ""

    def _parse_decimal(self, value: str) -> Decimal:
        """Parsea string a Decimal"""
        if not value:
            return Decimal("0")
        try:
            limpio = value.replace(",", "").replace("$", "").replace(" ", "").strip()
            return Decimal(limpio)
        except InvalidOperation:
            return Decimal("0")
