"""
Estado de Reflex para el módulo de Categorías de Contrato.
Maneja el estado de la UI para gestión de categorías asignadas a contratos.
"""
import reflex as rx
from typing import List, Optional
from decimal import Decimal, InvalidOperation

from app.presentation.components.shared.base_state import (
    BaseState,
    crear_setter,
    crear_setter_numerico,
)
from app.services import contrato_categoria_service, categoria_puesto_service
from app.core.text_utils import formatear_moneda

from app.entities import (
    ContratoCategoriaCreate,
    ContratoCategoriaUpdate,
)

# Las excepciones se manejan centralizadamente en BaseState
# BusinessRuleError se importa para lanzar errores de negocio
from app.core.exceptions import BusinessRuleError

from .contrato_categorias_validators import (
    validar_categoria_puesto_id,
    validar_cantidad_minima,
    validar_cantidad_maxima,
    validar_costo_unitario,
    validar_notas,
)


class ContratoCategoriaState(BaseState):
    """Estado para el módulo de Categorías de Contrato"""

    # ========================
    # ESTADO DE DATOS
    # ========================
    categorias_asignadas: List[dict] = []
    categorias_disponibles: List[dict] = []
    categoria_seleccionada: Optional[dict] = None

    # Contrato actual
    contrato_id: int = 0
    contrato_codigo: str = ""
    contrato_tiene_personal: bool = False
    tipo_servicio_id: int = 0

    # Resumen de personal
    total_minimo: int = 0
    total_maximo: int = 0
    cantidad_categorias: int = 0
    costo_minimo_total: str = ""
    costo_maximo_total: str = ""

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_categorias: bool = False
    mostrar_modal_categoria_form: bool = False
    mostrar_modal_confirmar_eliminar: bool = False
    es_edicion_categoria: bool = False

    # ========================
    # ESTADO DEL FORMULARIO
    # ========================
    form_categoria_puesto_id: str = ""
    form_cantidad_minima: str = ""
    form_cantidad_maxima: str = ""
    form_costo_unitario: str = ""
    form_notas: str = ""

    # ========================
    # ERRORES DE VALIDACIÓN
    # ========================
    error_categoria_puesto_id: str = ""
    error_cantidad_minima: str = ""
    error_cantidad_maxima: str = ""
    error_costo_unitario: str = ""
    error_notas: str = ""

    # ========================
    # SETTERS (generados con helpers para reducir código repetitivo)
    # ========================
    set_form_categoria_puesto_id = crear_setter("form_categoria_puesto_id")
    set_form_cantidad_minima = crear_setter_numerico("form_cantidad_minima")
    set_form_cantidad_maxima = crear_setter_numerico("form_cantidad_maxima")
    set_form_costo_unitario = crear_setter("form_costo_unitario", formatear_moneda)
    set_form_notas = crear_setter("form_notas")

    # ========================
    # VALIDACIÓN EN TIEMPO REAL
    # ========================
    def validar_categoria_puesto_id_campo(self):
        self.error_categoria_puesto_id = validar_categoria_puesto_id(self.form_categoria_puesto_id)

    def validar_cantidad_minima_campo(self):
        self.error_cantidad_minima = validar_cantidad_minima(self.form_cantidad_minima)

    def validar_cantidad_maxima_campo(self):
        self.error_cantidad_maxima = validar_cantidad_maxima(
            self.form_cantidad_maxima,
            self.form_cantidad_minima
        )

    def validar_costo_unitario_campo(self):
        self.error_costo_unitario = validar_costo_unitario(self.form_costo_unitario)

    def validar_notas_campo(self):
        self.error_notas = validar_notas(self.form_notas)

    def _validar_todos_los_campos(self):
        """Valida todos los campos del formulario"""
        self.validar_categoria_puesto_id_campo()
        self.validar_cantidad_minima_campo()
        self.validar_cantidad_maxima_campo()
        self.validar_costo_unitario_campo()
        self.validar_notas_campo()

    @rx.var
    def tiene_errores_formulario(self) -> bool:
        """Verifica si hay errores de validación"""
        return bool(
            self.error_categoria_puesto_id or
            self.error_cantidad_minima or
            self.error_cantidad_maxima or
            self.error_costo_unitario or
            self.error_notas
        )

    @rx.var
    def puede_guardar_categoria(self) -> bool:
        """Verifica si se puede guardar la categoría"""
        # En edición no se necesita categoria_puesto_id
        if self.es_edicion_categoria:
            tiene_requeridos = bool(
                self.form_cantidad_minima and
                self.form_cantidad_maxima
            )
        else:
            tiene_requeridos = bool(
                self.form_categoria_puesto_id and
                self.form_cantidad_minima and
                self.form_cantidad_maxima
            )
        return tiene_requeridos and not self.tiene_errores_formulario and not self.saving

    @rx.var
    def opciones_categoria(self) -> List[dict]:
        """Opciones formateadas para el select de categoría"""
        return [
            {"value": str(c["id"]), "label": f"{c['clave']} - {c['nombre']}"}
            for c in self.categorias_disponibles
        ]

    @rx.var
    def tiene_categorias_disponibles(self) -> bool:
        """Verifica si hay categorías disponibles para asignar"""
        return len(self.categorias_disponibles) > 0

    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def abrir_modal_categorias(self, contrato: dict):
        """Abre el modal de categorías para un contrato"""
        self.contrato_id = contrato.get("id", 0)
        self.contrato_codigo = contrato.get("codigo", "")
        self.contrato_tiene_personal = contrato.get("tiene_personal", False)
        self.tipo_servicio_id = contrato.get("tipo_servicio_id", 0)

        self.mostrar_modal_categorias = True
        await self.cargar_categorias()

    def cerrar_modal_categorias(self):
        """Cierra el modal de categorías"""
        self.mostrar_modal_categorias = False
        self._limpiar_estado()

    async def cargar_categorias(self):
        """Carga las categorías asignadas y disponibles"""
        if not self.contrato_id:
            return

        self.loading = True
        try:
            # Obtener categorías asignadas con resumen
            resumen = await contrato_categoria_service.obtener_resumen_de_contrato(self.contrato_id)
            self.categorias_asignadas = []
            for cc in resumen:
                cat_dict = cc.model_dump()
                cat_dict["costo_unitario_fmt"] = formatear_moneda(str(cc.costo_unitario)) if cc.costo_unitario else "-"
                cat_dict["costo_minimo_fmt"] = formatear_moneda(str(cc.costo_minimo)) if cc.costo_minimo else "-"
                cat_dict["costo_maximo_fmt"] = formatear_moneda(str(cc.costo_maximo)) if cc.costo_maximo else "-"
                self.categorias_asignadas.append(cat_dict)

            # Obtener totales
            totales = await contrato_categoria_service.calcular_total_personal(self.contrato_id)
            self.total_minimo = totales.total_minimo
            self.total_maximo = totales.total_maximo
            self.cantidad_categorias = totales.cantidad_categorias
            self.costo_minimo_total = formatear_moneda(str(totales.costo_minimo_total)) if totales.costo_minimo_total else "-"
            self.costo_maximo_total = formatear_moneda(str(totales.costo_maximo_total)) if totales.costo_maximo_total else "-"

            # Obtener categorías disponibles
            disponibles = await contrato_categoria_service.obtener_categorias_disponibles(self.contrato_id)
            self.categorias_disponibles = disponibles

        except Exception as e:
            self.manejar_error(e, "al cargar categorías")
            self.categorias_asignadas = []
        finally:
            self.finalizar_carga()

    # ========================
    # CRUD DE CATEGORÍAS
    # ========================
    def abrir_modal_agregar_categoria(self):
        """Abre el modal para agregar una nueva categoría"""
        self._limpiar_formulario()
        self.es_edicion_categoria = False
        self.mostrar_modal_categoria_form = True

    def abrir_modal_editar_categoria(self, categoria: dict):
        """Abre el modal para editar una categoría"""
        self._limpiar_formulario()
        self.es_edicion_categoria = True
        self.categoria_seleccionada = categoria
        self._cargar_categoria_en_formulario(categoria)
        self.mostrar_modal_categoria_form = True

    def cerrar_modal_categoria_form(self):
        """Cierra el modal de formulario de categoría"""
        self.mostrar_modal_categoria_form = False
        self._limpiar_formulario()

    async def guardar_categoria(self):
        """Guarda la categoría (crear o actualizar)"""
        self._validar_todos_los_campos()

        if self.tiene_errores_formulario:
            return rx.toast.error(
                "Por favor corrige los errores del formulario",
                position="top-center"
            )

        self.saving = True
        try:
            if self.es_edicion_categoria:
                mensaje = await self._actualizar_categoria()
            else:
                mensaje = await self._crear_categoria()

            self.cerrar_modal_categoria_form()
            await self.cargar_categorias()

            return rx.toast.success(mensaje, position="top-center")

        except Exception as e:
            self.manejar_error(e, "al guardar categoría")
        finally:
            self.finalizar_guardado()

    async def _crear_categoria(self) -> str:
        """Crea una nueva asignación de categoría"""
        categoria_create = ContratoCategoriaCreate(
            contrato_id=self.contrato_id,
            categoria_puesto_id=int(self.form_categoria_puesto_id),
            cantidad_minima=int(self.form_cantidad_minima),
            cantidad_maxima=int(self.form_cantidad_maxima),
            costo_unitario=self._parse_decimal(self.form_costo_unitario),
            notas=self.form_notas.strip() or None,
        )

        await contrato_categoria_service.crear(categoria_create)
        return "Categoría asignada exitosamente"

    async def _actualizar_categoria(self) -> str:
        """Actualiza una asignación existente"""
        if not self.categoria_seleccionada:
            raise BusinessRuleError("No hay categoría seleccionada")

        categoria_update = ContratoCategoriaUpdate(
            cantidad_minima=int(self.form_cantidad_minima),
            cantidad_maxima=int(self.form_cantidad_maxima),
            costo_unitario=self._parse_decimal(self.form_costo_unitario),
            notas=self.form_notas.strip() or None,
        )

        await contrato_categoria_service.actualizar(
            self.categoria_seleccionada["id"],
            categoria_update
        )
        return "Categoría actualizada exitosamente"

    def abrir_confirmar_eliminar(self, categoria: dict):
        """Abre el modal de confirmación para eliminar"""
        self.categoria_seleccionada = categoria
        self.mostrar_modal_confirmar_eliminar = True

    def cerrar_confirmar_eliminar(self):
        """Cierra el modal de confirmación"""
        self.mostrar_modal_confirmar_eliminar = False
        self.categoria_seleccionada = None

    async def eliminar_categoria(self):
        """Elimina la categoría seleccionada"""
        if not self.categoria_seleccionada:
            return

        self.saving = True
        try:
            await contrato_categoria_service.eliminar(self.categoria_seleccionada["id"])
            self.cerrar_confirmar_eliminar()
            await self.cargar_categorias()

            return rx.toast.success("Categoría eliminada", position="top-center")

        except Exception as e:
            self.manejar_error(e, "al eliminar categoría")
        finally:
            self.finalizar_guardado()

    # ========================
    # HELPERS
    # ========================
    def _limpiar_estado(self):
        """Limpia todo el estado"""
        self.categorias_asignadas = []
        self.categorias_disponibles = []
        self.categoria_seleccionada = None
        self.contrato_id = 0
        self.contrato_codigo = ""
        self.contrato_tiene_personal = False
        self.tipo_servicio_id = 0
        self.total_minimo = 0
        self.total_maximo = 0
        self.cantidad_categorias = 0
        self.costo_minimo_total = ""
        self.costo_maximo_total = ""
        self._limpiar_formulario()

    def _limpiar_formulario(self):
        """Limpia el formulario de categoría"""
        self.form_categoria_puesto_id = ""
        self.form_cantidad_minima = ""
        self.form_cantidad_maxima = ""
        self.form_costo_unitario = ""
        self.form_notas = ""
        self._limpiar_errores()
        self.categoria_seleccionada = None
        self.es_edicion_categoria = False

    def _limpiar_errores(self):
        """Limpia los errores de validación"""
        self.error_categoria_puesto_id = ""
        self.error_cantidad_minima = ""
        self.error_cantidad_maxima = ""
        self.error_costo_unitario = ""
        self.error_notas = ""

    def _cargar_categoria_en_formulario(self, categoria: dict):
        """Carga datos de una categoría en el formulario"""
        self.form_categoria_puesto_id = str(categoria.get("categoria_puesto_id", ""))
        self.form_cantidad_minima = str(categoria.get("cantidad_minima", ""))
        self.form_cantidad_maxima = str(categoria.get("cantidad_maxima", ""))

        costo = categoria.get("costo_unitario")
        self.form_costo_unitario = formatear_moneda(str(costo)) if costo else ""

        self.form_notas = categoria.get("notas", "") or ""

    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """Parsea string a Decimal"""
        if not value:
            return None
        try:
            limpio = value.replace(",", "").replace("$", "").replace(" ", "").strip()
            if not limpio:
                return None
            return Decimal(limpio)
        except InvalidOperation:
            return None
