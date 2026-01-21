"""
Estado de Reflex para el módulo de Plazas.
Maneja el estado de la UI y las operaciones del módulo.
"""
import reflex as rx
from typing import List, Optional
from decimal import Decimal
from datetime import date

from app.presentation.components.shared.base_state import BaseState
from app.services import plaza_service, contrato_categoria_service, contrato_service
from app.core.text_utils import formatear_moneda, formatear_fecha

from app.entities import (
    Plaza,
    PlazaCreate,
    PlazaUpdate,
    PlazaResumen,
    EstatusPlaza,
)

from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    DatabaseError,
    BusinessRuleError,
)


class PlazasState(BaseState):
    """Estado para el módulo de Plazas con toggle de vista"""

    # ========================
    # ESTADO DE VISTA
    # ========================
    view_mode: str = "table"  # "table" o "cards"

    # ========================
    # ESTADO DE DATOS
    # ========================
    plazas: List[dict] = []
    plaza_seleccionada: Optional[dict] = None
    total_plazas: int = 0

    # Contexto del contrato/categoría
    contrato_id: int = 0
    contrato_codigo: str = ""
    contrato_categoria_id: int = 0
    categoria_nombre: str = ""

    # Vista inicial: resumen de categorías con plazas
    resumen_categorias: List[dict] = []

    # Selector de contratos (para crear nuevas plazas)
    contratos_disponibles: List[dict] = []
    categorias_contrato: List[dict] = []
    contrato_seleccionado_id: str = ""  # String para el select
    categoria_seleccionada_id: str = ""  # String para el select
    cargando_contratos: bool = False
    cargando_categorias: bool = False

    # Resumen de plazas
    plazas_vacantes: int = 0
    plazas_ocupadas: int = 0
    plazas_suspendidas: int = 0

    # ========================
    # ESTADO DE UI
    # ========================
    mostrar_modal_plaza: bool = False
    mostrar_modal_detalle: bool = False
    mostrar_modal_confirmar_cancelar: bool = False
    mostrar_modal_crear_lote: bool = False
    mostrar_modal_asignar_empleado: bool = False
    es_edicion: bool = False

    # Estado para asignación de empleado
    empleados_disponibles: List[dict] = []
    empleado_seleccionado_id: str = ""
    cargando_empleados: bool = False

    # ========================
    # FILTROS
    # ========================
    filtro_estatus: str = "TODOS"
    search: str = ""

    # ========================
    # ESTADO DEL FORMULARIO
    # ========================
    form_numero_plaza: str = ""
    form_codigo: str = ""
    form_empleado_id: str = ""
    form_fecha_inicio: str = ""
    form_fecha_fin: str = ""
    form_salario_mensual: str = ""
    form_estatus: str = EstatusPlaza.VACANTE.value
    form_notas: str = ""

    # Formulario de creación en lote
    form_cantidad: str = "1"
    form_prefijo_codigo: str = ""

    # ========================
    # ERRORES DE VALIDACIÓN
    # ========================
    error_numero_plaza: str = ""
    error_codigo: str = ""
    error_fecha_inicio: str = ""
    error_salario_mensual: str = ""
    error_cantidad: str = ""

    # ========================
    # SETTERS DE VISTA
    # ========================
    def set_view_table(self):
        """Cambiar a vista de tabla."""
        self.view_mode = "table"

    def set_view_cards(self):
        """Cambiar a vista de cards."""
        self.view_mode = "cards"

    def toggle_view(self):
        """Alternar entre vistas."""
        self.view_mode = "cards" if self.view_mode == "table" else "table"

    @rx.var
    def is_table_view(self) -> bool:
        """True si la vista actual es tabla."""
        return self.view_mode == "table"

    @rx.var
    def is_cards_view(self) -> bool:
        """True si la vista actual es cards."""
        return self.view_mode == "cards"

    @rx.var
    def mostrar_vista_inicial(self) -> bool:
        """True si estamos en vista inicial (sin categoría seleccionada)."""
        return self.contrato_categoria_id == 0 and self.contrato_id == 0

    @rx.var
    def tiene_resumen(self) -> bool:
        """True si hay datos en el resumen inicial."""
        return len(self.resumen_categorias) > 0

    # ========================
    # SETTERS
    # ========================
    def set_search(self, value):
        self.search = value if value else ""

    def set_filtro_estatus(self, value):
        self.filtro_estatus = value if value else ""
        return PlazasState.filtrar_plazas

    def set_form_numero_plaza(self, value):
        self.form_numero_plaza = value if value else ""

    def set_form_codigo(self, value):
        self.form_codigo = value.upper() if value else ""

    def set_form_empleado_id(self, value):
        self.form_empleado_id = value if value else ""

    def set_form_fecha_inicio(self, value):
        self.form_fecha_inicio = value if value else ""

    def set_form_fecha_fin(self, value):
        self.form_fecha_fin = value if value else ""

    def set_form_salario_mensual(self, value):
        self.form_salario_mensual = formatear_moneda(value) if value else ""

    def set_form_estatus(self, value):
        self.form_estatus = value if value else ""

    def set_form_notas(self, value):
        self.form_notas = value if value else ""

    def set_form_cantidad(self, value):
        self.form_cantidad = value if value else ""

    def set_form_prefijo_codigo(self, value):
        self.form_prefijo_codigo = value.upper() if value else ""

    def set_empleado_seleccionado_id(self, value):
        self.empleado_seleccionado_id = value if value else ""

    def set_contrato_seleccionado_id(self, value):
        """Al seleccionar un contrato, limpiar y disparar carga de categorías"""
        self.contrato_seleccionado_id = value if value else ""
        self.categoria_seleccionada_id = ""
        self.categorias_contrato = []
        self.contrato_categoria_id = 0
        self.plazas = []
        self.total_plazas = 0

        if value:
            return PlazasState.cargar_categorias_de_contrato(int(value))

    def set_categoria_seleccionada_id(self, value):
        """Al seleccionar una categoría, abrir modal de creación de plazas"""
        self.categoria_seleccionada_id = value if value else ""

        if value:
            self.contrato_categoria_id = int(value)
            # Obtener datos de la categoría
            categoria = next(
                (c for c in self.categorias_contrato if str(c.get("id")) == value),
                None
            )
            if categoria:
                self.categoria_nombre = categoria.get("categoria_nombre", "")
                # Pre-llenar formulario
                self.form_cantidad = str(categoria.get("plazas_pendientes", 1))
                self.form_prefijo_codigo = categoria.get("categoria_clave", "")
                self.form_fecha_inicio = date.today().isoformat()
                self.form_salario_mensual = ""
                self.form_fecha_fin = ""
                # Abrir modal de creación
                self.mostrar_modal_crear_lote = True
        else:
            self.contrato_categoria_id = 0
            self.categoria_nombre = ""
            self.plazas = []
            self.total_plazas = 0

    # ========================
    # COMPUTED VARS
    # ========================
    @rx.var
    def opciones_estatus(self) -> List[dict]:
        """Opciones para el select de estatus"""
        return [
            {"value": "TODOS", "label": "Todos"},
            {"value": EstatusPlaza.VACANTE.value, "label": "Vacante"},
            {"value": EstatusPlaza.OCUPADA.value, "label": "Ocupada"},
            {"value": EstatusPlaza.SUSPENDIDA.value, "label": "Suspendida"},
            {"value": EstatusPlaza.CANCELADA.value, "label": "Cancelada"},
        ]

    @rx.var
    def opciones_estatus_form(self) -> List[dict]:
        """Opciones para el select de estatus en formulario (sin TODOS)"""
        return [
            {"value": EstatusPlaza.VACANTE.value, "label": "Vacante"},
            {"value": EstatusPlaza.OCUPADA.value, "label": "Ocupada"},
            {"value": EstatusPlaza.SUSPENDIDA.value, "label": "Suspendida"},
        ]

    @rx.var
    def plazas_filtradas(self) -> List[dict]:
        """Plazas filtradas por estatus y búsqueda"""
        resultado = self.plazas

        # Filtrar por estatus
        if self.filtro_estatus and self.filtro_estatus != "TODOS":
            resultado = [p for p in resultado if p.get("estatus") == self.filtro_estatus]

        # Filtrar por búsqueda
        if self.search:
            termino = self.search.lower()
            resultado = [
                p for p in resultado
                if termino in p.get("codigo", "").lower()
                or termino in str(p.get("numero_plaza", ""))
                or termino in p.get("empleado_nombre", "").lower()
            ]

        return resultado

    @rx.var
    def tiene_filtros_activos(self) -> bool:
        """Indica si hay algún filtro aplicado"""
        return self.filtro_estatus != "TODOS" or bool(self.search.strip())

    @rx.var
    def puede_guardar(self) -> bool:
        """Verifica si se puede guardar el formulario"""
        tiene_requeridos = bool(
            self.form_fecha_inicio and
            self.form_salario_mensual
        )
        sin_errores = not bool(
            self.error_numero_plaza or
            self.error_codigo or
            self.error_fecha_inicio or
            self.error_salario_mensual
        )
        return tiene_requeridos and sin_errores and not self.saving

    @rx.var
    def titulo_contexto(self) -> str:
        """Título con el contexto del contrato/categoría"""
        if self.contrato_codigo and self.categoria_nombre:
            return f"{self.contrato_codigo} - {self.categoria_nombre}"
        return "Plazas"

    @rx.var
    def breadcrumb_items(self) -> List[dict]:
        """Items para el breadcrumb en vista detalle"""
        items = [{"texto": "Plazas", "href": "/plazas"}]
        if self.contrato_codigo:
            items.append({"texto": self.contrato_codigo, "href": ""})
        if self.categoria_nombre:
            items.append({"texto": self.categoria_nombre, "href": ""})
        return items

    @rx.var
    def mostrar_selector_contrato(self) -> bool:
        """True si debemos mostrar el selector de contratos"""
        return self.contrato_categoria_id == 0 and not self.loading

    @rx.var
    def tiene_contexto(self) -> bool:
        """True si ya tenemos un contrato_categoria_id definido"""
        return self.contrato_categoria_id > 0

    @rx.var
    def opciones_contratos(self) -> List[dict]:
        """Opciones para el select de contratos (con plazas pendientes)"""
        return [
            {
                "value": str(c.get("id")),
                "label": f"{c.get('codigo')} - {c.get('empresa_nombre', '')} ({c.get('total_pendientes', 0)} pendientes)"
            }
            for c in self.contratos_disponibles
        ]

    @rx.var
    def opciones_categorias(self) -> List[dict]:
        """Opciones para el select de categorías (con plazas pendientes)"""
        return [
            {
                "value": str(c.get("id")),
                "label": f"{c.get('categoria_clave', '')} - {c.get('categoria_nombre', '')} ({c.get('plazas_pendientes', 0)} pendientes)"
            }
            for c in self.categorias_contrato
        ]

    @rx.var
    def opciones_empleados(self) -> List[dict]:
        """Opciones para el select de empleados disponibles"""
        return [
            {
                "value": str(e.get("id")),
                "label": f"{e.get('clave', '')} - {e.get('nombre_completo', '')}"
            }
            for e in self.empleados_disponibles
        ]

    @rx.var
    def puede_asignar_empleado(self) -> bool:
        """Verifica si se puede asignar el empleado seleccionado"""
        return bool(self.empleado_seleccionado_id) and not self.saving

    # ========================
    # OPERACIONES PRINCIPALES
    # ========================
    async def cargar_plazas_de_contrato(self, contrato_id: int):
        """Cargar todas las plazas de un contrato"""
        self.loading = True
        self.contrato_id = contrato_id

        try:
            # Obtener resumen de plazas con datos enriquecidos
            plazas_resumen = await plaza_service.obtener_resumen_de_contrato(contrato_id)

            self.plazas = []
            for plaza in plazas_resumen:
                plaza_dict = plaza.model_dump(mode='json')
                # Formatear datos para mostrar
                plaza_dict["fecha_inicio_fmt"] = formatear_fecha(plaza.fecha_inicio)
                plaza_dict["fecha_fin_fmt"] = formatear_fecha(plaza.fecha_fin) if plaza.fecha_fin else "-"
                plaza_dict["salario_fmt"] = formatear_moneda(str(plaza.salario_mensual))
                self.plazas.append(plaza_dict)

            self.total_plazas = len(self.plazas)
            self._actualizar_contadores()

            # Obtener código del contrato si no lo tenemos
            if not self.contrato_codigo and self.plazas:
                self.contrato_codigo = self.plazas[0].get("contrato_codigo", "")

        except Exception as e:
            self.manejar_error(e, "cargar plazas")
            self.plazas = []
            return rx.toast.error(f"Error al cargar plazas: {e}")
        finally:
            self.loading = False

    async def cargar_plazas_de_categoria(self, contrato_categoria_id: int):
        """Cargar plazas de una categoría específica con datos del empleado"""
        self.loading = True
        self.contrato_categoria_id = contrato_categoria_id

        try:
            # Usar obtener_resumen_de_categoria que incluye datos del empleado
            plazas_resumen = await plaza_service.obtener_resumen_de_categoria(
                contrato_categoria_id,
                incluir_canceladas=True
            )

            self.plazas = []
            for plaza in plazas_resumen:
                plaza_dict = plaza.model_dump(mode='json')
                plaza_dict["fecha_inicio_fmt"] = formatear_fecha(plaza.fecha_inicio)
                plaza_dict["fecha_fin_fmt"] = formatear_fecha(plaza.fecha_fin) if plaza.fecha_fin else "-"
                plaza_dict["salario_fmt"] = formatear_moneda(str(plaza.salario_mensual))
                self.plazas.append(plaza_dict)

            self.total_plazas = len(self.plazas)
            self._actualizar_contadores()

        except Exception as e:
            self.manejar_error(e, "cargar plazas de categoría")
            self.plazas = []
            return rx.toast.error(f"Error al cargar plazas: {e}")
        finally:
            self.loading = False

    def _actualizar_contadores(self):
        """Actualiza los contadores de plazas por estatus"""
        self.plazas_vacantes = len([p for p in self.plazas if p.get("estatus") == "VACANTE"])
        self.plazas_ocupadas = len([p for p in self.plazas if p.get("estatus") == "OCUPADA"])
        self.plazas_suspendidas = len([p for p in self.plazas if p.get("estatus") == "SUSPENDIDA"])

    def filtrar_plazas(self):
        """Método dummy para trigger de filtrado (el filtrado real es computed)"""
        pass

    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.filtro_estatus = "TODOS"
        self.search = ""

    # ========================
    # CARGA DE CONTRATOS Y CATEGORÍAS
    # ========================
    async def cargar_contratos_con_personal(self):
        """Carga contratos que tienen plazas pendientes por asignar"""
        self.cargando_contratos = True
        try:
            # Solo contratos con categorías que tienen plazas pendientes
            contratos = await plaza_service.obtener_contratos_con_plazas_pendientes()
            self.contratos_disponibles = contratos

        except Exception as e:
            self.manejar_error(e, "cargar contratos")
            self.contratos_disponibles = []
            return rx.toast.error(f"Error al cargar contratos: {e}")
        finally:
            self.cargando_contratos = False

    async def cargar_categorias_de_contrato(self, contrato_id: int):
        """Carga las categorías con plazas pendientes de un contrato (para el selector)"""
        self.cargando_categorias = True
        # NO establecer self.contrato_id aquí - solo se usa para cargar opciones del selector

        try:
            categorias_resumen = await contrato_categoria_service.obtener_resumen_de_contrato(
                contrato_id
            )

            # Obtener conteo de plazas por categoría
            from app.repositories.plaza_repository import SupabasePlazaRepository
            repo = SupabasePlazaRepository()

            categorias_con_pendientes = []
            for c in categorias_resumen:
                plazas_actuales = await repo.contar_por_contrato_categoria(c.id)
                plazas_pendientes = c.cantidad_maxima - plazas_actuales

                if plazas_pendientes > 0:
                    categorias_con_pendientes.append({
                        "id": c.id,
                        "categoria_puesto_id": c.categoria_puesto_id,
                        "categoria_clave": c.categoria_clave,
                        "categoria_nombre": c.categoria_nombre,
                        "cantidad_minima": c.cantidad_minima,
                        "cantidad_maxima": c.cantidad_maxima,
                        "plazas_actuales": plazas_actuales,
                        "plazas_pendientes": plazas_pendientes,
                    })

            self.categorias_contrato = categorias_con_pendientes

            # Obtener código del contrato
            contrato = next(
                (c for c in self.contratos_disponibles if c.get("id") == contrato_id),
                None
            )
            if contrato:
                self.contrato_codigo = contrato.get("codigo", "")

        except Exception as e:
            self.manejar_error(e, "cargar categorías")
            self.categorias_contrato = []
            return rx.toast.error(f"Error al cargar categorías: {e}")
        finally:
            self.cargando_categorias = False

    # ========================
    # CARGA INICIAL
    # ========================
    async def cargar_resumen_inicial(self):
        """Carga el resumen de categorías que tienen plazas creadas"""
        self.loading = True
        try:
            resumen = await plaza_service.obtener_resumen_categorias_con_plazas()
            self.resumen_categorias = resumen

        except Exception as e:
            self.manejar_error(e, "cargar resumen")
            self.resumen_categorias = []
            return rx.toast.error(f"Error al cargar resumen: {e}")
        finally:
            self.loading = False

    async def seleccionar_categoria_resumen(self, item: dict):
        """Navega a las plazas de una categoría desde el resumen inicial"""
        cc_id = item.get("contrato_categoria_id")
        if cc_id:
            self.contrato_categoria_id = cc_id
            self.contrato_id = item.get("contrato_id", 0)
            self.contrato_codigo = item.get("contrato_codigo", "")
            self.categoria_nombre = item.get("categoria_nombre", "")
            await self.cargar_plazas_de_categoria(cc_id)

    def volver_a_resumen(self):
        """Vuelve a la vista de resumen inicial"""
        self._limpiar_estado()
        return PlazasState.cargar_resumen_inicial

    async def cargar_desde_url(self):
        """
        Carga las plazas basándose en los query params de la URL.
        Espera: ?contrato_categoria_id=X o ?contrato_id=X

        Si no hay contexto, resetea el estado y carga los contratos disponibles.
        """
        # Obtener query params del router (Reflex 0.8.9+)
        contrato_categoria_id = self.router.url.query_parameters.get("contrato_categoria_id", "")
        contrato_id = self.router.url.query_parameters.get("contrato_id", "")

        # Si no hay contexto en URL, resetear todo el estado
        if not contrato_categoria_id and not contrato_id:
            self._limpiar_estado()

        if contrato_categoria_id:
            try:
                cc_id = int(contrato_categoria_id)
                await self.cargar_plazas_de_categoria(cc_id)
            except ValueError:
                return rx.toast.error("ID de categoría inválido")
        elif contrato_id:
            try:
                c_id = int(contrato_id)
                await self.cargar_plazas_de_contrato(c_id)
            except ValueError:
                return rx.toast.error("ID de contrato inválido")
        else:
            # Sin contexto - cargar resumen de categorías con plazas
            await self.cargar_resumen_inicial()
            # También cargar contratos disponibles para crear nuevas plazas
            await self.cargar_contratos_con_personal()

    # ========================
    # OPERACIONES CRUD
    # ========================
    async def abrir_modal_crear(self):
        """Abrir modal para crear nueva plaza"""
        # Validar que tenemos contexto
        if not self.contrato_categoria_id:
            return rx.toast.error(
                "Selecciona una categoría de contrato primero"
            )

        self._limpiar_formulario()
        self.es_edicion = False
        self.form_fecha_inicio = date.today().isoformat()

        # Auto-generar el siguiente número de plaza
        try:
            from app.repositories.plaza_repository import SupabasePlazaRepository
            repo = SupabasePlazaRepository()
            siguiente_numero = await repo.obtener_siguiente_numero_plaza(
                self.contrato_categoria_id
            )
            self.form_numero_plaza = str(siguiente_numero)
        except Exception as e:
            self.form_numero_plaza = "1"

        self.mostrar_modal_plaza = True

    def abrir_modal_editar(self, plaza: dict):
        """Abrir modal para editar plaza"""
        self._limpiar_formulario()
        self.es_edicion = True
        self.plaza_seleccionada = plaza
        self._cargar_plaza_en_formulario(plaza)
        self.mostrar_modal_plaza = True

    def cerrar_modal_plaza(self):
        """Cerrar modal de crear/editar"""
        self.mostrar_modal_plaza = False
        self._limpiar_formulario()

    def abrir_modal_crear_lote(self):
        """Abrir modal para crear plazas en lote"""
        # Validar que tenemos contexto
        if not self.contrato_categoria_id:
            return rx.toast.error(
                "Selecciona una categoría de contrato primero"
            )

        self._limpiar_formulario()
        self.form_fecha_inicio = date.today().isoformat()
        self.form_cantidad = "1"
        self.mostrar_modal_crear_lote = True

    def cerrar_modal_crear_lote(self):
        """Cerrar modal de crear en lote y limpiar selectores"""
        self.mostrar_modal_crear_lote = False
        self._limpiar_formulario()
        # Limpiar selectores completamente
        self.contrato_seleccionado_id = ""
        self.categoria_seleccionada_id = ""
        self.contrato_categoria_id = 0
        self.contrato_id = 0
        self.contrato_codigo = ""
        self.categoria_nombre = ""
        self.categorias_contrato = []

    def abrir_modal_detalle(self, plaza: dict):
        """Abrir modal de detalles"""
        self.plaza_seleccionada = plaza
        self.mostrar_modal_detalle = True

    def cerrar_modal_detalle(self):
        """Cerrar modal de detalles"""
        self.mostrar_modal_detalle = False
        self.plaza_seleccionada = None

    def abrir_confirmar_cancelar(self, plaza: dict):
        """Abrir modal de confirmación para cancelar"""
        self.plaza_seleccionada = plaza
        self.mostrar_modal_confirmar_cancelar = True

    def cerrar_confirmar_cancelar(self):
        """Cerrar modal de confirmación"""
        self.mostrar_modal_confirmar_cancelar = False
        self.plaza_seleccionada = None

    async def abrir_asignar_empleado(self, plaza: dict):
        """Abrir modal para asignar empleado a una plaza"""
        self.plaza_seleccionada = plaza
        self.empleado_seleccionado_id = ""
        self.cargando_empleados = True
        self.mostrar_modal_asignar_empleado = True

        try:
            # Cargar empleados activos
            from app.services import empleado_service
            empleados = await empleado_service.obtener_resumen_empleados(
                incluir_inactivos=False
            )

            # Obtener IDs de empleados ya asignados a plazas ocupadas
            empleados_asignados = await plaza_service.obtener_empleados_asignados()
            empleados_asignados_set = set(empleados_asignados)

            # Filtrar solo empleados disponibles (no asignados a otra plaza)
            self.empleados_disponibles = [
                {
                    "id": e.id,
                    "clave": e.clave,
                    "nombre_completo": e.nombre_completo,
                }
                for e in empleados
                if e.id not in empleados_asignados_set
            ]
        except Exception as e:
            self.manejar_error(e, "cargar empleados")
            self.empleados_disponibles = []
            return rx.toast.error(f"Error al cargar empleados: {e}")
        finally:
            self.cargando_empleados = False

    def cerrar_modal_asignar_empleado(self):
        """Cerrar modal de asignación de empleado"""
        self.mostrar_modal_asignar_empleado = False
        self.plaza_seleccionada = None
        self.empleado_seleccionado_id = ""
        self.empleados_disponibles = []

    async def confirmar_asignar_empleado(self):
        """Confirmar y ejecutar la asignación del empleado a la plaza"""
        if not self.plaza_seleccionada or not self.empleado_seleccionado_id:
            return rx.toast.error("Seleccione un empleado")

        self.saving = True
        try:
            plaza_id = self.plaza_seleccionada["id"]
            empleado_id = int(self.empleado_seleccionado_id)

            await plaza_service.asignar_empleado(plaza_id, empleado_id)

            self.cerrar_modal_asignar_empleado()

            # Recargar plazas
            if self.contrato_categoria_id:
                await self.cargar_plazas_de_categoria(self.contrato_categoria_id)
            elif self.contrato_id:
                await self.cargar_plazas_de_contrato(self.contrato_id)

            return rx.toast.success("Empleado asignado a la plaza")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "asignar empleado")
        finally:
            self.saving = False

    async def guardar_plaza(self):
        """Guardar plaza (crear o actualizar)"""
        if not self.puede_guardar:
            return rx.toast.error("Complete los campos requeridos")

        self.saving = True
        try:
            if self.es_edicion:
                mensaje = await self._actualizar_plaza()
            else:
                mensaje = await self._crear_plaza()

            self.cerrar_modal_plaza()

            # Recargar según contexto
            if self.contrato_categoria_id:
                await self.cargar_plazas_de_categoria(self.contrato_categoria_id)
            elif self.contrato_id:
                await self.cargar_plazas_de_contrato(self.contrato_id)

            return rx.toast.success(mensaje)

        except DuplicateError as e:
            return rx.toast.error(f"Número de plaza duplicado: {e}")
        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "guardar plaza")
        finally:
            self.saving = False

    async def _crear_plaza(self) -> str:
        """Crear nueva plaza"""
        # Validar contexto
        if not self.contrato_categoria_id:
            raise BusinessRuleError("No hay categoría de contrato seleccionada")

        # Obtener el siguiente número si no está definido
        numero_plaza = int(self.form_numero_plaza) if self.form_numero_plaza else 1

        plaza_create = PlazaCreate(
            contrato_categoria_id=self.contrato_categoria_id,
            numero_plaza=numero_plaza,
            codigo=self.form_codigo.strip(),
            fecha_inicio=date.fromisoformat(self.form_fecha_inicio),
            fecha_fin=date.fromisoformat(self.form_fecha_fin) if self.form_fecha_fin else None,
            salario_mensual=self._parse_decimal(self.form_salario_mensual),
            estatus=EstatusPlaza(self.form_estatus),
            notas=self.form_notas.strip() or None,
        )

        plaza = await plaza_service.crear(plaza_create)
        return f"Plaza #{plaza.numero_plaza} creada exitosamente"

    async def _actualizar_plaza(self) -> str:
        """Actualizar plaza existente"""
        if not self.plaza_seleccionada:
            raise BusinessRuleError("No hay plaza seleccionada")

        plaza_update = PlazaUpdate(
            codigo=self.form_codigo.strip() or None,
            fecha_inicio=date.fromisoformat(self.form_fecha_inicio) if self.form_fecha_inicio else None,
            fecha_fin=date.fromisoformat(self.form_fecha_fin) if self.form_fecha_fin else None,
            salario_mensual=self._parse_decimal(self.form_salario_mensual),
            estatus=EstatusPlaza(self.form_estatus) if self.form_estatus else None,
            notas=self.form_notas.strip() or None,
        )

        await plaza_service.actualizar(
            self.plaza_seleccionada["id"],
            plaza_update
        )

        return f"Plaza #{self.plaza_seleccionada.get('numero_plaza')} actualizada"

    async def crear_plazas_lote(self):
        """Crear múltiples plazas"""
        if not self.contrato_categoria_id:
            return rx.toast.error("No hay categoría seleccionada")

        if not self.form_salario_mensual:
            return rx.toast.error("El salario es requerido")

        self.saving = True
        try:
            cantidad = int(self.form_cantidad) if self.form_cantidad else 1
            salario = self._parse_decimal(self.form_salario_mensual)
            fecha_inicio = date.fromisoformat(self.form_fecha_inicio) if self.form_fecha_inicio else date.today()
            fecha_fin = date.fromisoformat(self.form_fecha_fin) if self.form_fecha_fin else None

            plazas = await plaza_service.crear_plazas_para_categoria(
                contrato_categoria_id=self.contrato_categoria_id,
                cantidad=cantidad,
                salario_mensual=salario,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                prefijo_codigo=self.form_prefijo_codigo.strip(),
            )

            self.cerrar_modal_crear_lote()

            # Recargar datos
            await self.cargar_resumen_inicial()
            await self.cargar_contratos_con_personal()

            return rx.toast.success(f"{len(plazas)} plazas creadas exitosamente")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "crear plazas en lote")
        finally:
            self.saving = False

    async def cancelar_plaza(self):
        """Cancelar (soft delete) una plaza"""
        if not self.plaza_seleccionada:
            return

        self.saving = True
        try:
            await plaza_service.cancelar(self.plaza_seleccionada["id"])
            self.cerrar_confirmar_cancelar()

            # Recargar
            if self.contrato_categoria_id:
                await self.cargar_plazas_de_categoria(self.contrato_categoria_id)
            elif self.contrato_id:
                await self.cargar_plazas_de_contrato(self.contrato_id)

            return rx.toast.success(
                f"Plaza #{self.plaza_seleccionada.get('numero_plaza')} cancelada"
            )

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "cancelar plaza")
        finally:
            self.saving = False

    # ========================
    # OPERACIONES DE ESTADO
    # ========================
    async def asignar_empleado(self, plaza_id: int, empleado_id: int):
        """Asignar empleado a una plaza"""
        try:
            await plaza_service.asignar_empleado(plaza_id, empleado_id)

            if self.contrato_categoria_id:
                await self.cargar_plazas_de_categoria(self.contrato_categoria_id)

            return rx.toast.success("Empleado asignado a la plaza")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "asignar empleado")

    async def liberar_plaza(self, plaza_id: int):
        """Liberar una plaza ocupada"""
        try:
            await plaza_service.liberar_plaza(plaza_id)

            if self.contrato_categoria_id:
                await self.cargar_plazas_de_categoria(self.contrato_categoria_id)

            return rx.toast.success("Plaza liberada")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "liberar plaza")

    async def suspender_plaza(self, plaza_id: int):
        """Suspender una plaza"""
        try:
            await plaza_service.suspender_plaza(plaza_id)

            if self.contrato_categoria_id:
                await self.cargar_plazas_de_categoria(self.contrato_categoria_id)

            return rx.toast.success("Plaza suspendida")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "suspender plaza")

    async def reactivar_plaza(self, plaza_id: int):
        """Reactivar una plaza suspendida"""
        try:
            await plaza_service.reactivar_plaza(plaza_id)

            if self.contrato_categoria_id:
                await self.cargar_plazas_de_categoria(self.contrato_categoria_id)

            return rx.toast.success("Plaza reactivada")

        except BusinessRuleError as e:
            return rx.toast.error(str(e))
        except Exception as e:
            return self.manejar_error_con_toast(e, "reactivar plaza")

    # ========================
    # HELPERS
    # ========================
    def _limpiar_estado(self):
        """Resetea todo el estado a valores iniciales"""
        # Datos
        self.plazas = []
        self.plaza_seleccionada = None
        self.total_plazas = 0

        # Contexto
        self.contrato_id = 0
        self.contrato_codigo = ""
        self.contrato_categoria_id = 0
        self.categoria_nombre = ""

        # Resumen inicial
        self.resumen_categorias = []

        # Selectores
        self.contratos_disponibles = []
        self.categorias_contrato = []
        self.contrato_seleccionado_id = ""
        self.categoria_seleccionada_id = ""
        self.cargando_contratos = False
        self.cargando_categorias = False

        # Asignación de empleado
        self.empleados_disponibles = []
        self.empleado_seleccionado_id = ""
        self.cargando_empleados = False

        # Contadores
        self.plazas_vacantes = 0
        self.plazas_ocupadas = 0
        self.plazas_suspendidas = 0

        # Filtros
        self.filtro_estatus = "TODOS"
        self.search = ""

        # UI
        self.mostrar_modal_plaza = False
        self.mostrar_modal_detalle = False
        self.mostrar_modal_confirmar_cancelar = False
        self.mostrar_modal_crear_lote = False
        self.mostrar_modal_asignar_empleado = False

        # Formulario
        self._limpiar_formulario()

    def _limpiar_formulario(self):
        """Limpia campos del formulario"""
        self.form_numero_plaza = ""
        self.form_codigo = ""
        self.form_empleado_id = ""
        self.form_fecha_inicio = ""
        self.form_fecha_fin = ""
        self.form_salario_mensual = ""
        self.form_estatus = EstatusPlaza.VACANTE.value
        self.form_notas = ""
        self.form_cantidad = "1"
        self.form_prefijo_codigo = ""
        self._limpiar_errores()
        self.plaza_seleccionada = None
        self.es_edicion = False

    def _limpiar_errores(self):
        """Limpia todos los errores de validación"""
        self.error_numero_plaza = ""
        self.error_codigo = ""
        self.error_fecha_inicio = ""
        self.error_salario_mensual = ""
        self.error_cantidad = ""

    def _cargar_plaza_en_formulario(self, plaza: dict):
        """Carga datos de plaza en el formulario"""
        self.form_numero_plaza = str(plaza.get("numero_plaza", ""))
        self.form_codigo = plaza.get("codigo", "")
        self.form_empleado_id = str(plaza.get("empleado_id", "")) if plaza.get("empleado_id") else ""
        fecha_inicio = plaza.get("fecha_inicio")
        self.form_fecha_inicio = str(fecha_inicio) if fecha_inicio else ""
        fecha_fin = plaza.get("fecha_fin")
        self.form_fecha_fin = str(fecha_fin) if fecha_fin else ""
        self.form_salario_mensual = str(plaza.get("salario_mensual", ""))
        self.form_estatus = plaza.get("estatus", EstatusPlaza.VACANTE.value)
        self.form_notas = plaza.get("notas", "") or ""

    def _parse_decimal(self, value: str) -> Decimal:
        """Parsea string a Decimal"""
        if not value or value.strip() == "":
            return Decimal("0")
        try:
            return Decimal(value.replace(",", "").replace("$", "").strip())
        except:
            return Decimal("0")
