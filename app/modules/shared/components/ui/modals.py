import reflex as rx
from typing import Optional, Any, List

def base_modal(
    title: str,
    content: rx.Component,
    footer_actions: rx.Component,
    open_state: bool,
    on_open_change: Any,
    description: Optional[str] = None,
    max_width: str = "600px",
    icon: Optional[str] = None
) -> rx.Component:
    """
    Modal base reutilizable para todo el sistema
    
    Args:
        title: Título del modal
        description: Descripción opcional
        content: Contenido principal del modal
        footer_actions: Botones de acción en el footer
        open_state: Estado de apertura (boolean)
        on_open_change: Función para cambiar estado
        max_width: Ancho máximo del modal
        icon: Icono opcional para el título
    """
    
    return rx.dialog.root(
        rx.dialog.content(
            # Header del modal
            rx.hstack(
                rx.cond(
                    icon,
                    rx.icon(icon, size=24, color="var(--blue-9)")
                ),
                rx.vstack(
                    rx.dialog.title(title),
                    rx.cond(
                        description,
                        rx.dialog.description(description)
                    ),
                    align="start",
                    spacing="1"
                ),
                spacing="3",
                align="center",
                width="100%"
            ),
            
            # Contenido principal
            content,
            
            # Footer con acciones
            footer_actions,
            
            max_width=max_width,
            spacing="4"
        ),
        open=open_state,
        on_open_change=on_open_change
    )

def confirmation_modal(
    title: str,
    message: str,
    on_confirm: Any,
    on_cancel: Any,
    open_state: bool,
    on_open_change: Any,
    confirm_text: str = "Confirmar",
    cancel_text: str = "Cancelar",
    danger: bool = False,
    icon: Optional[str] = None
) -> rx.Component:
    """
    Modal de confirmación para acciones críticas
    
    Args:
        title: Título del modal
        message: Mensaje de confirmación
        confirm_text: Texto del botón de confirmar
        cancel_text: Texto del botón de cancelar
        on_confirm: Función al confirmar
        on_cancel: Función al cancelar
        open_state: Estado de apertura
        on_open_change: Función para cambiar estado
        danger: Si es una acción peligrosa (botón rojo)
        icon: Icono opcional
    """
    
    # Contenido del modal
    content = rx.vstack(
        rx.text(message, size="3", text_align="center"),
        spacing="3",
        align="center",
        padding="4"
    )
    
    # Botones de acción
    footer_actions = rx.hstack(
        rx.dialog.close(
            rx.button(
                cancel_text,
                variant="soft",
                size="2",
                on_click=on_cancel
            )
        ),
        rx.button(
            confirm_text,
            on_click=on_confirm,
            size="2",
            color_scheme="red" if danger else "blue"
        ),
        spacing="2",
        justify="end"
    )
    
    return base_modal(
        title=title,
        content=content,
        footer_actions=footer_actions,
        open_state=open_state,
        on_open_change=on_open_change,
        max_width="400px",
        icon=icon or ("alert-triangle" if danger else "help-circle")
    )

def form_modal(
    title: str,
    form_fields: List[rx.Component],
    on_submit: Any,
    on_cancel: Any,
    open_state: bool,
    on_open_change: Any,
    description: Optional[str] = None,
    submit_text: str = "Guardar",
    cancel_text: str = "Cancelar",
    max_width: str = "600px",
    icon: Optional[str] = None,
    loading: bool = False
) -> rx.Component:
    """
    Modal con formulario reutilizable
    
    Args:
        title: Título del modal
        description: Descripción opcional
        form_fields: Lista de campos del formulario
        submit_text: Texto del botón de envío
        cancel_text: Texto del botón de cancelar
        on_submit: Función al enviar
        on_cancel: Función al cancelar
        open_state: Estado de apertura
        on_open_change: Función para cambiar estado
        max_width: Ancho máximo
        icon: Icono opcional
        loading: Si mostrar estado de carga
    """
    
    # Contenido del formulario
    content = rx.vstack(
        *form_fields,
        spacing="3",
        width="100%"
    )
    
    # Botones de acción
    footer_actions = rx.hstack(
        rx.dialog.close(
            rx.button(
                cancel_text,
                variant="soft",
                size="2",
                on_click=on_cancel,
                disabled=loading
            )
        ),
        rx.button(
            rx.cond(
                loading,
                rx.hstack(
                    rx.spinner(size="1"),
                    submit_text,
                    spacing="2"
                ),
                submit_text
            ),
            on_click=on_submit,
            size="2",
            disabled=loading
        ),
        spacing="2",
        justify="end"
    )
    
    return base_modal(
        title=title,
        description=description,
        content=content,
        footer_actions=footer_actions,
        open_state=open_state,
        on_open_change=on_open_change,
        max_width=max_width,
        icon=icon
    )

def detail_modal(
    title: str,
    open_state: bool,
    on_open_change: Any,
    sections: List[rx.Component],
    actions: Optional[rx.Component] = None,
    max_width: str = "500px",
    icon: Optional[str] = None
) -> rx.Component:
    """
    Modal para mostrar detalles/información
    
    Args:
        title: Título del modal
        sections: Lista de secciones de contenido
        actions: Botones de acción opcionales
        open_state: Estado de apertura
        on_open_change: Función para cambiar estado
        max_width: Ancho máximo
        icon: Icono opcional
    """
    
    # Contenido principal
    content = rx.vstack(
        *sections,
        spacing="4",
        width="100%"
    )
    
    # Footer con acciones
    footer_actions = rx.hstack(
        rx.dialog.close(
            rx.button("Cerrar", variant="soft", size="2")
        ),
        rx.cond(actions, actions),
        spacing="2",
        justify="end"
    )
    
    return base_modal(
        title=title,
        content=content,
        footer_actions=footer_actions,
        open_state=open_state,
        on_open_change=on_open_change,
        max_width=max_width,
        icon=icon
    )

def trigger_modal(
    trigger_component: rx.Component,
    modal_component: rx.Component
) -> rx.Component:
    """
    Modal con trigger integrado (botón que abre el modal)
    
    Args:
        trigger_component: Componente que activa el modal (botón, link, etc)
        modal_component: El modal a mostrar
    """
    
    return rx.dialog.root(
        rx.dialog.trigger(trigger_component),
        modal_component
    )

def section_card(
    title: str,
    fields: List[tuple],  # [(label, value), ...]
    icon: Optional[str] = None
) -> rx.Component:
    """
    Tarjeta de sección para usar dentro de modales de detalle
    
    Args:
        title: Título de la sección
        fields: Lista de tuplas (label, value)
        icon: Icono opcional
    """
    
    return rx.card(
        rx.vstack(
            # Header de la sección
            rx.hstack(
                rx.cond(icon, rx.icon(icon, size=20)),
                rx.text(title, weight="bold", size="4"),
                spacing="2",
                align="center"
            ),
            
            # Campos de la sección
            rx.grid(
                *[
                    rx.vstack(
                        rx.text(f"{label}:", weight="bold", size="2"),
                        rx.text(str(value), size="2"),
                        align="start"
                    )
                    for label, value in fields
                ],
                columns="2",
                spacing="4"
            ),
            
            spacing="3",
            align="start"
        )
    )

def form_section(
    title: str,
    fields: List[rx.Component],
    icon: Optional[str] = None
) -> rx.Component:
    """
    Sección de formulario para organizar campos
    
    Args:
        title: Título de la sección
        fields: Lista de campos del formulario
        icon: Icono opcional
    """
    
    return rx.vstack(
        # Header de la sección
        rx.hstack(
            rx.cond(icon, rx.icon(icon, size=18)),
            rx.text(title, weight="bold", size="3"),
            spacing="2",
            align="center"
        ),
        
        # Campos de la sección
        rx.vstack(
            *fields,
            spacing="3",
            width="100%"
        ),
        
        spacing="3",
        width="100%"
    )

def quick_action_modal(
    title: str,
    message: str,
    action_text: str,
    on_action: Any,
    trigger_text: str,
    trigger_icon: str = "plus",
    color_scheme: str = "blue"
) -> rx.Component:
    """
    Modal de acción rápida con trigger integrado
    
    Args:
        title: Título del modal
        message: Mensaje explicativo
        action_text: Texto del botón de acción
        on_action: Función a ejecutar
        trigger_text: Texto del botón trigger
        trigger_icon: Icono del botón trigger
        color_scheme: Esquema de colores
    """
    
    trigger = rx.button(
        rx.icon(trigger_icon, size=16),
        trigger_text,
        size="2",
        color_scheme=color_scheme
    )
    
    modal_content = rx.dialog.content(
        rx.dialog.title(title),
        
        rx.vstack(
            rx.text(message, size="3", text_align="center"),
            spacing="3",
            align="center",
            padding="4"
        ),
        
        rx.hstack(
            rx.dialog.close(
                rx.button("Cancelar", variant="soft", size="2")
            ),
            rx.dialog.close(
                rx.button(
                    action_text,
                    on_click=on_action,
                    size="2",
                    color_scheme=color_scheme
                )
            ),
            spacing="2",
            justify="end"
        ),
        
        max_width="400px",
        spacing="4"
    )
    
    return trigger_modal(trigger, modal_content)