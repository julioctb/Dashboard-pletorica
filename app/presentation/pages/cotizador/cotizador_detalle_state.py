"""
Estado del detalle de una cotización (partidas + matriz de costos).
"""
import reflex as rx
from typing import Optional

from app.presentation.components.shared.auth_state import AuthState
from app.presentation.pages.cotizador.cotizador_validators import (
    validar_salario_base,
    validar_cantidad,
    validar_nombre_concepto,
)


class CotizadorDetalleState(AuthState):
    """Estado del detalle de cotización: partidas, categorías y matriz."""

    # ─── Datos principales ────────────────────────────────────────────────────
    cotizacion: dict = {}
    partidas: list[dict] = []
    partida_seleccionada_id: int = 0
    categorias_partida: list[dict] = []
    conceptos_partida: list[dict] = []
    totales_partida: dict = {}

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

    # ─── Modal edición costo patronal ─────────────────────────────────────────
    mostrar_modal_costo_patronal: bool = False
    cat_editando_id: int = 0
    form_costo_patronal_manual: str = ""
    ultimo_resultado_calculo: dict = {}

    # ─── Estado de UI ─────────────────────────────────────────────────────────
    loading_detalle: bool = False
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
        self.error_cat_salario = ""

    def set_form_cat_cantidad_min(self, value: str):
        self.form_cat_cantidad_min = value
        self.error_cat_cantidad_min = ""

    def set_form_cat_cantidad_max(self, value: str):
        self.form_cat_cantidad_max = value

    def set_form_concepto_nombre(self, value: str):
        self.form_concepto_nombre = value
        self.error_concepto_nombre = ""

    def set_form_concepto_tipo_valor(self, value: str):
        self.form_concepto_tipo_valor = value

    def set_form_costo_patronal_manual(self, value: str):
        self.form_costo_patronal_manual = value

    def set_mostrar_modal_categoria(self, value: bool):
        self.mostrar_modal_categoria = value

    def set_mostrar_modal_concepto(self, value: bool):
        self.mostrar_modal_concepto = value

    def set_mostrar_modal_costo_patronal(self, value: bool):
        self.mostrar_modal_costo_patronal = value

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

    def abrir_modal_costo_patronal(self, cat_id: int, costo_actual: str):
        self.cat_editando_id = cat_id
        self.form_costo_patronal_manual = costo_actual
        self.mostrar_modal_costo_patronal = True

    def cerrar_modal_costo_patronal(self):
        self.mostrar_modal_costo_patronal = False

    # ─── Handlers principales ─────────────────────────────────────────────────
    async def cargar_detalle(self, cotizacion_id: str):
        """Carga el detalle completo de la cotización."""
        self.loading_detalle = True
        self.partida_seleccionada_id = 0
        self.partidas = []
        self.categorias_partida = []
        self.conceptos_partida = []
        self.totales_partida = {}
        yield

        try:
            from app.services import cotizacion_service, categoria_puesto_service

            cot_id = int(cotizacion_id)
            cotizacion = await cotizacion_service.obtener_por_id(cot_id)
            self.cotizacion = cotizacion.model_dump(mode='json')

            partidas = await cotizacion_service.obtener_partidas(cot_id)
            self.partidas = [p.model_dump(mode='json') for p in partidas]

            # Seleccionar primera partida
            if self.partidas and not self.partida_seleccionada_id:
                self.partida_seleccionada_id = self.partidas[0]['id']
                await self._cargar_partida(self.partidas[0]['id'])
            elif not self.partidas:
                self.partida_seleccionada_id = 0

            # Cargar catálogo de categorías de puesto
            cats = await categoria_puesto_service.obtener_todas()
            self.categorias_puesto_catalogo = [
                {'id': c.id, 'nombre': c.nombre, 'clave': c.clave}
                for c in cats
            ]

        except Exception as e:
            self.manejar_error(e, "cargar cotización")
        finally:
            self.loading_detalle = False

    async def seleccionar_partida(self, partida_id: int):
        """Selecciona una partida y carga su contenido."""
        self.partida_seleccionada_id = partida_id
        await self._cargar_partida(partida_id)

    async def _cargar_partida(self, partida_id: int):
        """Carga categorías y conceptos de la partida seleccionada."""
        try:
            from app.services import cotizacion_service

            categorias = await cotizacion_service.obtener_categorias_partida(partida_id)
            self.categorias_partida = [c.model_dump(mode='json') for c in categorias]

            conceptos = await cotizacion_service.obtener_conceptos_partida(partida_id)
            self.conceptos_partida = [c.model_dump(mode='json') for c in conceptos]

            totales = await cotizacion_service.recalcular_totales_partida(partida_id)
            self.totales_partida = totales

        except Exception as e:
            self.manejar_error(e, "cargar partida")

    async def agregar_partida(self):
        """Agrega una nueva partida a la cotización."""
        cotizacion_id = self.cotizacion.get('id')
        if not cotizacion_id:
            return

        self.loading = True
        yield

        try:
            from app.services import cotizacion_service
            partida = await cotizacion_service.agregar_partida(cotizacion_id)

            partidas = await cotizacion_service.obtener_partidas(cotizacion_id)
            self.partidas = [p.model_dump(mode='json') for p in partidas]

            self.partida_seleccionada_id = partida.id
            await self._cargar_partida(partida.id)
            self.mostrar_mensaje(f"Partida {partida.numero_partida} agregada", "success")

        except Exception as e:
            self.manejar_error(e, "agregar partida")
        finally:
            self.loading = False

    async def agregar_categoria(self):
        """Agrega una categoría a la partida seleccionada."""
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
            await cotizacion_service.agregar_categoria(datos)

            # Calcular costo patronal automáticamente
            empresa_id = self.empresa_actual.get('id') if self.empresa_actual else None
            if empresa_id:
                cat_result = await cotizacion_service.obtener_categorias_partida(
                    self.partida_seleccionada_id
                )
                if cat_result:
                    nueva_cat = cat_result[-1]
                    await cotizacion_service.calcular_costo_patronal(
                        nueva_cat.id, empresa_id
                    )

            self.cerrar_modal_categoria()
            await self._cargar_partida(self.partida_seleccionada_id)
            self.mostrar_mensaje("Categoría agregada y costo patronal calculado", "success")

        except Exception as e:
            self.manejar_error(e, "agregar categoría")
        finally:
            self.saving = False

    async def eliminar_categoria(self, cat_id: int):
        """Elimina una categoría de la partida activa."""
        self.saving = True
        yield

        try:
            from app.services import cotizacion_service
            await cotizacion_service.eliminar_categoria(cat_id)
            await self._cargar_partida(self.partida_seleccionada_id)
            self.mostrar_mensaje("Categoría eliminada", "success")
        except Exception as e:
            self.manejar_error(e, "eliminar categoría")
        finally:
            self.saving = False

    async def recalcular_costo_patronal(self, cat_id: int):
        """Recalcula el costo patronal de una categoría."""
        empresa_id = self.empresa_actual.get('id') if self.empresa_actual else None
        if not empresa_id:
            self.mostrar_mensaje("No hay empresa seleccionada", "error")
            return

        self.calculando_patronal = True
        yield

        try:
            from app.services import cotizacion_service
            resultado = await cotizacion_service.calcular_costo_patronal(cat_id, empresa_id)
            self.ultimo_resultado_calculo = resultado
            await self._cargar_partida(self.partida_seleccionada_id)
            self.mostrar_mensaje("Costo patronal recalculado", "success")
        except Exception as e:
            self.manejar_error(e, "calcular costo patronal")
        finally:
            self.calculando_patronal = False

    async def guardar_costo_patronal_manual(self):
        """Guarda un costo patronal editado manualmente."""
        try:
            from decimal import Decimal
            from app.services import cotizacion_service

            valor = Decimal(self.form_costo_patronal_manual.replace(',', ''))
            await cotizacion_service.actualizar_categoria(
                self.cat_editando_id,
                {
                    'costo_patronal_editado': float(valor),
                    'fue_editado_manualmente': True,
                }
            )
            await cotizacion_service.recalcular_precio_unitario(self.cat_editando_id)
            self.cerrar_modal_costo_patronal()
            await self._cargar_partida(self.partida_seleccionada_id)
            self.mostrar_mensaje("Costo patronal actualizado manualmente", "warning")
        except Exception as e:
            self.manejar_error(e, "editar costo patronal")

    async def agregar_concepto(self):
        """Agrega un concepto (gasto indirecto) a la partida."""
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
            await cotizacion_service.agregar_concepto(datos)
            self.cerrar_modal_concepto()
            await self._cargar_partida(self.partida_seleccionada_id)
            self.mostrar_mensaje("Concepto agregado", "success")

        except Exception as e:
            self.manejar_error(e, "agregar concepto")
        finally:
            self.saving = False

    async def eliminar_concepto(self, concepto_id: int):
        """Elimina un concepto INDIRECTO."""
        try:
            from app.services import cotizacion_service
            await cotizacion_service.eliminar_concepto(concepto_id)
            await self._cargar_partida(self.partida_seleccionada_id)
        except Exception as e:
            self.manejar_error(e, "eliminar concepto")

    async def actualizar_valor_celda(
        self, concepto_id: int, cat_id: int, valor_str: str
    ):
        """Actualiza el valor de una celda en la matriz."""
        try:
            from decimal import Decimal
            from app.services import cotizacion_service

            valor = Decimal(valor_str.replace(',', '') or '0')
            await cotizacion_service.actualizar_valor_concepto(concepto_id, cat_id, valor)
            await cotizacion_service.recalcular_precio_unitario(cat_id)
            await self._cargar_partida(self.partida_seleccionada_id)
        except Exception as e:
            self.manejar_error(e, "actualizar valor")

    async def cambiar_estatus_partida_local(self, nuevo_estatus: str):
        """Cambia el estatus de la partida activa."""
        if not self.partida_seleccionada_id:
            return
        self.loading = True
        yield

        try:
            from app.services import cotizacion_service
            from app.core.enums import EstatusPartidaCotizacion
            estatus_enum = EstatusPartidaCotizacion(nuevo_estatus)
            await cotizacion_service.cambiar_estatus_partida(
                self.partida_seleccionada_id, estatus_enum
            )
            self.mostrar_mensaje(f"Estatus de partida actualizado", "success")
            await self._cargar_partida(self.partida_seleccionada_id)
            partidas = await cotizacion_service.obtener_partidas(self.cotizacion.get('id', 0))
            self.partidas = [p.model_dump(mode='json') for p in partidas]
        except Exception as e:
            self.manejar_error(e, "cambiar estatus partida")
        finally:
            self.loading = False

    async def convertir_partida_a_contrato(self, partida_id: int):
        """Convierte una partida ACEPTADA a contrato."""
        self.loading = True
        yield

        try:
            from app.services import cotizacion_service
            contrato_id = await cotizacion_service.convertir_partida_a_contrato(partida_id)
            self.mostrar_mensaje(f"Partida convertida a contrato #{contrato_id}", "success")
            await self._cargar_partida(self.partida_seleccionada_id)
            partidas = await cotizacion_service.obtener_partidas(self.cotizacion.get('id', 0))
            self.partidas = [p.model_dump(mode='json') for p in partidas]
        except Exception as e:
            self.manejar_error(e, "convertir partida")
        finally:
            self.loading = False

    # ─── Computed vars ────────────────────────────────────────────────────────
    @rx.var
    def cotizacion_es_editable(self) -> bool:
        return self.cotizacion.get('estatus') == 'BORRADOR'

    @rx.var
    def titulo_cotizacion(self) -> str:
        codigo = self.cotizacion.get('codigo', '')
        return f"Cotización {codigo}" if codigo else "Cotización"

    @rx.var
    def cantidad_partidas(self) -> int:
        return len(self.partidas)

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
