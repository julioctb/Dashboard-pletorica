"""Componentes UI del módulo de Requisiciones."""

from core.presentation.components.backoffice.requisiciones.requisicion_tabla import requisicion_tabla
from core.presentation.components.backoffice.requisiciones.requisicion_form import requisicion_form_modal
from core.presentation.components.backoffice.requisiciones.requisicion_estado_badge import estado_requisicion_badge

__all__ = [
    "requisicion_tabla",
    "requisicion_form_modal",
    "estado_requisicion_badge",
]
