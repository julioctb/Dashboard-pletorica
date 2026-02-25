"""
Estado para configuración de Tipos de Entregable en Contratos.
Gestiona la pestaña/sección de configuración de entregables dentro del formulario de contrato.
"""

import reflex as rx
from typing import List, Optional

from app.presentation.components.shared.base_state import BaseState
from app.services import entregable_service
from app.core.enums import TipoEntregable, PeriodicidadEntregable
from app.entities.entregable import ContratoTipoEntregableCreate


class EntregablesConfigState(BaseState):
    """Estado para la configuración de tipos de entregable en un contrato."""

    # =========================================================================
    # DATOS
    # =========================================================================
    contrato_id: int = 0
    tipos_configurados: List[dict] = []

    # =========================================================================
    # UI
    # =========================================================================
    cargando: bool = False
    guardando: bool = False
    mostrar_modal_tipo: bool = False
    es_edicion_tipo: bool = False
    tipo_editando_id: Optional[int] = None

    # Formulario
    form_tipo_entregable: str = ""
    form_periodicidad: str = "MENSUAL"
    form_requerido: bool = True
    form_descripcion: str = ""
    form_instrucciones: str = ""
    error_tipo: str = ""

    # =========================================================================
    # SETTERS
    # =========================================================================
    @staticmethod
    def _validar_tipo_entregable(valor: str) -> str:
        return "" if valor else "Seleccione un tipo de entregable"

    def set_form_tipo_entregable(self, value: str):
        self.form_tipo_entregable = value
        self.limpiar_errores_campos(["tipo"])

    def set_form_periodicidad(self, value: str):
        self.form_periodicidad = value

    def set_form_requerido(self, value: bool):
        self.form_requerido = value

    def set_form_descripcion(self, value: str):
        self.form_descripcion = value

    def set_form_instrucciones(self, value: str):
        self.form_instrucciones = value

    # =========================================================================
    # COMPUTED VARS
    # =========================================================================
    @rx.var
    def tiene_tipos(self) -> bool:
        return len(self.tipos_configurados) > 0

    @rx.var
    def opciones_tipo_entregable(self) -> List[dict]:
        return [
            {"value": "FOTOGRAFICO", "label": "📷 Evidencia Fotográfica"},
            {"value": "REPORTE", "label": "📄 Reporte de Actividades"},
            {"value": "LISTADO", "label": "📋 Listado de Personal"},
            {"value": "DOCUMENTAL", "label": "📁 Documento Oficial"},
        ]

    @rx.var
    def opciones_periodicidad(self) -> List[dict]:
        return [
            {"value": "MENSUAL", "label": "Mensual"},
            {"value": "QUINCENAL", "label": "Quincenal"},
            {"value": "UNICO", "label": "Único (al finalizar)"},
        ]

    @rx.var
    def tipos_disponibles_para_agregar(self) -> List[dict]:
        tipos_usados = {t.get("tipo_entregable") for t in self.tipos_configurados}
        return [opt for opt in self.opciones_tipo_entregable if opt["value"] not in tipos_usados]

    @rx.var
    def puede_agregar_tipo(self) -> bool:
        return len(self.tipos_disponibles_para_agregar) > 0

    @rx.var
    def puede_guardar_tipo(self) -> bool:
        return bool(self.form_tipo_entregable) and not self.error_tipo

    @rx.var
    def titulo_modal(self) -> str:
        return "Editar Tipo" if self.es_edicion_tipo else "Agregar Tipo de Entregable"

    # =========================================================================
    # CARGA DE DATOS
    # =========================================================================
    async def cargar_configuracion(self, contrato_id: int):
        self.contrato_id = contrato_id
        self.cargando = True
        try:
            config = await entregable_service.obtener_configuracion_contrato(contrato_id)
            self.tipos_configurados = [
                {
                    "id": c.get("id"),
                    "tipo_entregable": c.get("tipo_entregable"),
                    "tipo_label": self._get_tipo_label(c.get("tipo_entregable")),
                    "periodicidad": c.get("periodicidad"),
                    "periodicidad_label": self._get_periodicidad_label(c.get("periodicidad")),
                    "requerido": c.get("requerido", True),
                    "descripcion": c.get("descripcion") or "",
                    "instrucciones": c.get("instrucciones") or "",
                }
                for c in config
            ]
        except Exception:
            self.tipos_configurados = []
        finally:
            self.cargando = False

    def _get_tipo_label(self, tipo: str) -> str:
        labels = {
            "FOTOGRAFICO": "📷 Evidencia Fotográfica",
            "REPORTE": "📄 Reporte de Actividades",
            "LISTADO": "📋 Listado de Personal",
            "DOCUMENTAL": "📁 Documento Oficial",
        }
        return labels.get(tipo, tipo)

    def _get_periodicidad_label(self, periodicidad: str) -> str:
        labels = {"MENSUAL": "Mensual", "QUINCENAL": "Quincenal", "UNICO": "Único"}
        return labels.get(periodicidad, periodicidad)

    # =========================================================================
    # MODAL
    # =========================================================================
    def abrir_modal_agregar(self):
        if not self.puede_agregar_tipo:
            self.mostrar_mensaje("Ya se han configurado todos los tipos disponibles", "info")
            return
        self._limpiar_formulario()
        self.es_edicion_tipo = False
        self.tipo_editando_id = None
        self.mostrar_modal_tipo = True

    def abrir_modal_editar(self, tipo_id: int):
        tipo = next((t for t in self.tipos_configurados if t["id"] == tipo_id), None)
        if not tipo:
            return
        self.es_edicion_tipo = True
        self.tipo_editando_id = tipo_id
        self.form_tipo_entregable = tipo["tipo_entregable"]
        self.form_periodicidad = tipo["periodicidad"]
        self.form_requerido = tipo["requerido"]
        self.form_descripcion = tipo["descripcion"]
        self.form_instrucciones = tipo["instrucciones"]
        self.mostrar_modal_tipo = True

    def cerrar_modal_tipo(self):
        self.mostrar_modal_tipo = False
        self._limpiar_formulario()

    def _limpiar_formulario(self):
        self.form_tipo_entregable = ""
        self.form_periodicidad = "MENSUAL"
        self.form_requerido = True
        self.form_descripcion = ""
        self.form_instrucciones = ""
        self.limpiar_errores_campos(["tipo"])
        self.es_edicion_tipo = False
        self.tipo_editando_id = None

    def validar_tipo_entregable_campo(self):
        self.validar_y_asignar_error(
            valor=self.form_tipo_entregable,
            validador=self._validar_tipo_entregable,
            error_attr="error_tipo",
        )

    # =========================================================================
    # GUARDAR
    # =========================================================================
    async def guardar_tipo(self):
        if not self.validar_y_asignar_error(
            valor=self.form_tipo_entregable,
            validador=self._validar_tipo_entregable,
            error_attr="error_tipo",
        ):
            return
        self.guardando = True
        try:
            config = ContratoTipoEntregableCreate(
                contrato_id=self.contrato_id,
                tipo_entregable=TipoEntregable(self.form_tipo_entregable),
                periodicidad=PeriodicidadEntregable(self.form_periodicidad),
                requerido=self.form_requerido,
                descripcion=self.form_descripcion or None,
                instrucciones=self.form_instrucciones or None,
            )
            await entregable_service.configurar_tipo_entregable(config)
            self.mostrar_mensaje(
                "Tipo guardado correctamente" if self.es_edicion_tipo else "Tipo agregado correctamente",
                "success",
            )
            self.cerrar_modal_tipo()
            await self.cargar_configuracion(self.contrato_id)
        except Exception as e:
            self.mostrar_mensaje(f"Error al guardar: {str(e)}", "error")
        finally:
            self.guardando = False

    # =========================================================================
    # ELIMINAR
    # =========================================================================
    async def eliminar_tipo(self, tipo_id: int):
        try:
            from app.database import db_manager
            supabase = db_manager.get_client()
            supabase.table("contrato_tipo_entregable").delete().eq("id", tipo_id).execute()
            self.mostrar_mensaje("Tipo eliminado", "success")
            await self.cargar_configuracion(self.contrato_id)
        except Exception as e:
            self.mostrar_mensaje(f"Error al eliminar: {str(e)}", "error")
