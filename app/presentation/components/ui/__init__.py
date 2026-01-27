"""Componentes genéricos de UI reutilizables"""

from .headers import page_header
from .form_input import form_input, form_select, form_textarea, form_date, form_row
from .buttons import boton_accion, acciones_crud
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
from .barra_herramientas import barra_herramientas
from .modals import (
    modal_confirmar_eliminar,
    modal_confirmar_accion,
    modal_formulario,
    modal_detalle,
)

from .status_badge import (
    status_badge,
    status_badge_contrato,
    status_badge_entidad,
    status_badge_plaza,
    status_badge_reactive,
    status_dot,
)

from .view_toggle import (
    view_toggle,
    view_toggle_with_label,
    view_toggle_segmented,
)

from .breadcrumb import (
    breadcrumb,
    breadcrumb_dynamic,
    breadcrumb_item,
)


__all__ = [
    'page_header',
    'form_input',
    'form_select',
    'form_textarea',
    'form_date',
    'form_row',
    'boton_accion',
    'acciones_crud',
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
    'barra_herramientas',
    # modales
    'modal_confirmar_eliminar',
    'modal_confirmar_accion',
    'modal_formulario',
    'modal_detalle',
     # Status badges
    "status_badge",
    "status_badge_contrato",
    "status_badge_entidad",
    "status_badge_plaza",
    "status_badge_reactive",
    "status_dot",
    
    # View toggle
    "view_toggle",
    "view_toggle_with_label",
    "view_toggle_segmented",
    # Breadcrumb
    "breadcrumb",
    "breadcrumb_dynamic",
    "breadcrumb_item",
]
