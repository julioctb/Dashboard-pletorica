"""
Estado principal del módulo Cotizador.

Gestiona el listado de cotizaciones y el formulario de creación.
Hereda de AuthState para acceso a empresa_actual y permisos.
"""
import reflex as rx
from typing import Optional

from app.presentation.components.shared.auth_state import AuthState
from app.presentation.pages.cotizador.cotizador_validators import (
    validar_fecha_inicio,
    validar_fecha_fin,
)


class CotizadorState(AuthState):
    """Estado del listado de cotizaciones."""

    # ─── Lista ────────────────────────────────────────────────────────────────
    cotizaciones: list[dict] = []

    # ─── Filtros ──────────────────────────────────────────────────────────────
    filtro_estatus: str = "__todos__"

    # ─── Modal Crear ──────────────────────────────────────────────────────────
    mostrar_modal_crear: bool = False
    form_fecha_inicio: str = ""
    form_fecha_fin: str = ""
    form_destinatario_nombre: str = ""
    form_destinatario_cargo: str = ""
    form_notas: str = ""
    form_mostrar_desglose: bool = False

    # Errores de validación
    error_fecha_inicio: str = ""
    error_fecha_fin: str = ""

    # ─── Estado de UI ─────────────────────────────────────────────────────────
    loading_cotizaciones: bool = False
    saving_cotizacion: bool = False
    cotizacion_id_cambiando_estatus: int = 0

    # ─── Setters explícitos ───────────────────────────────────────────────────
    def set_filtro_estatus(self, value: str):
        self.filtro_estatus = value

    def set_form_fecha_inicio(self, value: str):
        self.form_fecha_inicio = value
        self.error_fecha_inicio = ""

    def set_form_fecha_fin(self, value: str):
        self.form_fecha_fin = value
        self.error_fecha_fin = ""

    def set_form_destinatario_nombre(self, value: str):
        self.form_destinatario_nombre = value

    def set_form_destinatario_cargo(self, value: str):
        self.form_destinatario_cargo = value

    def set_form_notas(self, value: str):
        self.form_notas = value

    def set_form_mostrar_desglose(self, value: bool):
        self.form_mostrar_desglose = value

    def set_mostrar_modal_crear(self, value: bool):
        self.mostrar_modal_crear = value

    def abrir_modal_crear(self):
        self.mostrar_modal_crear = True
        self.form_fecha_inicio = ""
        self.form_fecha_fin = ""
        self.form_destinatario_nombre = ""
        self.form_destinatario_cargo = ""
        self.form_notas = ""
        self.form_mostrar_desglose = False
        self.error_fecha_inicio = ""
        self.error_fecha_fin = ""

    def cerrar_modal_crear(self):
        self.mostrar_modal_crear = False

    # ─── Validadores de campo ─────────────────────────────────────────────────
    def validar_fecha_inicio_campo(self):
        error = validar_fecha_inicio(self.form_fecha_inicio)
        self.error_fecha_inicio = error or ""

    def validar_fecha_fin_campo(self):
        error = validar_fecha_fin(self.form_fecha_fin, self.form_fecha_inicio)
        self.error_fecha_fin = error or ""

    # ─── Handlers principales ─────────────────────────────────────────────────
    async def cargar_cotizaciones(self):
        """Carga cotizaciones de la empresa actual. Se llama en on_mount."""
        if not self.esta_autenticado:
            return

        empresa_id = self.empresa_actual.get('id') if self.empresa_actual else None
        if not empresa_id:
            return

        self.loading_cotizaciones = True
        yield

        try:
            from app.services import cotizacion_service
            cotizaciones = await cotizacion_service.obtener_por_empresa(empresa_id)
            self.cotizaciones = [c.model_dump(mode='json') for c in cotizaciones]
        except Exception as e:
            self.manejar_error(e, "cargar cotizaciones")
        finally:
            self.loading_cotizaciones = False

    async def crear_cotizacion(self):
        """Crea una nueva cotización con los datos del formulario."""
        # Validar
        err_ini = validar_fecha_inicio(self.form_fecha_inicio)
        err_fin = validar_fecha_fin(self.form_fecha_fin, self.form_fecha_inicio)
        self.error_fecha_inicio = err_ini or ""
        self.error_fecha_fin = err_fin or ""

        if err_ini or err_fin:
            return

        empresa_id = self.empresa_actual.get('id') if self.empresa_actual else None
        if not empresa_id:
            self.mostrar_mensaje("No hay empresa seleccionada", "error")
            return

        self.saving_cotizacion = True
        yield

        try:
            from app.services import cotizacion_service
            from app.entities import CotizacionCreate
            from datetime import date

            datos = CotizacionCreate(
                empresa_id=empresa_id,
                fecha_inicio_periodo=date.fromisoformat(self.form_fecha_inicio),
                fecha_fin_periodo=date.fromisoformat(self.form_fecha_fin),
                destinatario_nombre=self.form_destinatario_nombre or None,
                destinatario_cargo=self.form_destinatario_cargo or None,
                notas=self.form_notas or None,
                mostrar_desglose=self.form_mostrar_desglose,
            )
            cotizacion = await cotizacion_service.crear(
                datos, user_id=self.usuario_actual.get('id')
            )
            self.cerrar_modal_crear()
            self.mostrar_mensaje(f"Cotización {cotizacion.codigo} creada", "success")
            await self.cargar_cotizaciones()
            yield rx.redirect(f"/cotizador/{cotizacion.id}")

        except Exception as e:
            self.manejar_error(e, "crear cotización")
        finally:
            self.saving_cotizacion = False

    async def cambiar_estatus(self, cotizacion_id: int, nuevo_estatus: str):
        """Cambia el estatus de una cotización."""
        self.cotizacion_id_cambiando_estatus = cotizacion_id
        yield

        try:
            from app.services import cotizacion_service
            from app.core.enums import EstatusCotizacion
            estatus_enum = EstatusCotizacion(nuevo_estatus)
            await cotizacion_service.cambiar_estatus(cotizacion_id, estatus_enum)
            self.mostrar_mensaje(f"Estatus actualizado a {nuevo_estatus}", "success")
            await self.cargar_cotizaciones()
        except Exception as e:
            self.manejar_error(e, "cambiar estatus")
        finally:
            self.cotizacion_id_cambiando_estatus = 0

    async def crear_nueva_version(self, cotizacion_id: int):
        """Crea una nueva versión de una cotización."""
        self.loading = True
        yield

        try:
            from app.services import cotizacion_service
            nueva = await cotizacion_service.crear_version(cotizacion_id)
            self.mostrar_mensaje(f"Nueva versión creada: {nueva.codigo}", "success")
            await self.cargar_cotizaciones()
            yield rx.redirect(f"/cotizador/{nueva.id}")
        except Exception as e:
            self.manejar_error(e, "crear nueva versión")
        finally:
            self.loading = False

    async def descargar_pdf(self, cotizacion_id: int):
        """Genera y descarga PDF de una cotización."""
        self.loading = True
        yield

        try:
            from app.services import cotizacion_pdf_service
            pdf_bytes = await cotizacion_pdf_service.generar_pdf(cotizacion_id)
            # En Reflex, el download se maneja a través de un endpoint o descarga directa
            # Por ahora mostrar mensaje de éxito
            self.mostrar_mensaje("PDF generado exitosamente", "success")
        except ImportError:
            self.mostrar_mensaje(
                "Para generar PDF instala reportlab: poetry add reportlab num2words",
                "warning"
            )
        except Exception as e:
            self.manejar_error(e, "generar PDF")
        finally:
            self.loading = False

    # ─── Computed vars ────────────────────────────────────────────────────────
    @rx.var
    def cotizaciones_filtradas(self) -> list[dict]:
        """Filtra cotizaciones por estatus."""
        if self.filtro_estatus == "__todos__":
            return self.cotizaciones
        return [
            c for c in self.cotizaciones
            if c.get('estatus') == self.filtro_estatus
        ]

    @rx.var
    def total_cotizaciones(self) -> int:
        return len(self.cotizaciones)
