import reflex as rx
from app.presentation.components.ui.cards import base_card
from app.entities import EmpresaResumen, TipoEmpresa, EstatusEmpresa

def empresa_card(empresa: EmpresaResumen, on_view: callable, on_edit: callable) -> rx.Component:
    """
    Tarjeta específica para mostrar información de una empresa
    
    Args:
        empresa: Objeto EmpresaResumen con datos de la empresa
        on_view: Función para ver detalles de la empresa
        on_edit: Función para editar la empresa
    """
    
    # Badge para tipo de empresa con colores específicos
    tipo_badge = rx.badge(
        empresa.tipo_empresa,
        color_scheme=rx.cond(
            empresa.tipo_empresa == TipoEmpresa.NOMINA,
            "blue",
            "green"
        )
    )
    
    # Contenido principal de la tarjeta
    content = rx.vstack(
        # Información de contacto
        rx.hstack(
            rx.icon("phone", size=16, color="var(--gray-9)"),
            rx.text(
                empresa.contacto_principal,
                size="2",
                color="var(--gray-9)"
            ),
            spacing="2",
            align="center"
        ),
        spacing="2",
        align="start"
    )
    
    # Acciones de la tarjeta
    actions = rx.hstack(
        rx.badge(
            empresa.estatus,
            color_scheme=get_estatus_color(empresa.estatus)
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.icon("eye", size=14),
                size="1",
                variant="soft",
                on_click=lambda: on_view(empresa.id)
            ),
            rx.button(
                rx.icon("pencil", size=14),
                size="1",
                variant="soft",
                on_click=lambda: on_edit(empresa.id)
            ),
            spacing="1"
        ),
        width="100%",
        align="center"
    )
    
    return base_card(
        title=empresa.nombre_comercial,
        subtitle=f"ID: {empresa.id}",
        badge=tipo_badge,
        content=content,
        actions=actions,
        hover_effect=True
    )

def get_estatus_color(estatus: EstatusEmpresa) -> str:
    """
    Retorna el color scheme apropiado para cada estatus
    
    Args:
        estatus: EstatusEmpresa enum
    
    Returns:
        Color scheme string para el badge
    """
    color_map = {
        EstatusEmpresa.ACTIVO: "green",
        EstatusEmpresa.SUSPENDIDO: "yellow", 
        EstatusEmpresa.INACTIVO: "red"
    }
    return color_map.get(estatus, "gray")

def empresa_info_content(empresa: EmpresaResumen) -> rx.Component:
    """
    Contenido de información extendida para la empresa
    Útil para modales de detalle
    
    Args:
        empresa: Objeto EmpresaResumen
    """
    
    return rx.vstack(
        # Información básica
        rx.hstack(
            rx.icon("building-2", size=16, color="var(--gray-9)"),
            rx.text(f"Tipo: {empresa.tipo_empresa}", size="2"),
            spacing="2",
            align="center"
        ),
        
        # Contacto
        rx.hstack(
            rx.icon("phone", size=16, color="var(--gray-9)"),
            rx.text(f"Contacto: {empresa.contacto_principal}", size="2"),
            spacing="2",
            align="center"
        ),
        
        # Fecha de creación
        rx.hstack(
            rx.icon("calendar", size=16, color="var(--gray-9)"),
            rx.text(
                f"Creada: {empresa.fecha_creacion.strftime('%d/%m/%Y') if empresa.fecha_creacion else 'N/A'}",
                size="2"
            ),
            spacing="2",
            align="center"
        ),
        
        spacing="2",
        align="start"
    )

def empresa_actions(empresa: EmpresaResumen, state_methods: dict) -> rx.Component:
    """
    Componente de acciones para la empresa
    
    Args:
        empresa: Objeto EmpresaResumen
        state_methods: Dict con métodos del state {
            'on_view': función,
            'on_edit': función,
            'on_change_status': función
        }
    """
    
    return rx.hstack(
        # Estatus actual
        rx.badge(
            empresa.estatus,
            color_scheme=get_estatus_color(empresa.estatus)
        ),
        
        rx.spacer(),
        
        # Menú de acciones
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.icon("more-horizontal", size=14),
                    size="1",
                    variant="soft"
                )
            ),
            rx.menu.content(
                rx.menu.item(
                    rx.icon("eye", size=14),
                    "Ver detalles",
                    on_click=lambda: state_methods['on_view'](empresa.id)
                ),
                rx.menu.item(
                    rx.icon("pencil", size=14),
                    "Editar",
                    on_click=lambda: state_methods['on_edit'](empresa.id)
                ),
                rx.menu.separator(),
                rx.cond(
                    empresa.estatus == EstatusEmpresa.ACTIVO,
                    rx.menu.item(
                        rx.icon("pause", size=14),
                        "Suspender",
                        on_click=lambda: state_methods['on_change_status'](
                            empresa.id, 
                            EstatusEmpresa.SUSPENDIDO
                        )
                    ),
                    rx.menu.item(
                        rx.icon("play", size=14),
                        "Activar",
                        on_click=lambda: state_methods['on_change_status'](
                            empresa.id, 
                            EstatusEmpresa.ACTIVO
                        )
                    )
                )
            )
        ),
        
        spacing="2",
        align="center"
    )

def empresa_summary_card(
    total_empresas: int,
    empresas_activas: int,
    empresas_nomina: int,
    empresas_mantenimiento: int
) -> rx.Component:
    """
    Tarjeta de resumen/estadísticas de empresas
    
    Args:
        total_empresas: Total de empresas
        empresas_activas: Empresas activas
        empresas_nomina: Empresas de nómina
        empresas_mantenimiento: Empresas de mantenimiento
    """
    
    content = rx.grid(
        # Total
        rx.vstack(
            rx.text("Total", size="2", color="var(--gray-9)"),
            rx.text(str(total_empresas), size="4", weight="bold"),
            align="center"
        ),
        
        # Activas
        rx.vstack(
            rx.text("Activas", size="2", color="var(--gray-9)"),
            rx.text(str(empresas_activas), size="4", weight="bold", color="var(--green-9)"),
            align="center"
        ),
        
        # Nómina
        rx.vstack(
            rx.text("Nómina", size="2", color="var(--gray-9)"),
            rx.text(str(empresas_nomina), size="4", weight="bold", color="var(--blue-9)"),
            align="center"
        ),
        
        # Mantenimiento
        rx.vstack(
            rx.text("Mantenimiento", size="2", color="var(--gray-9)"),
            rx.text(str(empresas_mantenimiento), size="4", weight="bold", color="var(--green-9)"),
            align="center"
        ),
        
        columns="4",
        spacing="4"
    )
    
    return base_card(
        title="Resumen de Empresas",
        content=content,
        icon=rx.icon("bar-chart-3", size=20, color="var(--blue-9)"),
        hover_effect=False
    )