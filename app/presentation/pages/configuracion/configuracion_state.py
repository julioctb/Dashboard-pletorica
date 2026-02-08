"""
Estado de la pagina de Configuracion de Requisiciones.

Gestiona la carga y actualizacion de los valores predeterminados
que se pre-llenan al crear nuevas requisiciones (area requirente,
firmas, entrega) y la gestion de lugares de entrega.
"""

import re
import reflex as rx
from typing import List

from app.core.text_utils import normalizar_por_sufijo, capitalizar_con_preposiciones
from app.core.validation.constants import (
    EMAIL_PATTERN,
    TELEFONO_DIGITOS,
    LUGAR_ENTREGA_MAX,
)
from app.core.validation.custom_validators import limpiar_telefono
from app.presentation.components.shared.base_state import BaseState
from app.services import requisicion_service


# =============================================================================
# HELPERS: METADATA POR CLAVE
# =============================================================================

_PLACEHOLDERS: dict = {
    "dependencia_nombre": "Ej: Vicerrectoria de Administracion",
    "dependencia_domicilio": "Ej: 4 Sur 104, Centro, Puebla",
    "dependencia_telefono": "Ej: 2221234567",
    "dependencia_email": "Ej: contacto@buap.mx",
    "titular_nombre": "Ej: Juan Perez Lopez",
    "titular_cargo": "Ej: Director de Recursos Humanos",
    "elabora_nombre": "Ej: Maria Garcia Hernandez",
    "elabora_cargo": "Ej: Jefe de Adquisiciones",
    "solicita_nombre": "Ej: Carlos Martinez Ruiz",
    "solicita_cargo": "Ej: Coordinador Operativo",
    "validacion_asesor": "Ej: Ana Lopez Mendez",
}

_HINTS_POR_SUFIJO: dict = {
    "_nombre": "Se formatea automaticamente",
    "_cargo": "Se formatea automaticamente",
    "_email": "Formato: correo@dominio.com",
    "_telefono": "10 digitos, se formatea automaticamente",
    "_domicilio": "Direccion completa",
}


def _placeholder_para(clave: str) -> str:
    """Retorna placeholder de ejemplo para una clave de configuracion."""
    return _PLACEHOLDERS.get(clave, "")


def _hint_para(clave: str) -> str:
    """Retorna hint de ayuda para una clave de configuracion."""
    for sufijo, hint in _HINTS_POR_SUFIJO.items():
        if clave.endswith(sufijo):
            return hint
    return ""


def _validar_campo_config(clave: str, valor: str) -> str:
    """Valida un campo de configuracion por su sufijo de clave."""
    if not valor or not valor.strip():
        return ""
    if clave.endswith("_email"):
        if not re.match(EMAIL_PATTERN, valor.strip()):
            return "Formato de correo invalido"
    elif clave.endswith("_telefono"):
        digitos = limpiar_telefono(valor)
        if digitos and len(digitos) != TELEFONO_DIGITOS:
            return f"Debe tener {TELEFONO_DIGITOS} digitos"
    return ""


# =============================================================================
# STATE
# =============================================================================

class ConfiguracionState(BaseState):
    """Estado para la pagina de configuracion de requisiciones."""

    # ========================
    # DATOS
    # ========================
    configuraciones: List[dict] = []
    valores_editados: dict = {}
    lugares_entrega: List[dict] = []
    nuevo_lugar: str = ""
    error_nuevo_lugar: str = ""

    # ========================
    # LIFECYCLE
    # ========================
    async def on_mount(self):
        """Se ejecuta al montar la pagina."""
        async for _ in self.montar_pagina(
            self._fetch_configuraciones,
            self._fetch_lugares_entrega,
        ):
            yield

    async def _fetch_configuraciones(self):
        """Carga configuraciones desde la BD (sin manejo de loading)."""
        try:
            configs = await requisicion_service.obtener_configuracion()
            self.configuraciones = [
                {
                    "id": str(c.id),
                    "clave": c.clave,
                    "valor": c.valor or "",
                    "descripcion": c.descripcion or c.clave,
                    "grupo": c.grupo,
                    "orden": c.orden,
                    "placeholder": _placeholder_para(c.clave),
                    "hint": _hint_para(c.clave),
                    "error": "",
                }
                for c in configs
            ]
            self.valores_editados = {}
        except Exception:
            self.configuraciones = []

    async def _fetch_lugares_entrega(self):
        """Carga los lugares de entrega desde la BD (sin manejo de loading)."""
        try:
            lugares = await requisicion_service.obtener_lugares_entrega()
            self.lugares_entrega = [
                {"id": str(l.id), "nombre": l.nombre}
                for l in lugares
            ]
        except Exception:
            self.lugares_entrega = []

    async def cargar_lugares_entrega(self):
        """Alias público para recargar lugares de entrega."""
        await self._fetch_lugares_entrega()

    # ========================
    # EDICION DE CONFIGURACION
    # ========================
    def actualizar_valor(self, config_id: str, valor: str):
        """Registra un cambio pendiente y actualiza el valor visible."""
        self.valores_editados[config_id] = valor
        for i, c in enumerate(self.configuraciones):
            if c["id"] == config_id:
                updated = dict(c)
                updated["valor"] = valor
                updated["error"] = ""
                self.configuraciones[i] = updated
                break

    def normalizar_campo(self, config_id: str):
        """Normaliza y valida un campo al perder foco (on_blur)."""
        for i, c in enumerate(self.configuraciones):
            if c["id"] == config_id:
                clave = c["clave"]
                valor = c["valor"]
                if not valor or not valor.strip():
                    break
                # Normalizar
                valor_normalizado = normalizar_por_sufijo(clave, valor)
                # Validar
                error = _validar_campo_config(clave, valor_normalizado)
                # Actualizar
                updated = dict(c)
                updated["valor"] = valor_normalizado
                updated["error"] = error
                self.configuraciones[i] = updated
                if valor_normalizado != valor:
                    self.valores_editados[config_id] = valor_normalizado
                break

    def _obtener_clave(self, config_id: str) -> str:
        """Obtiene la clave de una configuracion por su ID."""
        for c in self.configuraciones:
            if c["id"] == config_id:
                return c["clave"]
        return ""

    # ========================
    # LUGARES DE ENTREGA
    # ========================
    def set_nuevo_lugar(self, valor: str):
        """Setter para el campo de nuevo lugar."""
        self.nuevo_lugar = valor
        if self.error_nuevo_lugar:
            self.error_nuevo_lugar = ""

    def validar_nuevo_lugar(self):
        """Normaliza y valida el campo de nuevo lugar al perder foco."""
        valor = self.nuevo_lugar.strip()
        if not valor:
            return
        normalizado = capitalizar_con_preposiciones(valor)
        if normalizado != self.nuevo_lugar:
            self.nuevo_lugar = normalizado
        if len(normalizado) > LUGAR_ENTREGA_MAX:
            self.error_nuevo_lugar = f"Maximo {LUGAR_ENTREGA_MAX} caracteres"
        else:
            self.error_nuevo_lugar = ""

    async def agregar_lugar(self):
        """Agrega un nuevo lugar de entrega."""
        nombre = self.nuevo_lugar.strip()
        if not nombre:
            return

        if len(nombre) > LUGAR_ENTREGA_MAX:
            self.error_nuevo_lugar = f"Maximo {LUGAR_ENTREGA_MAX} caracteres"
            return

        self.saving = True
        try:
            await requisicion_service.crear_lugar_entrega(nombre)
            self.nuevo_lugar = ""
            self.error_nuevo_lugar = ""
            await self.cargar_lugares_entrega()
            yield rx.toast.success(
                f"Lugar '{nombre}' agregado",
                position="top-center",
            )
        except Exception as e:
            yield self.manejar_error_con_toast(e, "al agregar lugar")
        finally:
            self.saving = False

    async def eliminar_lugar(self, lugar_id: str):
        """Elimina un lugar de entrega."""
        try:
            await requisicion_service.eliminar_lugar_entrega(int(lugar_id))
            await self.cargar_lugares_entrega()
            yield rx.toast.success(
                "Lugar eliminado",
                position="top-center",
            )
        except Exception as e:
            yield self.manejar_error_con_toast(e, "al eliminar lugar")

    # ========================
    # GUARDAR CONFIGURACION
    # ========================
    async def guardar_cambios(self):
        """Guarda todos los cambios pendientes, normalizados por tipo."""
        if not self.valores_editados:
            return

        # No guardar si hay errores
        if any(c.get("error", "") for c in self.configuraciones):
            yield rx.toast.error(
                "Corrige los errores antes de guardar",
                position="top-center",
            )
            return

        self.saving = True
        try:
            for config_id, valor in self.valores_editados.items():
                clave = self._obtener_clave(config_id)
                valor_normalizado = normalizar_por_sufijo(clave, valor)
                await requisicion_service.actualizar_configuracion(
                    int(config_id), valor_normalizado
                )
            self.valores_editados = {}
            await self._fetch_configuraciones()
            yield rx.toast.success(
                "Configuracion actualizada correctamente",
                position="top-center",
            )
        except Exception as e:
            yield self.manejar_error_con_toast(e, "al guardar configuracion")
        finally:
            self.saving = False

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var(cache=True)
    def configs_area_requirente(self) -> List[dict]:
        """Configuraciones del grupo Area Requirente."""
        return [c for c in self.configuraciones if c["grupo"] == "AREA_REQUIRENTE"]

    @rx.var(cache=True)
    def configs_firmas(self) -> List[dict]:
        """Configuraciones del grupo Firmas."""
        return [c for c in self.configuraciones if c["grupo"] == "FIRMAS"]

    @rx.var(cache=True)
    def configs_entrega(self) -> List[dict]:
        """Configuraciones del grupo Entrega."""
        return [c for c in self.configuraciones if c["grupo"] == "ENTREGA"]

    @rx.var(cache=True)
    def tiene_cambios(self) -> bool:
        """Indica si hay cambios pendientes por guardar."""
        return len(self.valores_editados) > 0

    @rx.var(cache=True)
    def tiene_errores(self) -> bool:
        """Indica si hay errores de validacion pendientes."""
        return any(c.get("error", "") for c in self.configuraciones)
