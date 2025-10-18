import reflex as rx

from typing import Type, List, Dict, Callable

def empresa_filters(
        
        #Datos del estado
        estado: Type[rx.State],

        #configuracion de filtros
        chip_filters: List[dict], #lista de las configiraciones de chips
        text_search_config: Dict, #configuracion de la busqueda
        extra_controls: List[rx.Component],

        #Callbacks
        on_apply: Callable,
        on_clear: Callable


        ) -> rx.Component:
      """
      Panel de filtros reutilizable.
      
      Args:
          chip_filters: [
              {
                  "header": "Tipo de empresa",
                  "icon": "building",
                  "items": ["NOMINA", "MANTENIMIENTO"],
                  "selected_items": estado.chips_tipo,
                  "on_add": estado.add_chip_tipo,
                  "on_remove": estado.remove_chip_tipo
              },
              {...}  # Otro grupo de chips
          ]
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
                        justify="end",
                        width="100%"  # Necesario para que justify="end" funcione
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
