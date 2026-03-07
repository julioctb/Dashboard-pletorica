"""
Estado del detalle de una cotización (partidas + matriz de costos).
"""
import asyncio
import base64
from datetime import date, datetime
from typing import TypedDict

import reflex as rx

from app.presentation.portal.state.portal_state import PortalState
from app.presentation.pages.cotizador.cotizador_validators import (
    validar_fecha_inicio,
    validar_fecha_fin,
    validar_salario_base,
    validar_cantidad,
    validar_nombre_concepto,
    validar_precio_unitario,
    validar_cantidad_meses,
)

PORTAL_COTIZADOR_ROUTE = "/portal/cotizador"


class MatrizColumnaUI(TypedDict):
    id: int
    categoria_nombre: str
    cantidad_rango_texto: str
    precio_unitario_texto: str


class MatrizCeldaUI(TypedDict):
    partida_categoria_id: int
    editable: bool
    valor_input: str
    valor_calculado_texto: str
    valor_mostrado_texto: str


class MatrizFilaUI(TypedDict):
    id: int
    nombre: str
    tipo_concepto: str
    tipo_valor: str
    tipo_valor_texto: str
    es_autogenerado: bool
    celdas: list[MatrizCeldaUI]


def _formatear_fecha(valor) -> str:
    """Normaliza fechas de Supabase/Pydantic a formato legible estable."""
    if not valor:
        return ""

    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y")

    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")

    texto = str(valor).strip()
    if not texto:
        return ""

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


class CotizadorDetalleState(PortalState):
    """Estado del detalle de cotización: partidas, categorías y matriz."""

    # ─── Datos principales ────────────────────────────────────────────────────
    cotizacion: dict = {}
    partidas: list[dict] = []
    partida_seleccionada_id: int = 0
    categorias_partida: list[dict] = []
    conceptos_partida: list[dict] = []
    columnas_matriz: list[MatrizColumnaUI] = []
    matriz_costos: list[MatrizFilaUI] = []
    totales_partida: dict = {}
    totales_cotizacion: dict = {}

    # ─── Formulario categoría ─────────────────────────────────────────────────
    mostrar_modal_categoria: bool = False
    form_cat_categoria_puesto_id: int = 0
    form_cat_salario_base: str = ""
    form_cat_cantidad_min: str = "0"
    form_cat_cantidad_max: str = "0"
    error_cat_salario: str = ""
    error_cat_cantidad_min: str = ""
    error_cat_cantidad_max: str = ""

    # ─── Formulario concepto ──────────────────────────────────────────────────
    mostrar_modal_concepto: bool = False
    form_concepto_nombre: str = ""
    form_concepto_tipo_valor: str = "FIJO"
    error_concepto_nombre: str = ""

    # ─── Formulario edición partida ───────────────────────────────────────────
    mostrar_modal_editar_partida: bool = False
    form_partida_notas: str = ""

    # ─── Formulario edición cotización ────────────────────────────────────────
    mostrar_modal_editar_cotizacion: bool = False
    form_edit_fecha_inicio: str = ""
    form_edit_fecha_fin: str = ""
    form_edit_destinatario_nombre: str = ""
    form_edit_destinatario_cargo: str = ""
    form_edit_notas: str = ""
    form_edit_mostrar_desglose: bool = False
    error_edit_fecha_inicio: str = ""
    error_edit_fecha_fin: str = ""

    # ─── Modal edición costo patronal ─────────────────────────────────────────
    mostrar_modal_costo_patronal: bool = False
    cat_editando_id: int = 0
    form_costo_patronal_manual: str = ""
    ultimo_resultado_calculo: dict = {}

    # ─── Items (PRODUCTOS_SERVICIOS y extras) ──────────────────────────────────
    items_partida: list[dict] = []
    items_globales: list[dict] = []

    # ─── Formulario item ────────────────────────────────────────────────────────
    mostrar_modal_item: bool = False
    form_item_descripcion: str = ""
    form_item_cantidad: str = "1"
    form_item_precio_unitario: str = ""
    form_item_partida_id: int = 0
    form_item_es_global: bool = False
    error_item_descripcion: str = ""
    error_item_cantidad: str = ""
    error_item_precio: str = ""

    # ─── Estado de UI ─────────────────────────────────────────────────────────
    loading_detalle: bool = True
    calculando_patronal: bool = False
    categorias_puesto_catalogo: list[dict] = []

    # ─── Setters explícitos ───────────────────────────────────────────────────
    def set_partida_seleccionada_id(self, value: int):
        self.partida_seleccionada_id = value

    def set_form_cat_categoria_puesto_id(self, value: str):
        try:
            self.form_cat_categoria_puesto_id = int(value)
        except (ValueError, TypeError):
            self.form_cat_categoria_puesto_id = 0

    def set_form_cat_salario_base(self, value: str):
        self.form_cat_salario_base = value

    def set_form_cat_cantidad_min(self, value: str):
        self.form_cat_cantidad_min = value

    def set_form_cat_cantidad_max(self, value: str):
        self.form_cat_cantidad_max = value

    def set_form_concepto_nombre(self, value: str):
        self.form_concepto_nombre = value

    def set_form_concepto_tipo_valor(self, value: str):
        self.form_concepto_tipo_valor = value

    def set_form_partida_notas(self, value: str):
        self.form_partida_notas = value

    def set_form_edit_fecha_inicio(self, value: str):
        self.form_edit_fecha_inicio = value

    def set_form_edit_fecha_fin(self, value: str):
        self.form_edit_fecha_fin = value

    def set_form_edit_destinatario_nombre(self, value: str):
        self.form_edit_destinatario_nombre = value

    def set_form_edit_destinatario_cargo(self, value: str):
        self.form_edit_destinatario_cargo = value

    def set_form_edit_notas(self, value: str):
        self.form_edit_notas = value

    def set_form_edit_mostrar_desglose(self, value: bool):
        self.form_edit_mostrar_desglose = value

    def set_form_costo_patronal_manual(self, value: str):
        self.form_costo_patronal_manual = value

    def set_mostrar_modal_categoria(self, value: bool):
        self.mostrar_modal_categoria = value

    def set_mostrar_modal_concepto(self, value: bool):
        self.mostrar_modal_concepto = value

    def set_mostrar_modal_editar_partida(self, value: bool):
        self.mostrar_modal_editar_partida = value

    def set_mostrar_modal_editar_cotizacion(self, value: bool):
        self.mostrar_modal_editar_cotizacion = value

    def set_mostrar_modal_costo_patronal(self, value: bool):
        self.mostrar_modal_costo_patronal = value

    def set_mostrar_modal_item(self, value: bool):
        self.mostrar_modal_item = value

    def set_form_item_descripcion(self, value: str):
        self.form_item_descripcion = value

    def set_form_item_cantidad(self, value: str):
        self.form_item_cantidad = value

    def set_form_item_precio_unitario(self, value: str):
        self.form_item_precio_unitario = value

    def abrir_modal_item(self, partida_id: int = 0, es_global: bool = False):
        self.form_item_descripcion = ""
        self.form_item_cantidad = "1"
        self.form_item_precio_unitario = ""
        self.form_item_partida_id = partida_id
        self.form_item_es_global = es_global
        self.error_item_descripcion = ""
        self.error_item_cantidad = ""
        self.error_item_precio = ""
        self.mostrar_modal_item = True

    def abrir_modal_item_partida(self):
        self.abrir_modal_item(
            partida_id=self.partida_seleccionada_id,
            es_global=False,
        )

    def abrir_modal_item_global(self):
        self.abrir_modal_item(partida_id=0, es_global=True)

    def cerrar_modal_item(self):
        self.mostrar_modal_item = False

    def abrir_modal_categoria(self):
        self.mostrar_modal_categoria = True
        self.form_cat_categoria_puesto_id = 0
        self.form_cat_salario_base = ""
        self.form_cat_cantidad_min = "0"
        self.form_cat_cantidad_max = "0"
        self.error_cat_salario = ""
        self.error_cat_cantidad_min = ""
        self.error_cat_cantidad_max = ""

    def cerrar_modal_categoria(self):
        self.mostrar_modal_categoria = False

    def abrir_modal_concepto(self):
        self.mostrar_modal_concepto = True
        self.form_concepto_nombre = ""
        self.form_concepto_tipo_valor = "FIJO"
        self.error_concepto_nombre = ""

    def cerrar_modal_concepto(self):
        self.mostrar_modal_concepto = False

    def abrir_modal_editar_partida(self):
        self.form_partida_notas = self.partida_activa.get('notas', '') or ''
        self.mostrar_modal_editar_partida = True

    def cerrar_modal_editar_partida(self):
        self.mostrar_modal_editar_partida = False

    # ─── Formulario edición cotización: campos nuevos ──────────────────────────
    form_edit_aplicar_iva: bool = False
    form_edit_cantidad_meses: str = "1"

    def set_form_edit_aplicar_iva(self, value: bool):
        self.form_edit_aplicar_iva = value

    def set_form_edit_cantidad_meses(self, value: str):
        self.form_edit_cantidad_meses = value

    def abrir_modal_editar_cotizacion(self):
        self.form_edit_fecha_inicio = self.cotizacion.get('fecha_inicio_periodo', '') or ''
        self.form_edit_fecha_fin = self.cotizacion.get('fecha_fin_periodo', '') or ''
        self.form_edit_destinatario_nombre = self.cotizacion.get('destinatario_nombre', '') or ''
        self.form_edit_destinatario_cargo = self.cotizacion.get('destinatario_cargo', '') or ''
        self.form_edit_notas = self.cotizacion.get('notas', '') or ''
        self.form_edit_mostrar_desglose = bool(self.cotizacion.get('mostrar_desglose', False))
        self.form_edit_aplicar_iva = bool(self.cotizacion.get('aplicar_iva', False))
        self.form_edit_cantidad_meses = str(self.cotizacion.get('cantidad_meses', 1))
        self.error_edit_fecha_inicio = ""
        self.error_edit_fecha_fin = ""
        self.mostrar_modal_editar_cotizacion = True

    def cerrar_modal_editar_cotizacion(self):
        self.mostrar_modal_editar_cotizacion = False

    def validar_edit_fecha_inicio_campo(self):
        error = validar_fecha_inicio(self.form_edit_fecha_inicio)
        self.error_edit_fecha_inicio = error or ""

    def validar_edit_fecha_fin_campo(self):
        error = validar_fecha_fin(self.form_edit_fecha_fin, self.form_edit_fecha_inicio)
        self.error_edit_fecha_fin = error or ""

    def abrir_modal_costo_patronal(self, cat_id: int, costo_actual: str):
        self.cat_editando_id = cat_id
        self.form_costo_patronal_manual = costo_actual
        self.mostrar_modal_costo_patronal = True

    def cerrar_modal_costo_patronal(self):
        self.mostrar_modal_costo_patronal = False

    # ─── Handlers principales ─────────────────────────────────────────────────
    async def cargar_detalle(self):
        """Carga el detalle completo de la cotización.

        Reflex inyecta self.cotizacion_id automáticamente desde la ruta
        /portal/cotizador/[cotizacion_id].
        """
        self.loading_detalle = True

        try:
            from app.services import cotizacion_service, categoria_puesto_service

            codigo = self.cotizacion_id or ""
            if not codigo:
                self.loading_detalle = False
                return

            cotizacion, cats = await asyncio.gather(
                cotizacion_service.obtener_por_codigo(
                    codigo,
                    empresa_id=self.id_empresa_actual,
                ),
                categoria_puesto_service.obtener_todas(),
            )
            partidas = await cotizacion_service.obtener_partidas(
                cotizacion.id,
                empresa_id=self.id_empresa_actual,
            )
            partidas_serializadas = [self._serializar_partida_resumen(p) for p in partidas]
            partida_seleccionada_id = (
                partidas_serializadas[0]['id'] if partidas_serializadas else 0
            )

            snapshot = None
            if partida_seleccionada_id:
                snapshot = await self._obtener_snapshot_partida(
                    partida_seleccionada_id,
                    partidas_precargadas=partidas_serializadas,
                    cotizacion_id=cotizacion.id,
                )

            self.cotizacion = cotizacion.model_dump(mode='json')
            self.partidas = partidas_serializadas
            self.partida_seleccionada_id = partida_seleccionada_id
            self.categorias_puesto_catalogo = [
                {'id': c.id, 'nombre': c.nombre, 'clave': c.clave}
                for c in cats
            ]
            if snapshot:
                self.categorias_partida = snapshot['categorias_partida']
                self.conceptos_partida = snapshot['conceptos_partida']
                self.columnas_matriz = snapshot['columnas_matriz']
                self.matriz_costos = snapshot['matriz_costos']
                self.totales_partida = snapshot['totales_partida']
                self.items_partida = snapshot.get('items_partida', [])
            else:
                self.categorias_partida = []
                self.conceptos_partida = []
                self.columnas_matriz = []
                self.matriz_costos = []
                self.totales_partida = {}
                self.items_partida = []

            # Cargar items globales
            items_globales_raw = await cotizacion_service.obtener_items(
                cotizacion.id,
                empresa_id=self.id_empresa_actual,
            )
            self.items_globales = [
                self._serializar_item(it) for it in items_globales_raw
            ]

            # Totales a nivel cotización (todas las partidas + globales + IVA)
            await self._recargar_totales_cotizacion()

        except Exception as e:
            import logging as _lg
            _lg.getLogger("cotizador.detalle").error(
                "ERROR cargar_detalle: %s", e, exc_info=True,
            )
            self.manejar_error(e, "cargar cotización")
        finally:
            self.loading_detalle = False

    async def guardar_info_cotizacion(self):
        """Actualiza los datos generales de la cotización actual."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede editar cotizaciones")
            return

        cotizacion_id = self.cotizacion.get('id')
        if not cotizacion_id:
            return

        # Validar fechas solo si se proporcionan
        if self.form_edit_fecha_inicio or self.form_edit_fecha_fin:
            err_ini = validar_fecha_inicio(self.form_edit_fecha_inicio) if self.form_edit_fecha_inicio else None
            err_fin = validar_fecha_fin(self.form_edit_fecha_fin, self.form_edit_fecha_inicio) if self.form_edit_fecha_fin else None
            self.error_edit_fecha_inicio = err_ini or ""
            self.error_edit_fecha_fin = err_fin or ""
            if err_ini or err_fin:
                return
        else:
            self.error_edit_fecha_inicio = ""
            self.error_edit_fecha_fin = ""

        self.saving = True
        yield

        try:
            from datetime import date as date_cls
            from app.entities import CotizacionUpdate
            from app.services import cotizacion_service

            update_data = {
                'destinatario_nombre': self.form_edit_destinatario_nombre or None,
                'destinatario_cargo': self.form_edit_destinatario_cargo or None,
                'mostrar_desglose': self.form_edit_mostrar_desglose,
                'notas': self.form_edit_notas or None,
                'aplicar_iva': self.form_edit_aplicar_iva,
            }
            if self.form_edit_fecha_inicio:
                update_data['fecha_inicio_periodo'] = date_cls.fromisoformat(self.form_edit_fecha_inicio)
            if self.form_edit_fecha_fin:
                update_data['fecha_fin_periodo'] = date_cls.fromisoformat(self.form_edit_fecha_fin)
            # Meses solo para PERSONAL
            if self.cotizacion.get('tipo') == 'PERSONAL' and self.form_edit_cantidad_meses:
                try:
                    update_data['cantidad_meses'] = int(self.form_edit_cantidad_meses)
                except ValueError:
                    pass

            actualizada = await cotizacion_service.actualizar(
                int(cotizacion_id),
                CotizacionUpdate(**update_data),
                empresa_id=self.id_empresa_actual,
            )
            self.cotizacion = actualizada.model_dump(mode='json')
            self.cerrar_modal_editar_cotizacion()

            if self.partida_seleccionada_id:
                await self._cargar_partida(
                    self.partida_seleccionada_id,
                    refrescar_partidas=True,
                )
            await self._recargar_totales_cotizacion()

            self.mostrar_mensaje("Información de la cotización actualizada", "success")
        except Exception as e:
            self.manejar_error(e, "actualizar información de cotización")
        finally:
            self.saving = False

    async def cambiar_estatus_cotizacion(self, nuevo_estatus: str):
        """Actualiza el estatus global de la cotización actual."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede actualizar cotizaciones")
            return

        cotizacion_id = self.cotizacion.get('id')
        if not cotizacion_id:
            return

        self.loading = True
        yield

        try:
            from app.services import cotizacion_service
            from app.core.enums import EstatusCotizacion

            actualizada = await cotizacion_service.cambiar_estatus(
                cotizacion_id,
                EstatusCotizacion(nuevo_estatus),
                empresa_id=self.id_empresa_actual,
            )
            self.cotizacion = actualizada.model_dump(mode='json')
            self.mostrar_mensaje(
                f"Cotización actualizada a {nuevo_estatus}",
                "success",
            )
        except Exception as e:
            self.manejar_error(e, "actualizar estatus de cotización")
        finally:
            self.loading = False

    async def descargar_pdf(self):
        """Genera y descarga el PDF de la cotización actual."""
        cotizacion_id = self.cotizacion.get('id')
        if not cotizacion_id:
            return

        if not self.cantidad_partidas:
            yield rx.toast.error("La cotización no tiene partidas para generar PDF")
            return

        if not self.puede_descargar_pdf:
            yield rx.toast.error(
                "El PDF solo se habilita cuando la cotización está PREPARADA o en un estado posterior"
            )
            return

        self.loading = True
        yield

        try:
            from app.services import cotizacion_pdf_service

            pdf_bytes = await cotizacion_pdf_service.generar_pdf(int(cotizacion_id))
            pdf_b64 = base64.b64encode(pdf_bytes).decode()
            filename = f"{self.cotizacion.get('codigo', f'cotizacion-{cotizacion_id}')}.pdf"
            data_url = f"data:application/pdf;base64,{pdf_b64}"
            yield rx.download(url=data_url, filename=filename)
        except ImportError:
            yield rx.toast.warning(
                "Para generar PDF instala reportlab: poetry add reportlab num2words"
            )
        except Exception as e:
            self.manejar_error(e, "generar PDF")
        finally:
            self.loading = False

    async def seleccionar_partida(self, partida_id: int):
        """Selecciona una partida y carga su contenido."""
        if partida_id == self.partida_seleccionada_id:
            return
        self.partida_seleccionada_id = partida_id
        await self._cargar_partida(partida_id)

    async def _obtener_snapshot_partida(
        self,
        partida_id: int,
        partidas_precargadas: list[dict] | None = None,
        refrescar_partidas: bool = False,
        cotizacion_id: int | None = None,
    ) -> dict:
        """Obtiene todo el estado derivado de una partida en una sola carga."""
        from app.services import cotizacion_service

        cot_id = cotizacion_id or self.cotizacion.get('id', 0)

        tareas = [
            cotizacion_service.obtener_categorias_partida(
                partida_id,
                empresa_id=self.id_empresa_actual,
            ),
            cotizacion_service.obtener_conceptos_partida(
                partida_id,
                empresa_id=self.id_empresa_actual,
            ),
            cotizacion_service.obtener_valores_partida(
                partida_id,
                empresa_id=self.id_empresa_actual,
            ),
            cotizacion_service.recalcular_totales_partida(
                partida_id,
                empresa_id=self.id_empresa_actual,
            ),
        ]
        if refrescar_partidas:
            tareas.append(
                cotizacion_service.obtener_partidas(
                    cot_id,
                    empresa_id=self.id_empresa_actual,
                )
            )
        # Load items for this partida
        tareas.append(
            cotizacion_service.obtener_items(
                cot_id,
                partida_id=partida_id,
                empresa_id=self.id_empresa_actual,
            )
        )

        resultados = await asyncio.gather(*tareas)
        categorias = resultados[0]
        conceptos = resultados[1]
        valores = resultados[2]
        totales = resultados[3]
        partidas = partidas_precargadas
        idx = 4
        if refrescar_partidas:
            partidas = [self._serializar_partida_resumen(p) for p in resultados[idx]]
            idx += 1
        items_raw = resultados[idx]

        categorias_partida = [c.model_dump(mode='json') for c in categorias]
        conceptos_partida = [c.model_dump(mode='json') for c in conceptos]
        columnas_matriz = self._serializar_columnas_matriz(categorias_partida)
        matriz_costos = self._serializar_matriz_costos(
            conceptos_partida,
            categorias_partida,
            valores,
        )
        return {
            'categorias_partida': categorias_partida,
            'conceptos_partida': conceptos_partida,
            'columnas_matriz': columnas_matriz,
            'matriz_costos': matriz_costos,
            'totales_partida': totales,
            'partidas': partidas,
            'items_partida': [self._serializar_item(it) for it in items_raw],
        }

    async def _cargar_partida(self, partida_id: int, refrescar_partidas: bool = False):
        """Carga categorías y conceptos de la partida seleccionada."""
        try:
            snapshot = await self._obtener_snapshot_partida(
                partida_id,
                refrescar_partidas=refrescar_partidas,
            )
            self.categorias_partida = snapshot['categorias_partida']
            self.conceptos_partida = snapshot['conceptos_partida']
            self.columnas_matriz = snapshot['columnas_matriz']
            self.matriz_costos = snapshot['matriz_costos']
            self.totales_partida = snapshot['totales_partida']
            self.items_partida = snapshot.get('items_partida', [])
            if snapshot.get('partidas') is not None:
                self.partidas = snapshot['partidas']

        except Exception as e:
            self.manejar_error(e, "cargar partida")

    async def _recargar_totales_cotizacion(self):
        """Recarga totales a nivel cotización (todas las partidas + items globales + IVA)."""
        cotizacion_id = self.cotizacion.get('id')
        if not cotizacion_id:
            return
        try:
            from app.services import cotizacion_service
            self.totales_cotizacion = await cotizacion_service.recalcular_totales_cotizacion(
                int(cotizacion_id),
                empresa_id=self.id_empresa_actual,
            )
        except Exception:
            pass

    async def agregar_partida(self):
        """Agrega una nueva partida a la cotización."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede editar cotizaciones")
            return

        cotizacion_id = self.cotizacion.get('id')
        if not cotizacion_id:
            return

        self.loading = True
        yield

        try:
            from app.services import cotizacion_service
            partida = await cotizacion_service.agregar_partida(
                cotizacion_id,
                empresa_id=self.id_empresa_actual,
            )

            self.partida_seleccionada_id = partida.id
            await self._cargar_partida(partida.id, refrescar_partidas=True)
            await self._recargar_totales_cotizacion()
            self.mostrar_mensaje(f"Partida {partida.numero_partida} agregada", "success")

        except Exception as e:
            self.manejar_error(e, "agregar partida")
        finally:
            self.loading = False

    async def guardar_info_partida(self):
        """Actualiza la información editable de la partida activa."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede editar cotizaciones")
            return

        if not self.partida_seleccionada_id:
            return

        self.saving = True
        yield

        try:
            from app.services import cotizacion_service

            await cotizacion_service.actualizar_partida(
                self.partida_seleccionada_id,
                {"notas": self.form_partida_notas or None},
                empresa_id=self.id_empresa_actual,
            )
            self.cerrar_modal_editar_partida()
            await self._cargar_partida(self.partida_seleccionada_id, refrescar_partidas=True)
            self.mostrar_mensaje("Información de la partida actualizada", "success")
        except Exception as e:
            self.manejar_error(e, "actualizar información de partida")
        finally:
            self.saving = False

    async def agregar_categoria(self):
        """Agrega una categoría a la partida seleccionada."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede editar cotizaciones")
            return

        # Validar
        err_sal = validar_salario_base(self.form_cat_salario_base)
        err_min = validar_cantidad(self.form_cat_cantidad_min, "Cantidad mínima")
        self.error_cat_salario = err_sal or ""
        self.error_cat_cantidad_min = err_min or ""

        if err_sal or err_min:
            return

        if not self.form_cat_categoria_puesto_id:
            self.mostrar_mensaje("Selecciona una categoría de puesto", "error")
            return

        self.saving = True
        yield

        try:
            from app.services import cotizacion_service
            from app.entities import CotizacionPartidaCategoriaCreate
            from decimal import Decimal

            salario = Decimal(self.form_cat_salario_base.replace(',', ''))
            datos = CotizacionPartidaCategoriaCreate(
                partida_id=self.partida_seleccionada_id,
                categoria_puesto_id=self.form_cat_categoria_puesto_id,
                salario_base_mensual=salario,
                cantidad_minima=int(self.form_cat_cantidad_min),
                cantidad_maxima=int(self.form_cat_cantidad_max),
            )
            await cotizacion_service.agregar_categoria(
                datos,
                empresa_id=self.id_empresa_actual,
            )

            # Calcular costo patronal automáticamente
            empresa_id = self.id_empresa_actual
            if empresa_id:
                cat_result = await cotizacion_service.obtener_categorias_partida(
                    self.partida_seleccionada_id,
                    empresa_id=empresa_id,
                )
                if cat_result:
                    nueva_cat = cat_result[-1]
                    await cotizacion_service.calcular_costo_patronal(
                        nueva_cat.id,
                        empresa_id=empresa_id,
                    )

            self.cerrar_modal_categoria()
            await self._cargar_partida(self.partida_seleccionada_id, refrescar_partidas=True)
            await self._recargar_totales_cotizacion()
            self.mostrar_mensaje("Categoría agregada y costo patronal calculado", "success")

        except Exception as e:
            self.manejar_error(e, "agregar categoría")
        finally:
            self.saving = False

    async def eliminar_categoria(self, cat_id: int):
        """Elimina una categoría de la partida activa."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede editar cotizaciones")
            return

        self.saving = True
        yield

        try:
            from app.services import cotizacion_service
            await cotizacion_service.eliminar_categoria(
                cat_id,
                empresa_id=self.id_empresa_actual,
            )
            await self._cargar_partida(self.partida_seleccionada_id, refrescar_partidas=True)
            await self._recargar_totales_cotizacion()
            self.mostrar_mensaje("Categoría eliminada", "success")
        except Exception as e:
            self.manejar_error(e, "eliminar categoría")
        finally:
            self.saving = False

    async def recalcular_costo_patronal(self, cat_id: int):
        """Recalcula el costo patronal de una categoría."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede recalcular costos")
            return

        empresa_id = self.id_empresa_actual
        if not empresa_id:
            self.mostrar_mensaje("No hay empresa seleccionada", "error")
            return

        self.calculando_patronal = True
        yield

        try:
            from app.services import cotizacion_service
            resultado = await cotizacion_service.calcular_costo_patronal(
                cat_id,
                empresa_id=empresa_id,
            )
            self.ultimo_resultado_calculo = resultado
            await self._cargar_partida(
                self.partida_seleccionada_id,
                refrescar_partidas=True,
            )
            await self._recargar_totales_cotizacion()
            self.mostrar_mensaje("Costo patronal recalculado", "success")
        except Exception as e:
            self.manejar_error(e, "calcular costo patronal")
        finally:
            self.calculando_patronal = False

    async def guardar_costo_patronal_manual(self):
        """Guarda un costo patronal editado manualmente."""
        if not self.es_admin_empresa:
            return rx.toast.error("Solo admin_empresa puede editar cotizaciones")

        try:
            from decimal import Decimal
            from app.services import cotizacion_service

            valor = Decimal(self.form_costo_patronal_manual.replace(',', ''))
            await cotizacion_service.actualizar_categoria(
                self.cat_editando_id,
                {
                    'costo_patronal_editado': float(valor),
                    'fue_editado_manualmente': True,
                },
                empresa_id=self.id_empresa_actual,
            )
            await cotizacion_service.recalcular_precio_unitario(
                self.cat_editando_id,
                empresa_id=self.id_empresa_actual,
            )
            self.cerrar_modal_costo_patronal()
            await self._cargar_partida(
                self.partida_seleccionada_id,
                refrescar_partidas=True,
            )
            await self._recargar_totales_cotizacion()
            self.mostrar_mensaje("Costo patronal actualizado manualmente", "warning")
        except Exception as e:
            self.manejar_error(e, "editar costo patronal")

    async def agregar_concepto(self):
        """Agrega un concepto (gasto indirecto) a la partida."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede editar cotizaciones")
            return

        err = validar_nombre_concepto(self.form_concepto_nombre)
        self.error_concepto_nombre = err or ""
        if err:
            return

        self.saving = True
        yield

        try:
            from app.services import cotizacion_service
            from app.entities import CotizacionConceptoCreate
            from app.core.enums import TipoConceptoCotizacion, TipoValorConcepto

            datos = CotizacionConceptoCreate(
                partida_id=self.partida_seleccionada_id,
                nombre=self.form_concepto_nombre,
                tipo_concepto=TipoConceptoCotizacion.INDIRECTO,
                tipo_valor=TipoValorConcepto(self.form_concepto_tipo_valor),
            )
            await cotizacion_service.agregar_concepto(
                datos,
                empresa_id=self.id_empresa_actual,
            )
            self.cerrar_modal_concepto()
            await self._cargar_partida(
                self.partida_seleccionada_id,
                refrescar_partidas=True,
            )
            self.mostrar_mensaje("Concepto agregado", "success")

        except Exception as e:
            self.manejar_error(e, "agregar concepto")
        finally:
            self.saving = False

    async def eliminar_concepto(self, concepto_id: int):
        """Elimina un concepto INDIRECTO."""
        if not self.es_admin_empresa:
            return rx.toast.error("Solo admin_empresa puede editar cotizaciones")

        try:
            from app.services import cotizacion_service
            await cotizacion_service.eliminar_concepto(
                concepto_id,
                empresa_id=self.id_empresa_actual,
            )
            await self._cargar_partida(
                self.partida_seleccionada_id,
                refrescar_partidas=True,
            )
        except Exception as e:
            self.manejar_error(e, "eliminar concepto")

    async def actualizar_valor_celda(
        self, concepto_id: int, cat_id: int, valor_str: str
    ):
        """Actualiza el valor de una celda en la matriz."""
        if not self.es_admin_empresa:
            return rx.toast.error("Solo admin_empresa puede editar cotizaciones")

        try:
            from decimal import Decimal
            from app.services import cotizacion_service

            valor = Decimal(valor_str.replace(',', '') or '0')
            await cotizacion_service.actualizar_valor_concepto(
                concepto_id,
                cat_id,
                valor,
                empresa_id=self.id_empresa_actual,
            )
            await cotizacion_service.recalcular_precio_unitario(
                cat_id,
                empresa_id=self.id_empresa_actual,
            )
            await self._cargar_partida(
                self.partida_seleccionada_id,
                refrescar_partidas=True,
            )
            await self._recargar_totales_cotizacion()
        except Exception as e:
            self.manejar_error(e, "actualizar valor")

    async def cambiar_estatus_partida_local(self, nuevo_estatus: str):
        """Cambia el estatus de la partida activa."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede editar cotizaciones")
            return

        if not self.partida_seleccionada_id:
            return
        self.loading = True
        yield

        try:
            from app.services import cotizacion_service
            from app.core.enums import EstatusPartidaCotizacion
            estatus_enum = EstatusPartidaCotizacion(nuevo_estatus)
            await cotizacion_service.cambiar_estatus_partida(
                self.partida_seleccionada_id,
                estatus_enum,
                empresa_id=self.id_empresa_actual,
            )
            self.mostrar_mensaje(f"Estatus de partida actualizado", "success")
            await self._cargar_partida(
                self.partida_seleccionada_id,
                refrescar_partidas=True,
            )
        except Exception as e:
            self.manejar_error(e, "cambiar estatus partida")
        finally:
            self.loading = False

    async def convertir_partida_a_contrato(self, partida_id: int):
        """Convierte una partida ACEPTADA a contrato."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede convertir cotizaciones")
            return

        self.loading = True
        yield

        try:
            from app.services import cotizacion_service
            contrato_id = await cotizacion_service.convertir_partida_a_contrato(
                partida_id,
                empresa_id=self.id_empresa_actual,
            )
            self.mostrar_mensaje(f"Partida convertida a contrato #{contrato_id}", "success")
            await self._cargar_partida(
                self.partida_seleccionada_id,
                refrescar_partidas=True,
            )
        except Exception as e:
            self.manejar_error(e, "convertir partida")
        finally:
            self.loading = False

    # ─── Items CRUD (PRODUCTOS_SERVICIOS + extras globales) ───────────────────
    async def agregar_item_detalle(self):
        """Agrega un item a la partida actual o como item global."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede editar cotizaciones")
            return

        err_desc = validar_nombre_concepto(self.form_item_descripcion)
        err_cant = validar_cantidad(self.form_item_cantidad, "Cantidad")
        err_precio = validar_precio_unitario(self.form_item_precio_unitario)
        self.error_item_descripcion = err_desc or ""
        self.error_item_cantidad = err_cant or ""
        self.error_item_precio = err_precio or ""
        if err_desc or err_cant or err_precio:
            return

        self.saving = True
        yield

        try:
            from decimal import Decimal
            from app.services import cotizacion_service
            from app.entities import CotizacionItemCreate

            cotizacion_id = self.cotizacion.get('id')
            datos = CotizacionItemCreate(
                cotizacion_id=cotizacion_id,
                partida_id=self.form_item_partida_id if not self.form_item_es_global else None,
                cantidad=Decimal(self.form_item_cantidad),
                descripcion=self.form_item_descripcion.strip(),
                precio_unitario=Decimal(self.form_item_precio_unitario.replace(',', '')),
            )
            await cotizacion_service.agregar_item(
                datos,
                empresa_id=self.id_empresa_actual,
            )
            self.cerrar_modal_item()

            if self.form_item_es_global:
                items_globales_raw = await cotizacion_service.obtener_items(
                    cotizacion_id,
                    empresa_id=self.id_empresa_actual,
                )
                self.items_globales = [self._serializar_item(it) for it in items_globales_raw]
            if self.partida_seleccionada_id:
                await self._cargar_partida(self.partida_seleccionada_id, refrescar_partidas=True)
            await self._recargar_totales_cotizacion()
            self.mostrar_mensaje("Concepto agregado", "success")
        except Exception as e:
            self.manejar_error(e, "agregar concepto")
        finally:
            self.saving = False

    async def eliminar_item_detalle(self, item_id: int):
        """Elimina un item."""
        if not self.es_admin_empresa:
            return rx.toast.error("Solo admin_empresa puede editar cotizaciones")

        try:
            from app.services import cotizacion_service

            await cotizacion_service.eliminar_item(
                item_id,
                empresa_id=self.id_empresa_actual,
            )
            # Reload items
            cotizacion_id = self.cotizacion.get('id')
            items_globales_raw = await cotizacion_service.obtener_items(
                cotizacion_id,
                empresa_id=self.id_empresa_actual,
            )
            self.items_globales = [self._serializar_item(it) for it in items_globales_raw]

            if self.partida_seleccionada_id:
                await self._cargar_partida(self.partida_seleccionada_id, refrescar_partidas=True)
            await self._recargar_totales_cotizacion()
        except Exception as e:
            self.manejar_error(e, "eliminar concepto")

    async def actualizar_item_campo_detalle(
        self, item_id: int, campo: str, valor: str
    ):
        """Actualiza un campo de un item inline."""
        if not self.es_admin_empresa:
            return rx.toast.error("Solo admin_empresa puede editar cotizaciones")

        try:
            from decimal import Decimal
            from app.services import cotizacion_service

            datos = {}
            if campo == 'descripcion':
                datos['descripcion'] = valor.strip()
            elif campo == 'cantidad':
                datos['cantidad'] = float(Decimal(valor or '1'))
            elif campo == 'precio_unitario':
                datos['precio_unitario'] = float(Decimal(valor.replace(',', '') or '0'))

            if datos:
                await cotizacion_service.actualizar_item(
                    item_id,
                    datos,
                    empresa_id=self.id_empresa_actual,
                )
                # Reload
                cotizacion_id = self.cotizacion.get('id')
                items_globales_raw = await cotizacion_service.obtener_items(
                    cotizacion_id,
                    empresa_id=self.id_empresa_actual,
                )
                self.items_globales = [self._serializar_item(it) for it in items_globales_raw]

                if self.partida_seleccionada_id:
                    await self._cargar_partida(self.partida_seleccionada_id, refrescar_partidas=True)
                await self._recargar_totales_cotizacion()
        except Exception as e:
            self.manejar_error(e, "actualizar concepto")

    # ─── IVA y meses ──────────────────────────────────────────────────────────
    async def toggle_aplicar_iva(self, value: bool):
        """Activa/desactiva IVA en la cotización."""
        cotizacion_id = self.cotizacion.get('id')
        if not cotizacion_id:
            return

        try:
            from app.entities import CotizacionUpdate
            from app.services import cotizacion_service

            actualizada = await cotizacion_service.actualizar(
                int(cotizacion_id),
                CotizacionUpdate(aplicar_iva=value),
                empresa_id=self.id_empresa_actual,
            )
            self.cotizacion = actualizada.model_dump(mode='json')
            if self.partida_seleccionada_id:
                await self._cargar_partida(self.partida_seleccionada_id, refrescar_partidas=True)
            await self._recargar_totales_cotizacion()
        except Exception as e:
            self.manejar_error(e, "cambiar IVA")

    async def actualizar_cantidad_meses(self, value: str):
        """Actualiza la cantidad de meses de la cotización."""
        err = validar_cantidad_meses(value)
        if err:
            return

        cotizacion_id = self.cotizacion.get('id')
        if not cotizacion_id:
            return

        try:
            from app.entities import CotizacionUpdate
            from app.services import cotizacion_service

            actualizada = await cotizacion_service.actualizar(
                int(cotizacion_id),
                CotizacionUpdate(cantidad_meses=int(value)),
                empresa_id=self.id_empresa_actual,
            )
            self.cotizacion = actualizada.model_dump(mode='json')
            if self.partida_seleccionada_id:
                await self._cargar_partida(self.partida_seleccionada_id, refrescar_partidas=True)
            await self._recargar_totales_cotizacion()
        except Exception as e:
            self.manejar_error(e, "actualizar meses")

    async def crear_nueva_version_actual(self):
        """Duplica la cotización actual en una nueva versión editable."""
        if not self.es_admin_empresa:
            yield rx.toast.error("Solo admin_empresa puede versionar cotizaciones")
            return

        cotizacion_id = self.cotizacion.get('id')
        if not cotizacion_id:
            yield rx.toast.error("No se pudo identificar la cotización")
            return

        self.saving = True
        yield

        try:
            from app.services import cotizacion_service

            nueva = await cotizacion_service.crear_version(
                int(cotizacion_id),
                empresa_id=self.id_empresa_actual,
            )
            self.saving = False
            self.mostrar_mensaje(f"Nueva versión creada: {nueva.codigo}", "success")
            yield rx.redirect(f"{PORTAL_COTIZADOR_ROUTE}/{nueva.codigo}")
        except Exception as e:
            self.manejar_error(e, "crear nueva versión")
        finally:
            self.saving = False

    def _fmt_currency(self, valor) -> str:
        """Formatea montos para mostrar en resúmenes de partida."""
        try:
            return f"${float(valor or 0):,.2f}"
        except Exception:
            return "$0.00"

    def _fmt_decimal_input(self, valor) -> str:
        """Formatea números para inputs editables de matriz."""
        try:
            return f"{float(valor or 0):.2f}"
        except Exception:
            return "0.00"

    def _serializar_item(self, item) -> dict:
        """Serializa un CotizacionItem para la UI."""
        data = item.model_dump(mode='json') if hasattr(item, 'model_dump') else dict(item)
        data['cantidad_texto'] = str(data.get('cantidad', '1'))
        data['precio_unitario_texto'] = self._fmt_decimal_input(data.get('precio_unitario'))
        data['importe_texto'] = self._fmt_currency(data.get('importe'))
        return data

    def _serializar_columnas_matriz(self, categorias: list[dict]) -> list[dict]:
        """Prepara metadatos de columnas para la matriz de costos."""
        columnas = []
        for categoria in categorias:
            columnas.append(
                {
                    "id": categoria.get("id", 0),
                    "categoria_nombre": categoria.get("categoria_nombre", "Categoría"),
                    "cantidad_rango_texto": (
                        f"{int(categoria.get('cantidad_minima') or 0)} - "
                        f"{int(categoria.get('cantidad_maxima') or 0)} oper."
                    ),
                    "precio_unitario_texto": self._fmt_currency(
                        categoria.get("precio_unitario_final")
                    ),
                }
            )
        return columnas

    def _serializar_matriz_costos(
        self,
        conceptos: list[dict],
        categorias: list[dict],
        valores: list[dict],
    ) -> list[dict]:
        """Construye filas reactivas y serializables para la matriz."""
        valor_map = {
            (int(v.get("concepto_id", 0)), int(v.get("partida_categoria_id", 0))): v
            for v in valores
        }
        filas = []
        for concepto in conceptos:
            concepto_id = int(concepto.get("id", 0))
            tipo_concepto = concepto.get("tipo_concepto", "INDIRECTO")
            tipo_valor = concepto.get("tipo_valor", "FIJO")
            celdas = []
            for categoria in categorias:
                categoria_id = int(categoria.get("id", 0))
                valor = valor_map.get(
                    (concepto_id, categoria_id),
                    {
                        "valor_capturado": 0,
                        "valor_calculado": 0,
                    },
                )
                es_editable = (
                    self.cotizacion.get("estatus") == "BORRADOR"
                    and tipo_concepto == "INDIRECTO"
                    and not bool(concepto.get("es_autogenerado", False))
                )
                celdas.append(
                    {
                        "partida_categoria_id": categoria_id,
                        "editable": es_editable,
                        "valor_input": self._fmt_decimal_input(
                            valor.get("valor_capturado")
                        ),
                        "valor_calculado_texto": self._fmt_currency(
                            valor.get("valor_calculado")
                        ),
                        "valor_mostrado_texto": self._fmt_currency(
                            valor.get("valor_calculado")
                        ),
                    }
                )

            filas.append(
                {
                    "id": concepto_id,
                    "nombre": concepto.get("nombre", ""),
                    "tipo_concepto": tipo_concepto,
                    "tipo_valor": tipo_valor,
                    "tipo_valor_texto": (
                        "Porcentaje (%)"
                        if tipo_valor == "PORCENTAJE"
                        else "Importe fijo (pesos)"
                    ),
                    "es_autogenerado": bool(concepto.get("es_autogenerado", False)),
                    "celdas": celdas,
                }
            )
        return filas

    def _serializar_partida_resumen(self, partida) -> dict:
        """Prepara el resumen de partida listo para render en UI."""
        data = partida.model_dump(mode='json')
        es_productos = self.cotizacion.get('tipo') == 'PRODUCTOS_SERVICIOS'

        cantidad_min = int(data.get("cantidad_personal_minima") or 0)
        cantidad_max = int(data.get("cantidad_personal_maxima") or 0)
        if es_productos:
            data["personal_rango_texto"] = ""
            data["categorias_texto"] = f"{int(data.get('cantidad_categorias') or 0)} conceptos"
        else:
            data["personal_rango_texto"] = f"{cantidad_min} - {cantidad_max} personas"
            data["categorias_texto"] = f"{int(data.get('cantidad_categorias') or 0)} categorías"
        data["total_minimo_texto"] = self._fmt_currency(data.get("total_minimo"))
        data["total_maximo_texto"] = self._fmt_currency(data.get("total_maximo"))

        notas = (data.get("notas") or "").strip()
        if notas:
            data["notas_resumen"] = notas if len(notas) <= 72 else f"{notas[:69].rstrip()}..."
        else:
            data["notas_resumen"] = "Sin notas de partida"
        return data

    # ─── Computed vars ────────────────────────────────────────────────────────
    @rx.var
    def tipo_cotizacion(self) -> str:
        return self.cotizacion.get('tipo', 'PERSONAL')

    @rx.var
    def es_tipo_personal(self) -> bool:
        return self.tipo_cotizacion == 'PERSONAL'

    @rx.var
    def es_tipo_productos(self) -> bool:
        return self.tipo_cotizacion == 'PRODUCTOS_SERVICIOS'

    @rx.var
    def aplicar_iva(self) -> bool:
        return bool(self.cotizacion.get('aplicar_iva', False))

    @rx.var
    def cantidad_meses(self) -> str:
        return str(self.cotizacion.get('cantidad_meses', 1))

    @rx.var
    def hay_items_partida(self) -> bool:
        return len(self.items_partida) > 0

    @rx.var
    def hay_items_globales(self) -> bool:
        return len(self.items_globales) > 0

    @rx.var
    def cotizacion_es_editable(self) -> bool:
        return self.cotizacion.get('estatus') == 'BORRADOR'

    @rx.var
    def puede_preparar_cotizacion(self) -> bool:
        return self.cotizacion.get('estatus') == 'BORRADOR'

    @rx.var
    def puede_marcar_enviada(self) -> bool:
        return self.cotizacion.get('estatus') == 'PREPARADA'

    @rx.var
    def puede_aprobar_cotizacion(self) -> bool:
        return self.cotizacion.get('estatus') in ('PREPARADA', 'ENVIADA')

    @rx.var
    def puede_rechazar_cotizacion(self) -> bool:
        return self.cotizacion.get('estatus') in ('PREPARADA', 'ENVIADA')

    @rx.var
    def puede_descargar_pdf(self) -> bool:
        return (
            self.cantidad_partidas > 0
            and self.cotizacion.get('estatus') in ('PREPARADA', 'ENVIADA', 'APROBADA', 'RECHAZADA')
        )

    @rx.var
    def puede_versionar_cotizacion(self) -> bool:
        return self.cotizacion.get('estatus') in ('BORRADOR', 'PREPARADA', 'ENVIADA', 'RECHAZADA')

    @rx.var
    def titulo_cotizacion(self) -> str:
        codigo = self.cotizacion.get('codigo', '')
        return f"Cotización {codigo}" if codigo else "Cotización"

    @rx.var
    def version_cotizacion(self) -> str:
        return f"Versión {self.cotizacion.get('version', 1)}"

    @rx.var
    def periodo_cotizacion(self) -> str:
        fecha_inicio = self.cotizacion.get('fecha_inicio_periodo')
        fecha_fin = self.cotizacion.get('fecha_fin_periodo')
        if fecha_inicio and fecha_fin:
            inicio = _formatear_fecha(fecha_inicio)
            fin = _formatear_fecha(fecha_fin)
            return f"{inicio} a {fin}"
        return "Periodo no definido"

    @rx.var
    def destinatario_cotizacion(self) -> str:
        nombre = (self.cotizacion.get('destinatario_nombre') or '').strip()
        cargo = (self.cotizacion.get('destinatario_cargo') or '').strip()
        if nombre and cargo:
            return f"{nombre} · {cargo}"
        if nombre:
            return nombre
        if cargo:
            return cargo
        return "Sin destinatario capturado"

    @rx.var
    def notas_cotizacion_resumen(self) -> str:
        notas = (self.cotizacion.get('notas') or '').strip()
        if not notas:
            return "Sin notas adicionales"
        if len(notas) <= 140:
            return notas
        return f"{notas[:137].rstrip()}..."

    @rx.var
    def desglose_pdf_texto(self) -> str:
        if self.cotizacion.get('mostrar_desglose'):
            return "PDF con desglose de conceptos"
        return "PDF resumido sin desglose"

    @rx.var
    def representante_legal_cotizacion(self) -> str:
        representante = (self.cotizacion.get('representante_legal') or '').strip()
        return representante or "Sin representante legal configurado"

    @rx.var
    def cantidad_partidas(self) -> int:
        return len(self.partidas)

    @rx.var
    def cantidad_partidas_texto(self) -> str:
        return f"{self.cantidad_partidas} partidas"

    @rx.var
    def partida_activa(self) -> dict:
        """Retorna los datos de la partida seleccionada."""
        for p in self.partidas:
            if p.get('id') == self.partida_seleccionada_id:
                return p
        return {}

    @rx.var
    def hay_categorias(self) -> bool:
        return len(self.categorias_partida) > 0

    @rx.var
    def hay_matriz_costos(self) -> bool:
        return len(self.matriz_costos) > 0

    @rx.var
    def tiene_acciones_estatus(self) -> bool:
        return (
            self.puede_preparar_cotizacion
            or self.puede_marcar_enviada
            or self.puede_aprobar_cotizacion
            or self.puede_rechazar_cotizacion
        )

    @rx.var
    def puede_editar_info_cotizacion(self) -> bool:
        return self.cotizacion_es_editable

    @rx.var
    def partida_titulo(self) -> str:
        numero = self.partida_activa.get('numero_partida')
        if numero:
            return f"Partida {numero}"
        return "Partida"

    @rx.var
    def partida_rango_total_texto(self) -> str:
        minimo = self.partida_activa.get('total_minimo_texto', '$0.00')
        maximo = self.partida_activa.get('total_maximo_texto', '$0.00')
        if self.es_tipo_productos or minimo == maximo:
            return minimo
        return f"{minimo} a {maximo}"

    @rx.var
    def partida_rango_personal_texto(self) -> str:
        if self.es_tipo_productos:
            return ""
        return self.partida_activa.get('personal_rango_texto', '0 - 0 personas')

    @rx.var
    def partida_categorias_texto(self) -> str:
        return self.partida_activa.get('categorias_texto', '0 categorías')

    @rx.var
    def partida_notas_resumen(self) -> str:
        return self.partida_activa.get('notas_resumen', 'Sin notas de partida')

    @rx.var
    def puede_editar_info_partida(self) -> bool:
        return self.cotizacion_es_editable and self.partida_seleccionada_id > 0

    @rx.var
    def puede_asignar_partidas(self) -> bool:
        return self.cotizacion.get('estatus') == 'APROBADA'

    @rx.var
    def iva_texto(self) -> str:
        if self.aplicar_iva:
            return "IVA 16% incluido"
        return "Sin IVA"

    @rx.var
    def meses_texto(self) -> str:
        meses = self.cotizacion.get('cantidad_meses', 1)
        if meses and int(meses) > 1:
            return f"{meses} meses"
        return "1 mes"

    @rx.var
    def tiene_periodo_definido(self) -> bool:
        return bool(
            self.cotizacion.get('fecha_inicio_periodo')
            and self.cotizacion.get('fecha_fin_periodo')
        )

    # ─── Totales de partida formateados ────────────────────────────────────────
    @rx.var
    def resumen_subtotal_min(self) -> str:
        val = self.totales_partida.get('subtotal_minimo') or self.totales_partida.get('subtotal')
        return self._fmt_currency(val)

    @rx.var
    def resumen_subtotal_max(self) -> str:
        val = self.totales_partida.get('subtotal_maximo') or self.totales_partida.get('subtotal')
        return self._fmt_currency(val)

    @rx.var
    def resumen_iva_min(self) -> str:
        val = self.totales_partida.get('iva_minimo') or self.totales_partida.get('iva')
        return self._fmt_currency(val)

    @rx.var
    def resumen_iva_max(self) -> str:
        val = self.totales_partida.get('iva_maximo') or self.totales_partida.get('iva')
        return self._fmt_currency(val)

    @rx.var
    def resumen_total_min(self) -> str:
        val = self.totales_partida.get('total_minimo') or self.totales_partida.get('total')
        return self._fmt_currency(val)

    @rx.var
    def resumen_total_max(self) -> str:
        val = self.totales_partida.get('total_maximo') or self.totales_partida.get('total')
        return self._fmt_currency(val)

    # ─── Totales de cotización (todas las partidas + globales + IVA) ──────────
    @rx.var
    def cot_subtotal_min(self) -> str:
        val = self.totales_cotizacion.get('subtotal_minimo')
        return self._fmt_currency(val)

    @rx.var
    def cot_subtotal_max(self) -> str:
        val = self.totales_cotizacion.get('subtotal_maximo')
        return self._fmt_currency(val)

    @rx.var
    def cot_iva_min(self) -> str:
        val = self.totales_cotizacion.get('iva_minimo')
        return self._fmt_currency(val)

    @rx.var
    def cot_iva_max(self) -> str:
        val = self.totales_cotizacion.get('iva_maximo')
        return self._fmt_currency(val)

    @rx.var
    def cot_total_min(self) -> str:
        val = self.totales_cotizacion.get('total_minimo')
        return self._fmt_currency(val)

    @rx.var
    def cot_total_max(self) -> str:
        val = self.totales_cotizacion.get('total_maximo')
        return self._fmt_currency(val)

    @rx.var
    def hay_totales_cotizacion(self) -> bool:
        return len(self.totales_cotizacion) > 0
