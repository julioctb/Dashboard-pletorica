"""
Componentes de Entregables.
Exporta alertas para dashboard, badge para sidebar, y tab de configuración para contratos.
"""

from app.presentation.components.backoffice.entregables.alertas_section import (
    AlertasEntregablesState,
    alertas_entregables_card,
    alertas_entregables_badge,
    seccion_alertas_dashboard,
)

from app.presentation.components.backoffice.entregables.entregables_config_tab import (
    tab_entregables_config,
    seccion_entregables_contrato,
)

__all__ = [
    "AlertasEntregablesState",
    "alertas_entregables_card",
    "alertas_entregables_badge",
    "seccion_alertas_dashboard",
    "tab_entregables_config",
    "seccion_entregables_contrato",
]
