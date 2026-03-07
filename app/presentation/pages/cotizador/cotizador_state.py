"""
Estado principal del módulo Cotizador.

Gestiona el listado de cotizaciones y el formulario de creación.
Soporta dos tipos: PRODUCTOS_SERVICIOS y PERSONAL.
Restringido al portal para usuarios admin_empresa.
"""
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from typing import TypedDict

import reflex as rx


class FormCategoriaUI(TypedDict):
    categoria_puesto_id: int
    nombre: str
    salario: str
    min: str
    max: str
    tipo_sueldo: str
    cat_idx: int


class FormPartidaUI(TypedDict):
    notas: str
    categorias: list[FormCategoriaUI]
    items: list[dict]
    idx: int
    num: int


class FormItemUI(TypedDict):
    idx: int
    numero: int
    cantidad: str
    descripcion: str
    precio_unitario: str
    importe: str
    partida_idx: int  # -1 = global


from app.presentation.portal.state.portal_state import PortalState
from app.presentation.pages.cotizador.cotizador_validators import (
    validar_fecha_inicio,
    validar_fecha_fin,
    validar_salario_base,
    validar_cantidad,
)

PORTAL_COTIZADOR_ROUTE = "/portal/cotizador"


class CotizadorState(PortalState):
    """Estado del listado de cotizaciones."""

    # ─── Lista ────────────────────────────────────────────────────────────────
    cotizaciones: list[dict] = []

    # ─── Filtros ──────────────────────────────────────────────────────────────
    filtro_estatus: str = "__todos__"

    # ─── Selector de tipo ─────────────────────────────────────────────────────
    mostrar_selector_tipo: bool = False
    form_tipo_cotizacion: str = ""

    # ─── Modal Crear ──────────────────────────────────────────────────────────
    mostrar_modal_crear: bool = False
    form_destinatario_nombre: str = ""
    form_destinatario_cargo: str = ""
    form_notas: str = ""
    form_mostrar_desglose: bool = False

    # IVA interactivo (paso 3)
    form_aplicar_iva: bool = False

    # Personal: meses
    form_cantidad_meses: str = "1"
    error_cantidad_meses: str = ""

    # ─── Partidas inline ───────────────────────────────────────────────────────
    categorias_puesto_opciones: list[dict] = []
    form_partidas: list[FormPartidaUI] = []
    # Campos temporales para agregar categoría a una partida
    partida_editando_idx: int = -1
    form_temp_cat_puesto_id: str = ""
    form_temp_cat_salario: str = ""
    form_temp_cat_min: str = "1"
    form_temp_cat_max: str = "1"
    form_temp_cat_tipo_sueldo: str = "BRUTO"
    error_temp_cat_salario: str = ""

    # Items para PRODUCTOS_SERVICIOS (por partida)
    form_items_globales: list[dict] = []

    # ─── Wizard de creación ────────────────────────────────────────────────────
    form_paso_actual: int = 1

    # ─── Estado de UI ─────────────────────────────────────────────────────────
    loading_cotizaciones: bool = True
    saving_cotizacion: bool = False
    cotizacion_id_cambiando_estatus: int = 0

    # ─── Computed vars ────────────────────────────────────────────────────────
    @rx.var
    def es_tipo_personal(self) -> bool:
        return self.form_tipo_cotizacion == "PERSONAL"

    @rx.var
    def es_tipo_productos(self) -> bool:
        return self.form_tipo_cotizacion == "PRODUCTOS_SERVICIOS"

    # ─── Setters explícitos ───────────────────────────────────────────────────
    def _formatear_fecha_resumen(self, valor) -> str:
        """Normaliza fechas para el listado evitando render crudo en la UI."""
        if not valor:
            return "-"

        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y")

        if isinstance(valor, date):
            return valor.strftime("%d/%m/%Y")

        texto = str(valor).strip()
        if not texto:
            return "-"

        candidatos = [texto]
        if texto.endswith("Z"):
            candidatos.append(texto.replace("Z", "+00:00"))
        if "T" in texto:
            candidatos.append(texto.split("T", 1)[0])

        for candidato in candidatos:
            try:
                if len(candidato) <= 10:
                    return date.fromisoformat(candidato).strftime("%d/%m/%Y")
                return datetime.fromisoformat(candidato).strftime("%d/%m/%Y")
            except ValueError:
                continue

        return texto

    def _serializar_resumen_cotizacion(self, cotizacion) -> dict:
        """Prepara un resumen serializable y listo para render en tabla."""
        data = cotizacion.model_dump(mode='json')
        data["fecha_inicio_texto"] = self._formatear_fecha_resumen(
            data.get("fecha_inicio_periodo")
        )
        data["fecha_fin_texto"] = self._formatear_fecha_resumen(
            data.get("fecha_fin_periodo")
        )
        data["cantidad_partidas_texto"] = str(int(data.get("cantidad_partidas") or 0))
        return data

    def _periodo_default(self) -> tuple[str, str]:
        """Sugiere un período válido para evitar inputs de fecha vacíos."""
        hoy = date.today()
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy.replace(day=monthrange(hoy.year, hoy.month)[1])
        return fecha_inicio.isoformat(), fecha_fin.isoformat()

    def set_filtro_estatus(self, value: str):
        self.filtro_estatus = value

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

    def set_form_aplicar_iva(self, value: bool):
        self.form_aplicar_iva = value

    def set_form_cantidad_meses(self, value: str):
        self.form_cantidad_meses = value
        self.error_cantidad_meses = ""
        try:
            n = int(value)
            if n < 1:
                self.error_cantidad_meses = "Mínimo 1 mes"
        except (ValueError, TypeError):
            self.error_cantidad_meses = "Ingresa un número válido"

    def set_form_paso_actual(self, paso: int):
        if 1 <= paso <= 3:
            self.form_paso_actual = paso

    def ir_paso_siguiente(self):
        if self.form_paso_actual < 3:
            self.form_paso_actual += 1

    def ir_paso_anterior(self):
        if self.form_paso_actual > 1:
            self.form_paso_actual -= 1

    # ─── Selector de tipo ─────────────────────────────────────────────────────
    async def abrir_modal_crear(self):
        """Abre el selector de tipo primero."""
        self.mostrar_selector_tipo = True

    async def seleccionar_tipo_cotizacion(self, tipo: str):
        """Guarda tipo y abre wizard."""
        self.form_tipo_cotizacion = tipo
        self.mostrar_selector_tipo = False
        self.mostrar_modal_crear = True
        self.form_paso_actual = 1
        self.form_destinatario_nombre = ""
        self.form_destinatario_cargo = ""
        self.form_notas = ""
        self.form_mostrar_desglose = False
        self.form_aplicar_iva = False
        self.form_cantidad_meses = "1"
        self.error_cantidad_meses = ""
        self.form_partidas = self._reindexar_partidas(
            [{"notas": "", "categorias": [], "items": []}]
        )
        self.form_items_globales = []
        self.partida_editando_idx = -1
        self.form_temp_cat_puesto_id = ""
        self.form_temp_cat_salario = ""
        self.form_temp_cat_min = "1"
        self.form_temp_cat_max = "1"
        self.form_temp_cat_tipo_sueldo = "BRUTO"
        self.error_temp_cat_salario = ""

        if tipo == "PERSONAL":
            try:
                from app.services import categoria_puesto_service
                cats = await categoria_puesto_service.obtener_todas(
                    incluir_inactivas=False
                )
                self.categorias_puesto_opciones = [
                    {"id": c.id, "nombre": c.nombre, "clave": getattr(c, "clave", "")}
                    for c in cats
                ]
            except Exception:
                self.categorias_puesto_opciones = []

    def cerrar_modal_crear(self):
        self.mostrar_modal_crear = False

    def cerrar_selector_tipo(self):
        self.mostrar_selector_tipo = False

    # ─── Partidas inline: handlers ─────────────────────────────────────────────
    def _reindexar_partidas(self, partidas: list[dict]) -> list[dict]:
        """Inyecta idx, num y cat_idx en partidas para rx.foreach."""
        resultado = []
        for i, p in enumerate(partidas):
            cats = []
            for j, c in enumerate(p.get("categorias", [])):
                cats.append({**c, "cat_idx": j})
            items = []
            for k, item in enumerate(p.get("items", [])):
                items.append({**item, "idx": k, "numero": k + 1, "partida_idx": i})
            resultado.append({
                **p, "idx": i, "num": i + 1,
                "categorias": cats, "items": items,
            })
        return resultado

    def _reindexar_items_globales(self, items: list[dict]) -> list[dict]:
        """Reindexar items globales."""
        resultado = []
        for k, item in enumerate(items):
            resultado.append({**item, "idx": k, "numero": k + 1, "partida_idx": -1})
        return resultado

    def set_form_temp_cat_puesto_id(self, value):
        self.form_temp_cat_puesto_id = str(value) if value else ""

    def set_form_temp_cat_salario(self, value: str):
        self.form_temp_cat_salario = value

    def set_form_temp_cat_min(self, value: str):
        self.form_temp_cat_min = value

    def set_form_temp_cat_max(self, value: str):
        self.form_temp_cat_max = value

    def set_form_temp_cat_tipo_sueldo(self, value: str):
        self.form_temp_cat_tipo_sueldo = value

    def agregar_partida_form(self):
        raw = list(self.form_partidas) + [{"notas": "", "categorias": [], "items": []}]
        self.form_partidas = self._reindexar_partidas(raw)

    def eliminar_partida_form(self, idx: int):
        if len(self.form_partidas) <= 1:
            return
        nuevas = list(self.form_partidas)
        nuevas.pop(idx)
        self.form_partidas = self._reindexar_partidas(nuevas)
        if self.partida_editando_idx == idx:
            self.partida_editando_idx = -1
        elif self.partida_editando_idx > idx:
            self.partida_editando_idx -= 1

    def iniciar_agregar_categoria(self, partida_idx: int):
        self.partida_editando_idx = partida_idx
        self.form_temp_cat_puesto_id = ""
        self.form_temp_cat_salario = ""
        self.form_temp_cat_min = "1"
        self.form_temp_cat_max = "1"
        self.error_temp_cat_salario = ""

    def cancelar_agregar_categoria(self):
        self.partida_editando_idx = -1

    def confirmar_agregar_categoria(self):
        idx = self.partida_editando_idx
        if idx < 0 or idx >= len(self.form_partidas):
            return

        # Validar puesto seleccionado
        if not self.form_temp_cat_puesto_id:
            self.error_temp_cat_salario = "Selecciona una categoría de puesto"
            return

        # Validar salario
        err_salario = validar_salario_base(self.form_temp_cat_salario)
        if err_salario:
            self.error_temp_cat_salario = err_salario
            return

        # Validar cantidades
        err_min = validar_cantidad(self.form_temp_cat_min, "Cantidad mínima")
        if err_min:
            self.error_temp_cat_salario = err_min
            return
        err_max = validar_cantidad(self.form_temp_cat_max, "Cantidad máxima")
        if err_max:
            self.error_temp_cat_salario = err_max
            return

        cat_min = int(self.form_temp_cat_min)
        cat_max = int(self.form_temp_cat_max)
        if cat_max < cat_min:
            self.error_temp_cat_salario = "Máximo debe ser ≥ Mínimo"
            return

        # Buscar nombre en catálogo
        cat_puesto_id = int(self.form_temp_cat_puesto_id)
        nombre_cat = ""
        for op in self.categorias_puesto_opciones:
            if op.get("id") == cat_puesto_id:
                nombre_cat = op.get("nombre", "")
                break

        nueva_cat = {
            "categoria_puesto_id": cat_puesto_id,
            "nombre": nombre_cat,
            "salario": self.form_temp_cat_salario,
            "min": str(cat_min),
            "max": str(cat_max),
            "tipo_sueldo": self.form_temp_cat_tipo_sueldo,
        }

        nuevas_partidas = []
        for i, p in enumerate(self.form_partidas):
            if i == idx:
                cats_actualizadas = list(p.get("categorias", [])) + [nueva_cat]
                nuevas_partidas.append(
                    {**p, "categorias": cats_actualizadas}
                )
            else:
                nuevas_partidas.append(p)
        self.form_partidas = self._reindexar_partidas(nuevas_partidas)

        self.error_temp_cat_salario = ""
        self.partida_editando_idx = -1

    def eliminar_categoria_form(self, partida_idx: int, cat_idx: int):
        nuevas_partidas = []
        for i, p in enumerate(self.form_partidas):
            if i == partida_idx:
                cats = list(p.get("categorias", []))
                if 0 <= cat_idx < len(cats):
                    cats.pop(cat_idx)
                nuevas_partidas.append({**p, "categorias": cats})
            else:
                nuevas_partidas.append(p)
        self.form_partidas = self._reindexar_partidas(nuevas_partidas)

    # ─── Items handlers (PRODUCTOS_SERVICIOS) ─────────────────────────────────
    def _calcular_importe(self, cantidad: str, precio: str) -> str:
        """Calcula importe = cantidad × precio."""
        try:
            c = Decimal(cantidad.replace(",", "") or "0")
            p = Decimal(precio.replace(",", "") or "0")
            return str(round(float(c * p), 2))
        except Exception:
            return "0"

    def agregar_item_partida(self, partida_idx: int):
        """Agrega un item vacío a una partida."""
        nuevas = list(self.form_partidas)
        if 0 <= partida_idx < len(nuevas):
            items = list(nuevas[partida_idx].get("items", []))
            items.append({
                "cantidad": "1",
                "descripcion": "",
                "precio_unitario": "0",
                "importe": "0",
            })
            nuevas[partida_idx] = {**nuevas[partida_idx], "items": items}
            self.form_partidas = self._reindexar_partidas(nuevas)

    def eliminar_item_partida(self, partida_idx: int, item_idx: int):
        """Elimina un item de una partida y renumera."""
        nuevas = list(self.form_partidas)
        if 0 <= partida_idx < len(nuevas):
            items = list(nuevas[partida_idx].get("items", []))
            if 0 <= item_idx < len(items):
                items.pop(item_idx)
            nuevas[partida_idx] = {**nuevas[partida_idx], "items": items}
            self.form_partidas = self._reindexar_partidas(nuevas)

    def actualizar_item_campo(self, partida_idx: int, item_idx: int, campo: str, valor: str):
        """Actualiza campo de un item y recalcula importe."""
        nuevas = list(self.form_partidas)
        if 0 <= partida_idx < len(nuevas):
            items = list(nuevas[partida_idx].get("items", []))
            if 0 <= item_idx < len(items):
                item = dict(items[item_idx])
                item[campo] = valor
                item["importe"] = self._calcular_importe(
                    item.get("cantidad", "1"),
                    item.get("precio_unitario", "0"),
                )
                items[item_idx] = item
            nuevas[partida_idx] = {**nuevas[partida_idx], "items": items}
            self.form_partidas = self._reindexar_partidas(nuevas)

    # Items globales (paso 3)
    def agregar_item_global(self):
        items = list(self.form_items_globales)
        items.append({
            "cantidad": "1",
            "descripcion": "",
            "precio_unitario": "0",
            "importe": "0",
        })
        self.form_items_globales = self._reindexar_items_globales(items)

    def eliminar_item_global(self, item_idx: int):
        items = list(self.form_items_globales)
        if 0 <= item_idx < len(items):
            items.pop(item_idx)
        self.form_items_globales = self._reindexar_items_globales(items)

    def actualizar_item_global_campo(self, item_idx: int, campo: str, valor: str):
        items = list(self.form_items_globales)
        if 0 <= item_idx < len(items):
            item = dict(items[item_idx])
            item[campo] = valor
            item["importe"] = self._calcular_importe(
                item.get("cantidad", "1"),
                item.get("precio_unitario", "0"),
            )
            items[item_idx] = item
        self.form_items_globales = self._reindexar_items_globales(items)

    # ─── Handlers principales ─────────────────────────────────────────────────
    async def on_mount_cotizador(self):
        """Valida acceso y carga cotizaciones de la empresa activa.

        Admins del sistema acceden directamente.
        Usuarios portal pasan por on_mount_portal para verificar empresa.
        """
        resultado_auth = await self.verificar_y_redirigir()
        if resultado_auth:
            self.loading_cotizaciones = False
            yield resultado_auth
            return

        if not self.es_admin:
            if not self.es_empleado_portal and not self.id_empresa_actual:
                self.loading_cotizaciones = False
                yield rx.toast.error(
                    "No tienes una empresa asignada.",
                    position="top-center",
                )
                return

            if not self.es_admin_empresa:
                self.loading_cotizaciones = False
                yield rx.redirect("/portal")
                return

        try:
            await self._fetch_cotizaciones()
        finally:
            self.loading_cotizaciones = False
        yield

    async def _fetch_cotizaciones(self):
        """Obtiene cotizaciones de la empresa activa sin manejar loading."""
        empresa_id = self.id_empresa_actual
        if not empresa_id:
            self.cotizaciones = []
            return

        try:
            from app.services import cotizacion_service

            cotizaciones = await cotizacion_service.obtener_por_empresa(empresa_id)
            self.cotizaciones = [
                self._serializar_resumen_cotizacion(c)
                for c in cotizaciones
            ]
        except Exception as e:
            self.cotizaciones = []
            self.manejar_error(e, "cargar cotizaciones")

    async def cargar_cotizaciones(self):
        """Recarga cotizaciones mostrando spinner del listado."""
        self.loading_cotizaciones = True
        yield
        try:
            await self._fetch_cotizaciones()
        finally:
            self.loading_cotizaciones = False

    async def crear_cotizacion(self):
        """Crea una nueva cotización con partidas, categorías/items inline."""
        if not self.form_partidas:
            yield rx.toast.error("Agrega al menos una partida")
            return

        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede crear cotizaciones")
            return

        empresa_id = self.id_empresa_actual
        if not empresa_id:
            self.mostrar_mensaje("No hay empresa seleccionada", "error")
            return

        self.saving_cotizacion = True
        yield

        try:
            from app.services import cotizacion_service
            from app.entities import CotizacionCreate
            from app.entities.cotizacion_partida_categoria import (
                CotizacionPartidaCategoriaCreate,
            )
            from app.entities.cotizacion_item import CotizacionItemCreate

            cantidad_meses = 1
            try:
                cantidad_meses = max(1, int(self.form_cantidad_meses))
            except (ValueError, TypeError):
                pass

            datos = CotizacionCreate(
                empresa_id=empresa_id,
                tipo=self.form_tipo_cotizacion,
                aplicar_iva=self.form_aplicar_iva,
                cantidad_meses=cantidad_meses,
                destinatario_nombre=self.form_destinatario_nombre or None,
                destinatario_cargo=self.form_destinatario_cargo or None,
                notas=self.form_notas or None,
                mostrar_desglose=self.form_mostrar_desglose,
            )
            cotizacion = await cotizacion_service.crear(
                datos,
                user_id=self.usuario_actual.get('id'),
                empresa_permitida_id=empresa_id,
            )

            partidas_db = await cotizacion_service.obtener_partidas(
                cotizacion.id, empresa_id=empresa_id
            )

            for form_idx, form_partida in enumerate(self.form_partidas):
                if form_idx == 0:
                    partida_id = partidas_db[0].id
                else:
                    nueva_partida = await cotizacion_service.agregar_partida(
                        cotizacion.id, empresa_id=empresa_id
                    )
                    partida_id = nueva_partida.id

                if self.form_tipo_cotizacion == "PERSONAL":
                    # Crear categorías (perfiles)
                    categorias = form_partida.get("categorias", [])
                    for cat in categorias:
                        cat_create = CotizacionPartidaCategoriaCreate(
                            partida_id=partida_id,
                            categoria_puesto_id=int(cat["categoria_puesto_id"]),
                            salario_base_mensual=Decimal(
                                cat["salario"].replace(",", "")
                            ),
                            cantidad_minima=int(cat["min"]),
                            cantidad_maxima=int(cat["max"]),
                            tipo_sueldo=cat.get("tipo_sueldo", "BRUTO"),
                        )
                        await cotizacion_service.agregar_categoria(
                            cat_create, empresa_id=empresa_id
                        )

                    if categorias:
                        try:
                            await cotizacion_service.calcular_costo_patronal(
                                partida_id, empresa_id=empresa_id
                            )
                        except Exception:
                            pass
                else:
                    # PRODUCTOS_SERVICIOS: crear items por partida
                    items = form_partida.get("items", [])
                    for item in items:
                        if not item.get("descripcion", "").strip():
                            continue
                        item_create = CotizacionItemCreate(
                            cotizacion_id=cotizacion.id,
                            partida_id=partida_id,
                            cantidad=Decimal(str(item.get("cantidad", "1") or "1")),
                            descripcion=item["descripcion"],
                            precio_unitario=Decimal(str(item.get("precio_unitario", "0") or "0")),
                        )
                        await cotizacion_service.agregar_item(
                            item_create, empresa_id=empresa_id
                        )

            # Items globales
            for item in self.form_items_globales:
                if not item.get("descripcion", "").strip():
                    continue
                item_create = CotizacionItemCreate(
                    cotizacion_id=cotizacion.id,
                    cantidad=Decimal(str(item.get("cantidad", "1") or "1")),
                    descripcion=item["descripcion"],
                    precio_unitario=Decimal(str(item.get("precio_unitario", "0") or "0")),
                )
                await cotizacion_service.agregar_item(
                    item_create, empresa_id=empresa_id
                )

            self.cerrar_modal_crear()
            self.mostrar_mensaje(f"Cotización {cotizacion.codigo} creada", "success")
            await self._fetch_cotizaciones()
            yield rx.redirect(f"{PORTAL_COTIZADOR_ROUTE}/{cotizacion.codigo}")

        except Exception as e:
            self.manejar_error(e, "crear cotización")
        finally:
            self.saving_cotizacion = False

    async def cambiar_estatus(self, cotizacion_id: int, nuevo_estatus: str):
        """Cambia el estatus de una cotización."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede actualizar cotizaciones")
            return

        self.cotizacion_id_cambiando_estatus = cotizacion_id
        yield

        try:
            from app.services import cotizacion_service
            from app.core.enums import EstatusCotizacion
            estatus_enum = EstatusCotizacion(nuevo_estatus)
            await cotizacion_service.cambiar_estatus(
                cotizacion_id,
                estatus_enum,
                empresa_id=self.id_empresa_actual,
            )
            self.mostrar_mensaje(f"Estatus actualizado a {nuevo_estatus}", "success")
            await self._fetch_cotizaciones()
        except Exception as e:
            self.manejar_error(e, "cambiar estatus")
        finally:
            self.cotizacion_id_cambiando_estatus = 0

    async def crear_nueva_version(self, cotizacion_id: int):
        """Crea una nueva versión de una cotización."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede versionar cotizaciones")
            return

        self.loading = True
        yield

        try:
            from app.services import cotizacion_service
            nueva = await cotizacion_service.crear_version(
                cotizacion_id,
                empresa_id=self.id_empresa_actual,
            )
            self.mostrar_mensaje(f"Nueva versión creada: {nueva.codigo}", "success")
            await self._fetch_cotizaciones()
            yield rx.redirect(f"{PORTAL_COTIZADOR_ROUTE}/{nueva.codigo}")
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

    # ─── Computed vars (listado) ──────────────────────────────────────────────
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

    # ─── Computed vars (resumen wizard) ────────────────────────────────────────
    @rx.var
    def resumen_subtotal(self) -> str:
        """Subtotal calculado en tiempo real para PRODUCTOS_SERVICIOS."""
        total = 0.0
        for p in self.form_partidas:
            for item in p.get("items", []):
                try:
                    total += float(item.get("importe", 0) or 0)
                except (ValueError, TypeError):
                    pass
        for item in self.form_items_globales:
            try:
                total += float(item.get("importe", 0) or 0)
            except (ValueError, TypeError):
                pass
        return f"${total:,.2f}"

    @rx.var
    def resumen_iva(self) -> str:
        """IVA 16% del subtotal si aplicar_iva."""
        if not self.form_aplicar_iva:
            return "$0.00"
        total = 0.0
        for p in self.form_partidas:
            for item in p.get("items", []):
                try:
                    total += float(item.get("importe", 0) or 0)
                except (ValueError, TypeError):
                    pass
        for item in self.form_items_globales:
            try:
                total += float(item.get("importe", 0) or 0)
            except (ValueError, TypeError):
                pass
        return f"${total * 0.16:,.2f}"

    @rx.var
    def resumen_total(self) -> str:
        """Total = subtotal + IVA."""
        total = 0.0
        for p in self.form_partidas:
            for item in p.get("items", []):
                try:
                    total += float(item.get("importe", 0) or 0)
                except (ValueError, TypeError):
                    pass
        for item in self.form_items_globales:
            try:
                total += float(item.get("importe", 0) or 0)
            except (ValueError, TypeError):
                pass
        if self.form_aplicar_iva:
            total *= 1.16
        return f"${total:,.2f}"
