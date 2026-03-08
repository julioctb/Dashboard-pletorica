"""
Modales para el módulo de Contratos.
"""
import reflex as rx
from app.presentation.components.ui.form_input import form_input, form_select, form_textarea, form_date
from app.presentation.components.ui import (
    status_badge_reactive,
    boton_guardar,
    boton_cancelar,
    boton_eliminar,
    empty_state_card,
    feedback_callout,
    metric_card,
    table_shell,
)
from app.presentation.pages.contratos.contratos_state import ContratosState
from app.presentation.theme import Colors, Radius, Spacing, Typography


def _tarjeta_paso(
    titulo: str,
    descripcion: str,
    contenido: rx.Component,
) -> rx.Component:
    """Contenedor visual consistente para cada paso del wizard."""
    return rx.card(
        rx.vstack(
            rx.vstack(
                rx.text(titulo, size="4", weight="bold", color=Colors.TEXT_PRIMARY),
                rx.text(descripcion, size="2", color=Colors.TEXT_SECONDARY),
                spacing="1",
                width="100%",
                align="start",
            ),
            rx.separator(),
            contenido,
            spacing="4",
            width="100%",
            align="stretch",
        ),
        width="100%",
        variant="surface",
    )


def _indicador_pasos() -> rx.Component:
    """Indicador compacto del wizard de contratos."""

    def _paso(numero: int, titulo: str) -> rx.Component:
        es_activo = ContratosState.form_paso_actual >= numero
        es_actual = ContratosState.form_paso_actual == numero

        return rx.hstack(
            rx.center(
                rx.text(
                    str(numero),
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_BOLD,
                ),
                width="32px",
                height="32px",
                border_radius="999px",
                background=rx.cond(es_activo, Colors.PRIMARY, Colors.SECONDARY_LIGHT),
                color=rx.cond(es_activo, Colors.TEXT_INVERSE, Colors.TEXT_SECONDARY),
                border=f"1px solid {Colors.BORDER}",
                cursor="pointer",
                flex_shrink="0",
                on_click=ContratosState.set_form_paso_actual(numero),
            ),
            rx.text(
                titulo,
                size="2",
                weight=rx.cond(es_actual, "bold", "medium"),
                color=rx.cond(es_activo, Colors.TEXT_PRIMARY, Colors.TEXT_MUTED),
            ),
            spacing="2",
            align="center",
        )

    def _conector() -> rx.Component:
        return rx.box(
            flex="1",
            min_width="24px",
            height="1px",
            background=Colors.BORDER,
        )

    pasos_dos = rx.hstack(
        _paso(1, "Datos"),
        _conector(),
        _paso(2, "Plazas"),
        width="100%",
        justify="center",
        align="center",
        spacing="3",
    )

    pasos_tres = rx.hstack(
        _paso(1, "Datos"),
        _conector(),
        _paso(2, "Plazas"),
        _conector(),
        _paso(3, "Entregables"),
        width="100%",
        justify="center",
        align="center",
        spacing="3",
    )

    return rx.vstack(
        rx.cond(ContratosState.mostrar_paso_entregables, pasos_tres, pasos_dos),
        rx.text(
            ContratosState.titulo_paso_actual_wizard,
            size="2",
            weight="medium",
            color=Colors.TEXT_PRIMARY,
            width="100%",
            text_align="center",
        ),
        spacing="3",
        width="100%",
        padding_y=Spacing.XS,
    )


def _paso_contrato() -> rx.Component:
    """Paso 1: datos principales del contrato."""
    empresa_field = rx.cond(
        ContratosState.empresa_fijada_en_contexto,
        form_input(
            label="Empresa",
            required=True,
            value=ContratosState.nombre_empresa_formulario,
            error=ContratosState.error_empresa_id,
            hint="Se usa la empresa precargada para este contrato.",
            disabled=True,
        ),
        form_select(
            label="Empresa",
            required=True,
            placeholder="Seleccione empresa",
            value=ContratosState.form_empresa_id,
            on_change=ContratosState.set_form_empresa_id,
            options=ContratosState.opciones_empresa,
            error=ContratosState.error_empresa_id,
            hint="Se precarga desde el contexto activo cuando está disponible.",
        ),
    )

    return _tarjeta_paso(
        "Datos del contrato",
        "Capture la información base y la vigencia del contrato.",
        rx.vstack(
            rx.hstack(
                empresa_field,
                form_select(
                    label="Tipo de contrato",
                    required=True,
                    placeholder="Seleccione tipo",
                    value=ContratosState.form_tipo_contrato,
                    on_change=ContratosState.set_form_tipo_contrato,
                    options=ContratosState.opciones_tipo_contrato,
                    error=ContratosState.error_tipo_contrato,
                ),
                spacing="3",
                width="100%",
                align="start",
            ),
            rx.cond(
                ContratosState.es_servicios,
                rx.hstack(
                    form_input(
                        label="Folio BUAP",
                        placeholder="Ej: BUAP-2026-001",
                        value=ContratosState.form_folio_buap,
                        on_change=ContratosState.set_form_folio_buap,
                        on_blur=ContratosState.validar_folio_buap_campo,
                        error=ContratosState.error_folio_buap,
                    ),
                    form_select(
                        label="Tipo de servicio",
                        required=True,
                        placeholder="Seleccione tipo de servicio",
                        value=ContratosState.form_tipo_servicio_id,
                        on_change=ContratosState.set_form_tipo_servicio_id,
                        options=ContratosState.opciones_tipo_servicio,
                        error=ContratosState.error_tipo_servicio_id,
                    ),
                    spacing="3",
                    width="100%",
                    align="start",
                ),
                form_input(
                    label="Folio BUAP",
                    placeholder="Ej: BUAP-2026-001",
                    value=ContratosState.form_folio_buap,
                    on_change=ContratosState.set_form_folio_buap,
                    on_blur=ContratosState.validar_folio_buap_campo,
                    error=ContratosState.error_folio_buap,
                ),
            ),
            rx.hstack(
                form_date(
                    label="Fecha de inicio",
                    required=True,
                    value=ContratosState.form_fecha_inicio,
                    on_change=ContratosState.set_form_fecha_inicio,
                    on_blur=ContratosState.validar_fecha_inicio_campo,
                    error=ContratosState.error_fecha_inicio,
                ),
                form_date(
                    label="Fecha fin",
                    value=ContratosState.form_fecha_fin,
                    on_change=ContratosState.set_form_fecha_fin,
                    on_blur=ContratosState.validar_fecha_fin_campo,
                    error=ContratosState.error_fecha_fin,
                    hint="Si la deja vacía, el contrato se tomará como indefinido.",
                ),
                spacing="3",
                width="100%",
                align="start",
            ),
            rx.box(
                rx.hstack(
                    rx.text("Vigencia:", size="2", weight="medium", color=Colors.TEXT_PRIMARY),
                    rx.badge(
                        ContratosState.vigencia_formulario_label,
                        color_scheme=ContratosState.vigencia_formulario_color_scheme,
                        variant="soft",
                        size="2",
                    ),
                    rx.text(
                        "Depende de la fecha fin respecto a la fecha actual.",
                        size="1",
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="3",
                    align="center",
                    wrap="wrap",
                ),
                padding=Spacing.SM,
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.MD,
                background=Colors.SECONDARY_LIGHT,
                width="100%",
            ),
            form_textarea(
                label="Descripción del objeto",
                required=True,
                placeholder="Ej: Servicio integral de limpieza en instalaciones administrativas.",
                value=ContratosState.form_descripcion_objeto,
                on_change=ContratosState.set_form_descripcion_objeto,
                on_blur=ContratosState.sync_form_descripcion_objeto_blur,
                error=ContratosState.error_descripcion_objeto,
                rows="4",
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.checkbox(
                            "Incluye personal",
                            checked=ContratosState.form_tiene_personal,
                            on_change=ContratosState.set_form_tiene_personal,
                            disabled=ContratosState.es_adquisicion,
                        ),
                        align="center",
                        spacing="3",
                    ),
                    rx.text(
                        rx.cond(
                            ContratosState.es_adquisicion,
                            "Los contratos de adquisición no generan plazas.",
                            "Active esta opción si el contrato debe materializar plazas.",
                        ),
                        size="1",
                        color=Colors.TEXT_SECONDARY,
                    ),
                    spacing="1",
                    align="start",
                    width="100%",
                ),
                padding=Spacing.SM,
                border=f"1px solid {Colors.BORDER}",
                border_radius=Radius.MD,
                background=Colors.SECONDARY_LIGHT,
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
    )


def _paso_plazas() -> rx.Component:
    """Paso 2: configuración de plazas."""
    plazas_habilitadas = ContratosState.es_servicios & ContratosState.form_tiene_personal
    totales_bloqueados = ContratosState.usa_desglose_categorias_plazas
    puede_configurar_desglose = plazas_habilitadas & (ContratosState.form_tipo_servicio_id != "")

    return _tarjeta_paso(
        "Plazas",
        "Defina el rango total de plazas o desglose el personal por categoría.",
        rx.vstack(
            feedback_callout(
                rx.cond(
                    plazas_habilitadas,
                    "Puede usar un rango global o un desglose por categoría. Si agrega categorías, los totales y montos del contrato se calculan automáticamente.",
                    "Este contrato no generará plazas mientras 'Incluye personal' esté desactivado.",
                ),
                "info",
            ),
            rx.hstack(
                rx.card(
                    rx.vstack(
                        rx.text("Total mínimo", size="1", color=Colors.TEXT_SECONDARY),
                        rx.text(
                            rx.cond(
                                ContratosState.form_cantidad_plazas_minima != "",
                                ContratosState.form_cantidad_plazas_minima,
                                "0",
                            ),
                            size="6",
                            weight="bold",
                            color=Colors.TEXT_PRIMARY,
                        ),
                        rx.text(
                            rx.cond(
                                totales_bloqueados,
                                "Derivado del desglose por categoría",
                                "Configuración global del contrato",
                            ),
                            size="1",
                            color=Colors.TEXT_MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Total máximo", size="1", color=Colors.TEXT_SECONDARY),
                        rx.text(
                            rx.cond(
                                ContratosState.form_cantidad_plazas_maxima != "",
                                ContratosState.form_cantidad_plazas_maxima,
                                "0",
                            ),
                            size="6",
                            weight="bold",
                            color=Colors.TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Sincroniza la materialización de plazas vacantes",
                            size="1",
                            color=Colors.TEXT_MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    width="100%",
                    variant="surface",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            rx.hstack(
                rx.card(
                    rx.vstack(
                        rx.text("Monto mínimo", size="1", color=Colors.TEXT_SECONDARY),
                        rx.text(
                            rx.cond(
                                ContratosState.form_monto_minimo != "",
                                ContratosState.form_monto_minimo,
                                "$ 0",
                            ),
                            size="5",
                            weight="bold",
                            color=Colors.TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Suma de costo x plazas mínimas por categoría",
                            size="1",
                            color=Colors.TEXT_MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    width="100%",
                    variant="surface",
                ),
                rx.card(
                    rx.vstack(
                        rx.text("Monto máximo", size="1", color=Colors.TEXT_SECONDARY),
                        rx.text(
                            rx.cond(
                                ContratosState.form_monto_maximo != "",
                                ContratosState.form_monto_maximo,
                                "$ 0",
                            ),
                            size="5",
                            weight="bold",
                            color=Colors.TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Suma de costo x plazas máximas por categoría",
                            size="1",
                            color=Colors.TEXT_MUTED,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    width="100%",
                    variant="surface",
                ),
                spacing="3",
                width="100%",
                align="stretch",
            ),
            rx.hstack(
                form_input(
                    label="Plazas mínimas",
                    required=plazas_habilitadas,
                    placeholder="0",
                    value=ContratosState.form_cantidad_plazas_minima,
                    on_change=ContratosState.set_form_cantidad_plazas_minima,
                    on_blur=ContratosState.validar_cantidad_plazas_minima_campo,
                    error=ContratosState.error_cantidad_plazas_minima,
                    type="number",
                    min="0",
                    disabled=(~plazas_habilitadas) | totales_bloqueados,
                    hint=rx.cond(
                        totales_bloqueados,
                        "Se calcula automáticamente desde las categorías capturadas abajo.",
                        "Capture el total mínimo si no desea desglosarlo por categoría.",
                    ),
                ),
                form_input(
                    label="Plazas máximas",
                    required=plazas_habilitadas,
                    placeholder="0",
                    value=ContratosState.form_cantidad_plazas_maxima,
                    on_change=ContratosState.set_form_cantidad_plazas_maxima,
                    on_blur=ContratosState.validar_cantidad_plazas_maxima_campo,
                    error=ContratosState.error_cantidad_plazas_maxima,
                    hint="Debe ser mayor o igual que el mínimo.",
                    type="number",
                    min="0",
                    disabled=(~plazas_habilitadas) | totales_bloqueados,
                ),
                spacing="3",
                width="100%",
                align="start",
            ),
            rx.separator(),
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("Desglose por categoría", size="3", weight="bold"),
                        rx.text(
                            "Asigne plazas mínimas y máximas por perfil operativo.",
                            size="1",
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.cond(
                        plazas_habilitadas,
                        rx.cond(
                            ContratosState.mostrar_form_nueva_categoria,
                            boton_cancelar(
                                texto="Usar catálogo",
                                size="1",
                                on_click=ContratosState.ocultar_form_crear_categoria_contrato,
                            ),
                            boton_cancelar(
                                texto="Nueva categoría",
                                size="1",
                                on_click=ContratosState.mostrar_form_crear_categoria_contrato,
                            ),
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    plazas_habilitadas,
                    rx.cond(
                        puede_configurar_desglose,
                        rx.vstack(
                            rx.cond(
                                ContratosState.mostrar_form_nueva_categoria,
                                rx.vstack(
                                    feedback_callout(
                                        "La nueva categoría se creará dentro del tipo de servicio seleccionado y quedará disponible para futuros contratos.",
                                        "info",
                                    ),
                                    rx.hstack(
                                        form_input(
                                            label="Nombre de categoría",
                                            required=True,
                                            placeholder="Ej: JARDINERO A",
                                            value=ContratosState.form_nueva_categoria_nombre,
                                            on_change=ContratosState.set_form_nueva_categoria_nombre,
                                            error=ContratosState.error_nueva_categoria_nombre,
                                        ),
                                        form_input(
                                            label="Clave",
                                            required=True,
                                            placeholder="Ej: JARA",
                                            value=ContratosState.form_nueva_categoria_clave,
                                            on_change=ContratosState.set_form_nueva_categoria_clave,
                                            error=ContratosState.error_nueva_categoria_clave,
                                            max_length=5,
                                        ),
                                        spacing="3",
                                        width="100%",
                                        align="start",
                                    ),
                                    spacing="3",
                                    width="100%",
                                ),
                                form_select(
                                    label="Categoría",
                                    required=True,
                                    placeholder="Seleccione categoría",
                                    value=ContratosState.form_categoria_puesto_id,
                                    on_change=ContratosState.set_form_categoria_puesto_id,
                                    options=ContratosState.opciones_categoria_puesto_para_contrato,
                                    error=ContratosState.error_categoria_contrato_id,
                                    hint="Solo se muestran categorías activas del tipo de servicio seleccionado.",
                                ),
                            ),
                            rx.hstack(
                                form_input(
                                    label="Plazas mínimas",
                                    required=True,
                                    placeholder="0",
                                    value=ContratosState.form_categoria_contrato_minima,
                                    on_change=ContratosState.set_form_categoria_contrato_minima,
                                    error=ContratosState.error_categoria_contrato_minima,
                                    type="number",
                                    min="0",
                                ),
                                form_input(
                                    label="Plazas máximas",
                                    required=True,
                                    placeholder="0",
                                    value=ContratosState.form_categoria_contrato_maxima,
                                    on_change=ContratosState.set_form_categoria_contrato_maxima,
                                    error=ContratosState.error_categoria_contrato_maxima,
                                    type="number",
                                    min="0",
                                ),
                                form_input(
                                    label="Costo por categoría",
                                    required=True,
                                    placeholder="0.00",
                                    value=ContratosState.form_categoria_contrato_costo,
                                    on_change=ContratosState.set_form_categoria_contrato_costo,
                                    error=ContratosState.error_categoria_contrato_costo,
                                    hint="Costo contractual por persona/mes. No se copia al salario de la plaza.",
                                ),
                                rx.box(
                                    boton_guardar(
                                        texto=rx.cond(
                                            ContratosState.mostrar_form_nueva_categoria,
                                            "Crear y agregar",
                                            "Agregar categoría",
                                        ),
                                        texto_guardando="Agregando...",
                                        on_click=ContratosState.agregar_categoria_contrato,
                                        saving=ContratosState.guardando_categoria_contrato,
                                        disabled=~ContratosState.puede_agregar_categoria_contrato,
                                        variant="soft",
                                        size="2",
                                    ),
                                    padding_top="26px",
                                ),
                                spacing="3",
                                width="100%",
                                align="start",
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        feedback_callout(
                            "Seleccione el tipo de servicio en el paso Datos para habilitar el catálogo de categorías.",
                            "warning",
                        ),
                    ),
                    feedback_callout(
                        "El desglose por categoría solo aplica cuando el contrato de servicios incluye personal.",
                        "warning",
                    ),
                ),
                rx.cond(
                    ContratosState.tiene_categorias_contrato_configuradas,
                    table_shell(
                        loading=False,
                        has_rows=True,
                        empty_component=rx.fragment(),
                        header_cells=[
                            rx.table.column_header_cell("Clave", width="90px"),
                            rx.table.column_header_cell("Categoría"),
                            rx.table.column_header_cell("Mín.", width="80px"),
                            rx.table.column_header_cell("Máx.", width="80px"),
                            rx.table.column_header_cell("Costo", width="120px"),
                            rx.table.column_header_cell("Acciones", width="96px"),
                        ],
                        body_component=rx.foreach(
                            ContratosState.form_categorias_contrato,
                            lambda item: rx.table.row(
                                rx.table.cell(
                                    rx.badge(
                                        item["categoria_clave"],
                                        color_scheme="blue",
                                        variant="soft",
                                        size="1",
                                    ),
                                ),
                                rx.table.cell(
                                    rx.text(item["categoria_nombre"], size="2"),
                                ),
                                rx.table.cell(
                                    rx.text(item["cantidad_minima"], size="2"),
                                ),
                                rx.table.cell(
                                    rx.text(item["cantidad_maxima"], size="2"),
                                ),
                                rx.table.cell(
                                    rx.text(
                                        rx.cond(
                                            item["costo_unitario"],
                                            item["costo_unitario"],
                                            "-",
                                        ),
                                        size="2",
                                    ),
                                ),
                                rx.table.cell(
                                    boton_eliminar(
                                        texto="Quitar",
                                        texto_eliminando="Quitar",
                                        on_click=lambda: ContratosState.quitar_categoria_contrato(item["uid"]),
                                        saving=False,
                                        size="1",
                                        variant="soft",
                                    ),
                                ),
                            ),
                        ),
                        table_size="1",
                    ),
                    empty_state_card(
                        title="Sin categorías configuradas",
                        description="Puede dejar solo el total global o capturar un desglose por categoría para derivar automáticamente las plazas mínimas y máximas.",
                        icon="users",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
    )


def _fila_config_entregable(config: dict) -> rx.Component:
    """Fila de tipo de entregable configurado"""
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(config["tipo_label"], weight="medium", size="2"),
                rx.cond(
                    config["requerido"],
                    rx.badge("Requerido", color_scheme="red", size="1"),
                    rx.badge("Opcional", color_scheme="gray", size="1"),
                ),
                spacing="2",
                align="center",
            ),
            rx.text(config["periodicidad_label"], size="1", color=Colors.TEXT_MUTED),
            rx.cond(
                config["descripcion"],
                rx.text(config["descripcion"], size="1", color=Colors.TEXT_SECONDARY),
                rx.fragment(),
            ),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        boton_cancelar(
            texto="Quitar",
            size="1",
            on_click=lambda: ContratosState.eliminar_tipo_entregable(config["tipo_entregable"]),
        ),
        width="100%",
        padding="3",
        background=Colors.SECONDARY_LIGHT,
        border=f"1px solid {Colors.BORDER}",
        border_radius=Radius.MD,
        align="center",
    )


def _paso_entregables() -> rx.Component:
    """Paso 3: configuración inicial de entregables."""
    return _tarjeta_paso(
        "Entregables",
        "Configure los tipos de entregable que el proveedor deberá presentar.",
        rx.vstack(
            feedback_callout(
                "Puede dejar este paso vacío si el contrato no requiere entregables configurables desde el alta.",
                "info",
            ),
            rx.cond(
                ContratosState.tiene_config_entregables,
                rx.vstack(
                    rx.text("Tipos configurados", size="2", weight="bold"),
                    rx.foreach(
                        ContratosState.config_entregables,
                        _fila_config_entregable,
                    ),
                    spacing="2",
                    width="100%",
                ),
                empty_state_card(
                    title="Sin entregables configurados",
                    description="Agregue uno o más tipos si este contrato debe generar entregables periódicos.",
                    icon="files",
                ),
            ),
            rx.separator(),
            rx.vstack(
                rx.text("Agregar tipo de entregable", size="2", weight="bold"),
                rx.hstack(
                    form_select(
                        label="Tipo",
                        required=True,
                        placeholder="Seleccione tipo",
                        value=ContratosState.form_tipo_entregable,
                        on_change=ContratosState.set_form_tipo_entregable,
                        options=ContratosState.opciones_tipo_entregable,
                    ),
                    form_select(
                        label="Periodicidad",
                        required=True,
                        placeholder="Seleccione periodicidad",
                        value=ContratosState.form_periodicidad_entregable,
                        on_change=ContratosState.set_form_periodicidad_entregable,
                        options=ContratosState.opciones_periodicidad_entregable,
                    ),
                    spacing="3",
                    width="100%",
                    align="start",
                ),
                rx.checkbox(
                    "Requerido para aprobar el periodo",
                    checked=ContratosState.form_entregable_requerido,
                    on_change=ContratosState.set_form_entregable_requerido,
                ),
                form_input(
                    label="Descripción personalizada",
                    placeholder="Ej: Fotografías mensuales del servicio",
                    value=ContratosState.form_entregable_descripcion,
                    on_change=ContratosState.set_form_entregable_descripcion,
                ),
                form_textarea(
                    label="Instrucciones para el proveedor",
                    placeholder="Ej: Subir evidencia fechada y con nombre del área atendida.",
                    value=ContratosState.form_entregable_instrucciones,
                    on_change=ContratosState.set_form_entregable_instrucciones,
                    rows="3",
                ),
                boton_guardar(
                    texto="Agregar tipo",
                    texto_guardando="Agregar tipo",
                    on_click=ContratosState.agregar_tipo_entregable,
                    saving=False,
                    disabled=~ContratosState.puede_agregar_entregable,
                    variant="soft",
                    size="2",
                ),
                spacing="3",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
    )


def modal_contrato() -> rx.Component:
    """Modal wizard para crear o editar contratos."""
    contenido_paso = rx.match(
        ContratosState.form_paso_actual,
        (1, _paso_contrato()),
        (2, _paso_plazas()),
        (3, _paso_entregables()),
        _paso_contrato(),
    )

    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.vstack(
                    rx.dialog.title(
                        rx.cond(
                            ContratosState.es_edicion,
                            "Editar Contrato",
                            "Nuevo Contrato",
                        )
                    ),
                    rx.dialog.description(
                        rx.cond(
                            ContratosState.es_edicion,
                            "Actualice la información base y la configuración de plazas.",
                            "Complete el wizard para crear el contrato.",
                        ),
                    ),
                    spacing="1",
                    width="100%",
                    align="start",
                ),
                _indicador_pasos(),
                rx.cond(
                    ContratosState.mensaje_info != "",
                    feedback_callout(
                        ContratosState.mensaje_info,
                        ContratosState.tipo_mensaje,
                    ),
                    rx.fragment(),
                ),
                rx.box(
                    contenido_paso,
                    width="100%",
                    max_height="62vh",
                    overflow_y="auto",
                    padding_right=Spacing.XS,
                ),
                rx.separator(),
                rx.hstack(
                    boton_cancelar(
                        on_click=ContratosState.cerrar_modal_contrato,
                    ),
                    rx.spacer(),
                    rx.cond(
                        ~ContratosState.es_primer_paso_wizard,
                        boton_cancelar(
                            texto="Anterior",
                            on_click=ContratosState.ir_paso_anterior,
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        ContratosState.es_ultimo_paso_wizard,
                        boton_guardar(
                            texto=rx.cond(
                                ContratosState.es_edicion,
                                "Guardar Cambios",
                                "Crear Contrato",
                            ),
                            texto_guardando="Guardando...",
                            on_click=ContratosState.guardar_contrato,
                            saving=ContratosState.saving,
                            disabled=~ContratosState.puede_guardar,
                        ),
                        boton_guardar(
                            texto="Siguiente",
                            texto_guardando="Siguiente",
                            on_click=ContratosState.ir_paso_siguiente,
                            saving=False,
                            disabled=False,
                        ),
                    ),
                    spacing="3",
                    width="100%",
                    align="center",
                ),
                spacing="4",
                width="100%",
                align="stretch",
            ),
            max_width="820px",
            width="95vw",
            padding=Spacing.LG,
        ),
        open=ContratosState.mostrar_modal_contrato,
        on_open_change=rx.noop,
    )


def _detalle_campo(label: str, contenido: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(
            label,
            size="1",
            weight="medium",
            color=Colors.TEXT_SECONDARY,
        ),
        contenido,
        spacing="1",
        align="start",
        width="100%",
    )


def _fila_categoria_detalle(categoria: dict) -> rx.Component:
    return rx.table.row(
        rx.table.cell(
            rx.badge(
                categoria["categoria_clave"],
                color_scheme="blue",
                variant="soft",
                size="1",
            )
        ),
        rx.table.cell(rx.text(categoria["categoria_nombre"], size="2")),
        rx.table.cell(rx.text(categoria["cantidad_minima"], size="2")),
        rx.table.cell(rx.text(categoria["cantidad_maxima"], size="2")),
        rx.table.cell(rx.text(categoria["costo_unitario_fmt"], size="2", weight="medium")),
        rx.table.cell(rx.text(categoria["costo_minimo_fmt"], size="2")),
        rx.table.cell(rx.text(categoria["costo_maximo_fmt"], size="2")),
    )


def _tab_informacion_contrato() -> rx.Component:
    """Pestaña de información del contrato."""
    return rx.vstack(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("Información General", weight="bold", size="4"),
                        rx.text(
                            "Resumen operativo y financiero del contrato.",
                            size="2",
                            color=Colors.TEXT_SECONDARY,
                        ),
                        spacing="1",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.badge(
                        ContratosState.contrato_seleccionado["codigo"],
                        color_scheme="blue",
                        size="2",
                        variant="soft",
                    ),
                    align="center",
                    width="100%",
                ),
                rx.grid(
                    _detalle_campo(
                        "Empresa",
                        rx.text(
                            rx.cond(
                                ContratosState.contrato_seleccionado["nombre_empresa"],
                                ContratosState.contrato_seleccionado["nombre_empresa"],
                                "Sin empresa",
                            ),
                            size="2",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ),
                    _detalle_campo(
                        "Tipo de servicio",
                        rx.text(
                            rx.cond(
                                ContratosState.contrato_seleccionado["nombre_servicio"],
                                ContratosState.contrato_seleccionado["nombre_servicio"],
                                "No aplica",
                            ),
                            size="2",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ),
                    _detalle_campo(
                        "Tipo de contrato",
                        rx.text(
                            ContratosState.contrato_seleccionado["tipo_contrato"],
                            size="2",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ),
                    _detalle_campo(
                        "Modalidad",
                        rx.text(
                            ContratosState.contrato_seleccionado["modalidad_adjudicacion"],
                            size="2",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ),
                    _detalle_campo(
                        "Estatus",
                        status_badge_reactive(
                            ContratosState.contrato_seleccionado["estatus"],
                            show_icon=True,
                        ),
                    ),
                    _detalle_campo(
                        "Folio BUAP",
                        rx.text(
                            rx.cond(
                                ContratosState.contrato_seleccionado["numero_folio_buap"],
                                ContratosState.contrato_seleccionado["numero_folio_buap"],
                                "Sin folio",
                            ),
                            size="2",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.card(
            rx.vstack(
                rx.text("Vigencia", weight="bold", size="4"),
                rx.grid(
                    _detalle_campo(
                        "Inicio",
                        rx.text(
                            ContratosState.contrato_seleccionado["fecha_inicio_fmt"],
                            size="2",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ),
                    _detalle_campo(
                        "Fin",
                        rx.text(
                            rx.cond(
                                ContratosState.contrato_seleccionado["fecha_fin"],
                                ContratosState.contrato_seleccionado["fecha_fin_fmt"],
                                "Indefinido",
                            ),
                            size="2",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ),
                    _detalle_campo(
                        "Tipo de duración",
                        rx.text(
                            rx.cond(
                                ContratosState.contrato_seleccionado["tipo_duracion"],
                                ContratosState.contrato_seleccionado["tipo_duracion"],
                                "No aplica",
                            ),
                            size="2",
                            color=Colors.TEXT_PRIMARY,
                        ),
                    ),
                    _detalle_campo(
                        "Vigencia",
                        rx.badge(
                            ContratosState.contrato_seleccionado["vigencia_label"],
                            color_scheme=ContratosState.contrato_seleccionado["vigencia_color_scheme"],
                            size="1",
                            variant="soft",
                        ),
                    ),
                    columns="2",
                    spacing="4",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.vstack(
            rx.text("Planeación de personal", weight="bold", size="4"),
            rx.grid(
                metric_card(
                    titulo="Plazas mínimas",
                    valor=ContratosState.contrato_seleccionado["cantidad_plazas_minima"],
                    icono="users",
                    color_scheme="blue",
                    descripcion="Compromiso mínimo del contrato",
                ),
                metric_card(
                    titulo="Plazas máximas",
                    valor=ContratosState.contrato_seleccionado["cantidad_plazas_maxima"],
                    icono="briefcase",
                    color_scheme="green",
                    descripcion="Capacidad máxima materializable",
                ),
                metric_card(
                    titulo="Categorías",
                    valor=ContratosState.total_categorias_detalle_contrato,
                    icono="tags",
                    color_scheme="amber",
                    descripcion="Perfiles configurados en el contrato",
                ),
                columns="3",
                spacing="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.text("Montos", weight="bold", size="4"),
                    rx.spacer(),
                    rx.badge(
                        rx.cond(
                            ContratosState.contrato_seleccionado["incluye_iva"],
                            "Incluye IVA",
                            "Sin IVA",
                        ),
                        color_scheme=rx.cond(
                            ContratosState.contrato_seleccionado["incluye_iva"],
                            "green",
                            "gray",
                        ),
                        variant="soft",
                    ),
                    align="center",
                    width="100%",
                ),
                rx.grid(
                    metric_card(
                        titulo="Monto mínimo",
                        valor=ContratosState.contrato_seleccionado["monto_minimo_fmt"],
                        icono="banknote",
                        color_scheme="blue",
                        descripcion="Estimación mínima del contrato",
                    ),
                    metric_card(
                        titulo="Monto máximo",
                        valor=ContratosState.contrato_seleccionado["monto_maximo_fmt"],
                        icono="wallet",
                        color_scheme="green",
                        descripcion="Tope autorizado del contrato",
                    ),
                    columns="2",
                    spacing="3",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.text("Categorías configuradas", weight="bold", size="4"),
                    rx.spacer(),
                    rx.cond(
                        ContratosState.tiene_categorias_detalle_contrato,
                        rx.badge(
                            ContratosState.total_categorias_detalle_contrato,
                            color_scheme="blue",
                            variant="soft",
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.cond(
                    ContratosState.tiene_categorias_detalle_contrato,
                    rx.box(
                        table_shell(
                            loading=False,
                            has_rows=True,
                            empty_component=rx.fragment(),
                            header_cells=[
                                rx.table.column_header_cell("Clave", width="90px"),
                                rx.table.column_header_cell("Categoría"),
                                rx.table.column_header_cell("Mín.", width="70px"),
                                rx.table.column_header_cell("Máx.", width="70px"),
                                rx.table.column_header_cell("Costo", width="120px"),
                                rx.table.column_header_cell("Monto mín.", width="120px"),
                                rx.table.column_header_cell("Monto máx.", width="120px"),
                            ],
                            body_component=rx.foreach(
                                ContratosState.categorias_detalle_contrato,
                                _fila_categoria_detalle,
                            ),
                        ),
                        overflow_x="auto",
                        width="100%",
                    ),
                    empty_state_card(
                        title="Sin categorías configuradas",
                        description="Este contrato no tiene un desglose de plazas por categoría capturado.",
                        icon="tags",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
            width="100%",
            variant="surface",
        ),
        rx.cond(
            ContratosState.contrato_seleccionado["descripcion_objeto"],
            rx.card(
                rx.vstack(
                    rx.text("Descripción del objeto", weight="bold", size="4"),
                    rx.text(
                        ContratosState.contrato_seleccionado["descripcion_objeto"],
                        size="2",
                        color=Colors.TEXT_PRIMARY,
                    ),
                    spacing="2",
                    width="100%",
                    align="start",
                ),
                width="100%",
                variant="surface",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ContratosState.contrato_seleccionado["notas"],
            rx.card(
                rx.vstack(
                    rx.text("Notas", weight="bold", size="4"),
                    rx.text(
                        ContratosState.contrato_seleccionado["notas"],
                        size="2",
                        color=Colors.TEXT_PRIMARY,
                    ),
                    spacing="2",
                    width="100%",
                    align="start",
                ),
                width="100%",
                variant="surface",
            ),
            rx.fragment(),
        ),
        spacing="4",
        width="100%",
    )


def _fila_entregable(entregable: dict) -> rx.Component:
    """Fila de entregable en la tabla"""
    return rx.table.row(
        rx.table.cell(rx.text(f"Período {entregable['numero_periodo']}", weight="medium")),
        rx.table.cell(rx.text(entregable["periodo_texto"], size="2", color=Colors.TEXT_SECONDARY)),
        rx.table.cell(status_badge_reactive(entregable["estatus"])),
        rx.table.cell(
            rx.cond(
                entregable["monto_aprobado"],
                rx.text(entregable["monto_aprobado_fmt"], size="2", weight="medium"),
                rx.text("-", size="2", color=Colors.TEXT_MUTED),
            ),
        ),
        rx.table.cell(
            rx.button(
                rx.icon("eye", size=14),
                size="1",
                variant="ghost",
                on_click=rx.redirect(f"/entregables/{entregable['id']}"),
            ),
        ),
    )


def _tab_entregables_contrato() -> rx.Component:
    """Pestaña de entregables del contrato"""
    return rx.vstack(
        rx.cond(
            ContratosState.cargando_entregables,
            rx.center(rx.spinner(size="3"), padding="8"),
            rx.cond(
                ContratosState.tiene_entregables_contrato,
                rx.box(
                    table_shell(
                        loading=False,
                        has_rows=True,
                        empty_component=rx.fragment(),
                        header_cells=[
                            rx.table.column_header_cell("Período"),
                            rx.table.column_header_cell("Fechas"),
                            rx.table.column_header_cell("Estado"),
                            rx.table.column_header_cell("Monto"),
                            rx.table.column_header_cell(""),
                        ],
                        body_component=rx.foreach(ContratosState.entregables_contrato, _fila_entregable),
                    ),
                    overflow_x="auto",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("package", size=40, color=Colors.TEXT_MUTED),
                        rx.text("No hay entregables para este contrato", color=Colors.TEXT_MUTED),
                        rx.text("Los entregables se generan automáticamente según la configuración", size="1", color=Colors.TEXT_MUTED),
                        spacing="2",
                        align="center",
                    ),
                    padding="8",
                ),
            ),
        ),
        spacing="4",
        width="100%",
        min_height="200px",
    )


def modal_detalle_contrato() -> rx.Component:
    """Modal para mostrar detalles del contrato con pestañas"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.cond(
                ContratosState.contrato_seleccionado,
                rx.vstack(
                    rx.dialog.title("Detalle del Contrato"),

                    # Tabs de contenido
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Información", value="info"),
                            rx.tabs.trigger(
                                rx.hstack(
                                    rx.text("Entregables"),
                                    rx.cond(
                                        ContratosState.tiene_entregables_contrato,
                                        rx.badge(
                                            ContratosState.entregables_contrato.length(),
                                            color_scheme="blue",
                                            size="1",
                                        ),
                                        rx.fragment(),
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                value="entregables",
                            ),
                        ),
                        rx.tabs.content(
                            _tab_informacion_contrato(),
                            value="info",
                            padding_top="16px",
                        ),
                        rx.tabs.content(
                            _tab_entregables_contrato(),
                            value="entregables",
                            padding_top="16px",
                        ),
                        default_value="info",
                        width="100%",
                    ),

                    # Botones
                    rx.hstack(
                        rx.button(
                            "Cerrar",
                            variant="soft",
                            size="2",
                            on_click=ContratosState.cerrar_modal_detalle,
                        ),
                        # Editar solo si está en BORRADOR o SUSPENDIDO
                        rx.cond(
                            (ContratosState.contrato_seleccionado["estatus"] == "BORRADOR") |
                            (ContratosState.contrato_seleccionado["estatus"] == "SUSPENDIDO"),
                            rx.button(
                                "Editar",
                                on_click=lambda: ContratosState.abrir_modal_editar(
                                    ContratosState.contrato_seleccionado
                                ),
                                size="2"
                            ),
                        ),
                        spacing="2",
                        justify="end",
                        margin_top="16px",
                    ),

                    spacing="4",
                    width="100%"
                ),
            ),
            max_width="700px"
        ),
        open=ContratosState.mostrar_modal_detalle,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )


def modal_confirmar_cancelar() -> rx.Component:
    """Modal de confirmación para cancelar contrato"""
    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title("Cancelar Contrato"),
            rx.alert_dialog.description(
                rx.cond(
                    ContratosState.contrato_seleccionado,
                    rx.text(
                        "¿Está seguro que desea cancelar el contrato ",
                        rx.text(
                            ContratosState.contrato_seleccionado["codigo"],
                            weight="bold"
                        ),
                        "? Esta acción no se puede deshacer."
                    ),
                    "¿Está seguro que desea cancelar este contrato?"
                )
            ),
            rx.hstack(
                boton_cancelar(
                    texto="No, mantener",
                    on_click=ContratosState.cerrar_confirmar_cancelar,
                ),
                boton_eliminar(
                    texto="Sí, cancelar",
                    texto_eliminando="Cancelando...",
                    on_click=ContratosState.cancelar_contrato,
                    saving=ContratosState.saving,
                ),
                spacing="3",
                justify="end",
            ),
        ),
        open=ContratosState.mostrar_modal_confirmar_cancelar,
        # No cerrar al hacer click fuera - solo con botones
        on_open_change=rx.noop,
    )
