"""Componente reutilizable de barra de herramientas con filtros."""
import reflex as rx
from typing import Callable, List

from .filters import (
    input_busqueda,
    indicador_filtros,
    contador_registros,
    switch_inactivos,
    barra_filtros,
)


def barra_herramientas(
    # State vars
    filtro_busqueda: rx.Var,
    incluir_inactivas: rx.Var,
    tiene_filtros_activos: rx.Var,
    total: rx.Var,
    # Callbacks
    on_change_busqueda: Callable,
    on_clear_busqueda: Callable,
    on_key_down: Callable,
    on_toggle_inactivas: Callable,
    on_limpiar_filtros: Callable,
    # Entity info
    texto_entidad: str,
    texto_entidad_plural: str = "",
    # Optional extra filters
    filtros_extra: List[rx.Component] = None,
) -> rx.Component:
    """
    Barra de herramientas genérica con filtros estándar.

    Args:
        filtro_busqueda: Variable con el valor del input de búsqueda
        incluir_inactivas: Variable booleana del switch
        tiene_filtros_activos: Variable booleana indicando filtros activos
        total: Variable con el total de registros
        on_change_busqueda: Callback al cambiar búsqueda
        on_clear_busqueda: Callback al limpiar búsqueda
        on_key_down: Callback al presionar tecla
        on_toggle_inactivas: Callback al cambiar switch
        on_limpiar_filtros: Callback al limpiar todos los filtros
        texto_entidad: Nombre de la entidad en singular
        texto_entidad_plural: Nombre en plural (opcional)
        filtros_extra: Lista de componentes de filtro adicionales
    """
    # Construir lista de componentes
    componentes = [
        # Input de búsqueda
        input_busqueda(
            value=filtro_busqueda,
            on_change=on_change_busqueda,
            on_clear=on_clear_busqueda,
            on_key_down=on_key_down,
        ),
    ]

    # Agregar filtros extra si existen
    if filtros_extra:
        componentes.extend(filtros_extra)

    # Agregar componentes estándar
    componentes.extend([
        # Switch inactivas
        switch_inactivos(
            checked=incluir_inactivas,
            on_change=on_toggle_inactivas,
        ),
        # Indicador de filtros
        indicador_filtros(
            tiene_filtros=tiene_filtros_activos,
            on_limpiar=on_limpiar_filtros,
        ),
        rx.spacer(),
    ])

    return barra_filtros(
        *componentes,
        contador=contador_registros(
            total=total,
            tiene_filtros=tiene_filtros_activos,
            texto_entidad=texto_entidad,
            texto_entidad_plural=texto_entidad_plural,
        ),
    )
