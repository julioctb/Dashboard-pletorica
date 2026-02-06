"""Componentes genéricos de UI reutilizables"""

from .headers import page_header
from .form_input import form_input, form_select, form_textarea, form_date, form_row
from .badges import estatus_badge
from .tables import tabla_vacia, tabla
from .skeletons import skeleton_tabla
from .filters import (
    input_busqueda,
    indicador_filtros,
    contador_registros,
    switch_inactivos,
    barra_filtros,
)
from .modals import (
    modal_confirmar_eliminar,
    modal_confirmar_accion,
    modal_formulario,
    modal_detalle,
)

from .status_badge import (
    status_badge,
    status_badge_reactive,
)

from .view_toggle import (
    view_toggle,
)

from .breadcrumb import (
    breadcrumb_dynamic,
)

from .action_buttons import (
    action_buttons,
    action_button_config,
    action_buttons_reactive,
)

from .entity_card import (
    entity_card,
    entity_grid,
)


__all__ = [
    'page_header',
    # formularios
    'form_input',
    'form_select',
    'form_textarea',
    'form_date',
    'form_row',
    'estatus_badge',
    # tablas
    'tabla_vacia',
    'tabla',
    'skeleton_tabla',
    # filtros
    'input_busqueda',
    'indicador_filtros',
    'contador_registros',
    'switch_inactivos',
    'barra_filtros',
    # modales
    'modal_confirmar_eliminar',
    'modal_confirmar_accion',
    'modal_formulario',
    'modal_detalle',
    # Status badges
    "status_badge",
    "status_badge_reactive",
    # View toggle
    "view_toggle",
    # Breadcrumb
    "breadcrumb_dynamic",
    # Action buttons
    "action_buttons",
    "action_button_config",
    "action_buttons_reactive",
    # Entity cards
    "entity_card",
    "entity_grid",
]
