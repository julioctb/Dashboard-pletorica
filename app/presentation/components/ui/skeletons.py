"""
TODO: Componentes de skeleton para estados de carga

PENDIENTE: Implementar skeletons para mejorar UX durante cargas

Componentes a crear:
- skeleton_box(): Caja base con animación de pulso
- skeleton_empresa_card(): Skeleton para tarjeta de empresa
- skeleton_empresa_grid(): Grid de skeletons (6 cards por defecto)
- skeleton_form_field(): Skeleton para campo de formulario
- skeleton_modal_form(): Skeleton para formulario completo en modal
- skeleton_detail_card(): Skeleton para tarjeta de detalles
- skeleton_table_row(): Skeleton para fila de tabla
- skeleton_table(): Skeleton para tabla completa

CSS necesario (añadir a assets/):
.skeleton-pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

Uso previsto:
- empresa_grid.py: Mostrar skeleton_empresa_grid() mientras loading=True
- empresa_modals.py: Mostrar skeleton_modal_form() mientras carga datos para editar
- Otros módulos: Reutilizar skeletons para empleados, sedes, nóminas

Prioridad: Media (Nice to have)
Estimado: 2-3 horas de implementación
"""
import reflex as rx


# TODO: Implementar componentes skeleton cuando sea necesario
def skeleton_placeholder() -> rx.Component:
    """Placeholder temporal - implementar skeletons reales"""
    return rx.fragment()
