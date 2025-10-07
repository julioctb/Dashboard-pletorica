from typing import Type
import reflex as rx

# Importar desde el domain layer
from app.entities import TipoEmpresa, EstatusEmpresa

def filtros_component(estado: Type[rx.State]) -> rx.Component:
  
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
                
                #TODO: agregar un condicional para los demas filtros
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