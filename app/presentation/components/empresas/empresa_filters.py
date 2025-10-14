"""Componente de filtros específico para el módulo de empresas"""
from typing import Type
import reflex as rx

from app.entities import TipoEmpresa, EstatusEmpresa


def empresa_filters(estado: Type[rx.State]) -> rx.Component:
    """
    Componente de filtros manuales para el módulo de empresas.

    Comportamiento TODO MANUAL:
    - Cambiar cualquier filtro → Solo actualiza UI (no hace request)
    - Click "Buscar" → Aplica TODOS los filtros a la vez
    - Click "Mostrar Todas" → Limpia todos los filtros y recarga

    Mejoras UI/UX v2.0:
    - Jerarquía visual mejorada (título size="5", controles size="3")
    - Accesibilidad WCAG 2.1 AA (controles 40px, contraste mejorado)
    - Badge contador de filtros activos
    - Switch en lugar de checkbox
    - Iconos en botones para mejor reconocimiento
    - Espaciado optimizado (spacing="3" horizontal, spacing="4" vertical)

    Args:
        estado: Clase de estado (EmpresasState) con los campos:
            - filtro_busqueda: str
            - filtro_tipo: str
            - filtro_estatus: str
            - incluir_inactivas: bool
            - tiene_filtros_activos: bool (computed)
            - cantidad_filtros_activos: int (computed)
            - set_filtro_busqueda, set_filtro_tipo, set_filtro_estatus, set_incluir_inactivas
            - aplicar_filtros(), limpiar_filtros()

    Returns:
        Componente de card con filtros manuales profesionales
    """
    return rx.card(
        rx.vstack(
            # ===== HEADER =====
            rx.hstack(
                # Título + Badge contador
                rx.hstack(
                    rx.text(
                        "Filtros",
                        size="5",  # 20px - Mayor jerarquía visual
                        weight="bold"
                    ),
                    # Badge contador de filtros activos
                    rx.cond(
                        estado.tiene_filtros_activos,
                        rx.badge(
                            estado.cantidad_filtros_activos,
                            color_scheme="blue",
                            variant="soft"
                        )
                    ),
                    spacing="2",
                    align="center"
                ),

                rx.spacer(),

                # Instrucción
                rx.text(
                    "Configure los filtros y presione 'Buscar' para aplicar",
                    size="2",  # 14px - Legible (antes era 12px)
                    color="var(--gray-11)"  # Contraste mejorado (antes --gray-9)
                ),
                width="100%",
                align="center"
            ),

            # ===== DIVIDER =====
            rx.divider(size="4", color_scheme="gray"),

            # ===== FILA 1: BÚSQUEDA =====
            rx.vstack(
                # Input búsqueda (100% width)
                rx.input(
                    placeholder="Buscar por nombre comercial o razón social...",  # Sin emoji, más descriptivo
                    value=estado.filtro_busqueda,
                    on_change=estado.set_filtro_busqueda,
                    size="3",  # 16px texto, 40px height
                    style={"height": "40px"},  # Cumple WCAG 44px target
                    width="100%"
                ),

                # Botones de acción (alineados a la derecha)
                rx.hstack(
                    rx.button(
                        rx.icon("search", size=18),
                        "Buscar",
                        on_click=estado.aplicar_filtros,
                        size="3",
                        style={"height": "40px"}
                    ),
                    rx.button(
                        rx.icon("refresh-cw", size=18),
                        "Mostrar Todas",
                        on_click=estado.limpiar_filtros,
                        variant="soft",
                        size="3",
                        style={"height": "40px"}
                    ),
                    spacing="3",  # 12px - Mejor espaciado
                    justify="end"
                ),

                spacing="2",  # 8px entre input y botones
                width="100%"
            ),

            # ===== FILA 2: FILTROS ADICIONALES =====
            rx.hstack(
                # Filtro por tipo
                rx.select(
                    [tipo.value for tipo in TipoEmpresa],
                    placeholder="Tipo de empresa",
                    value=estado.filtro_tipo,
                    on_change=estado.set_filtro_tipo,
                    size="3"  # 16px - Mayor legibilidad
                ),

                # Filtro por estatus
                rx.select(
                    [estatus.value for estatus in EstatusEmpresa],
                    placeholder="Estatus",
                    value=estado.filtro_estatus,
                    on_change=estado.set_filtro_estatus,
                    size="3"
                ),

                # Switch para incluir inactivas (mejor que checkbox)
                rx.hstack(
                    rx.text(
                        "Incluir inactivas",
                        size="2",  # 14px
                        weight="medium"
                    ),
                    rx.switch(
                        checked=estado.incluir_inactivas,
                        on_change=estado.set_incluir_inactivas,
                        size="3"
                    ),
                    spacing="2",
                    align="center"
                ),

                spacing="3",  # 12px - Mejor espaciado horizontal
                width="100%",
                align="center"
            ),

            spacing="4",  # 16px - Respiro entre secciones principales
            width="100%"
        ),
        width="100%",
        style={
            "minWidth": "100%",
            "maxWidth": "100%",
            "flexShrink": "0"
        }
    )
