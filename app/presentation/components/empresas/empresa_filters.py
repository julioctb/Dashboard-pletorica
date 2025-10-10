"""Componente de filtros específico para el módulo de empresas"""
from typing import Type
import reflex as rx

from app.entities import TipoEmpresa, EstatusEmpresa


def empresa_filters(estado: Type[rx.State]) -> rx.Component:
    """
    Componente de filtros para el módulo de empresas

    Args:
        estado: Clase de estado (EmpresasState) con los campos:
            - filtro_busqueda: str
            - filtro_tipo: str
            - filtro_estatus: str
            - incluir_inactivas: bool
            - set_filtro_busqueda, set_filtro_tipo, set_filtro_estatus, set_incluir_inactivas
            - aplicar_filtros(), limpiar_filtros()

    Returns:
        Componente de card con filtros de búsqueda
    """
    return rx.card(
        rx.vstack(
            rx.text("Filtros de Búsqueda", size="3", weight="bold"),

            rx.hstack(
                # Búsqueda general
                rx.input(
                    placeholder="Buscar por nombre comercial...",
                    value=estado.filtro_busqueda,
                    on_change=estado.set_filtro_busqueda,
                    size="2",
                    width="100%"
                ),

                # Filtro por tipo
                rx.select(
                    [tipo.value for tipo in TipoEmpresa],
                    placeholder="Tipo de empresa",
                    value=estado.filtro_tipo,
                    on_change=estado.set_filtro_tipo,
                    size="2"
                ),

                # Filtro por estatus
                rx.select(
                    [estatus.value for estatus in EstatusEmpresa],
                    placeholder="Estatus",
                    value=estado.filtro_estatus,
                    on_change=estado.set_filtro_estatus,
                    size="2"
                ),

                # Checkbox para incluir inactivas
                rx.checkbox(
                    "Incluir inactivas",
                    checked=estado.incluir_inactivas,
                    on_change=estado.set_incluir_inactivas
                ),

                spacing="2",
                wrap="wrap"
            ),

            rx.hstack(
                rx.button(
                    "Aplicar Filtros",
                    on_click=estado.aplicar_filtros,
                    size="2"
                ),
                rx.button(
                    "Limpiar",
                    on_click=estado.limpiar_filtros,
                    variant="soft",
                    size="2"
                ),
                spacing="2"
            ),

            spacing="3"
        ),
        width="100%"
    )
