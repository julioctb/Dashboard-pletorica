"""
Pagina de configuracion operativa de empresa en el portal.

Permite definir la politica de nomina:
- tipo de nomina
- reglas de pago por periodicidad
- bloqueo bancario previo a dispersion
"""
import reflex as rx

from app.presentation.components.ui import boton_guardar, form_input, form_select
from app.presentation.layouts.backoffice import page_header, page_layout
from app.presentation.theme import Colors, Spacing, Typography

from .state import ConfiguracionEmpresaState


def _card_shell(*children) -> rx.Component:
    return rx.vstack(
        *children,
        width="100%",
        spacing="3",
        padding=Spacing.LG,
        background=Colors.SURFACE,
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
    )


def _seccion_politica_nomina() -> rx.Component:
    return _card_shell(
        rx.text(
            "Politica de Nomina",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.text(
            "Define la periodicidad de pago que controla el calendario y la sugerencia de fechas de pago.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.separator(),
        form_select(
            label="Tipo de nomina",
            required=True,
            value=ConfiguracionEmpresaState.form_tipo_nomina,
            on_change=ConfiguracionEmpresaState.set_form_tipo_nomina,
            options=ConfiguracionEmpresaState.tipos_nomina_options,
            hint="La periodicidad controla el catalogo de periodos disponibles en /portal/nominas.",
        ),
    )


def _seccion_reglas_pago() -> rx.Component:
    return _card_shell(
        rx.text(
            "Reglas de Pago",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.text(
            "Los periodos y la fecha de pago sugerida se calculan automaticamente con estas reglas.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.separator(),
        rx.cond(
            ConfiguracionEmpresaState.es_quincenal,
            rx.vstack(
                form_select(
                    label="Regla de calculo quincenal",
                    required=True,
                    value=ConfiguracionEmpresaState.form_regla_calculo_quincenal,
                    on_change=ConfiguracionEmpresaState.set_form_regla_calculo_quincenal,
                    options=ConfiguracionEmpresaState.reglas_calculo_quincenal_options,
                    hint="Real por dias paga segun dias pagables. Base fija quincenal paga 15 dias y descuenta faltas/incapacidades por separado.",
                ),
                form_input(
                    label="Dia de pago - Primera quincena",
                    value=ConfiguracionEmpresaState.form_dia_pago_1q.to(str),
                    on_change=ConfiguracionEmpresaState.set_form_dia_pago_1q,
                    type="number",
                    min="1",
                    max="31",
                    hint="Dia del mes para la 1A quincena.",
                ),
                form_input(
                    label="Dia de pago - Segunda quincena",
                    value=ConfiguracionEmpresaState.form_dia_pago_2q.to(str),
                    on_change=ConfiguracionEmpresaState.set_form_dia_pago_2q,
                    type="number",
                    min="0",
                    max="31",
                    hint="0 significa ultimo dia del mes. Si capturas 1-15, el pago cae en el mes siguiente.",
                ),
                spacing="3",
                width="100%",
            ),
            rx.cond(
                ConfiguracionEmpresaState.es_semanal,
                form_select(
                    label="Dia de pago semanal",
                    required=True,
                    value=ConfiguracionEmpresaState.form_dia_pago_semanal.to(str),
                    on_change=ConfiguracionEmpresaState.set_form_dia_pago_semanal,
                    options=ConfiguracionEmpresaState.dias_semana_options,
                    hint="Base 1=Lunes ... 7=Domingo. El sistema toma la siguiente ocurrencia en o despues del cierre semanal.",
                ),
                form_input(
                    label="Dia de pago mensual",
                    value=ConfiguracionEmpresaState.form_dia_pago_mensual.to(str),
                    on_change=ConfiguracionEmpresaState.set_form_dia_pago_mensual,
                    type="number",
                    min="0",
                    max="31",
                    hint="0 significa ultimo dia del mes. Cualquier otro valor usa ese dia, ajustado al fin de mes si hace falta.",
                ),
            ),
        ),
    )


def _seccion_bloqueo_bancario() -> rx.Component:
    return _card_shell(
        rx.text(
            "Bloqueo Bancario",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.text(
            "Controla cuantos dias antes del pago se bloquean cambios a cuentas bancarias del personal.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.separator(),
        form_input(
            label="Dias de bloqueo antes del pago",
            value=ConfiguracionEmpresaState.form_dias_bloqueo.to(str),
            on_change=ConfiguracionEmpresaState.set_form_dias_bloqueo,
            type="number",
            min="1",
            max="10",
            hint="Rango permitido: 1 a 10 dias.",
        ),
        rx.callout.root(
            rx.callout.icon(rx.icon("info", size=16)),
            rx.callout.text(
                "Este bloqueo evita cambios bancarios de ultimo momento que puedan afectar la dispersion de nomina."
            ),
            color_scheme="blue",
            variant="soft",
            width="100%",
        ),
    )


def _seccion_aguinaldo() -> rx.Component:
    return _card_shell(
        rx.text(
            "Prestaciones Anuales",
            font_size=Typography.SIZE_LG,
            font_weight=Typography.WEIGHT_BOLD,
            color=Colors.TEXT_PRIMARY,
        ),
        rx.text(
            "Los días de aguinaldo se usan como snapshot al generar la corrida especial anual en nómina.",
            font_size=Typography.SIZE_SM,
            color=Colors.TEXT_SECONDARY,
        ),
        rx.separator(),
        form_input(
            label="Días de aguinaldo",
            value=ConfiguracionEmpresaState.form_dias_aguinaldo.to(str),
            on_change=ConfiguracionEmpresaState.set_form_dias_aguinaldo,
            type="number",
            min="15",
            max="90",
            hint="Mínimo legal: 15 días.",
        ),
    )


def _contenido_habilitado() -> rx.Component:
    return rx.vstack(
        _seccion_politica_nomina(),
        _seccion_reglas_pago(),
        _seccion_aguinaldo(),
        _seccion_bloqueo_bancario(),
        rx.hstack(
            rx.spacer(),
            boton_guardar(
                on_click=ConfiguracionEmpresaState.guardar_configuracion,
                saving=ConfiguracionEmpresaState.saving,
                disabled=~ConfiguracionEmpresaState.tiene_cambios,
                texto="Guardar cambios",
            ),
            width="100%",
        ),
        width="100%",
        spacing="4",
        max_width="760px",
    )


def _contenido_inactivo() -> rx.Component:
    return rx.vstack(
        rx.callout.root(
            rx.callout.icon(rx.icon("lock", size=16)),
            rx.callout.text(
                "La gestion de nomina no esta activa para esta empresa. Activa el modulo desde el catalogo de empresas para configurar la politica."
            ),
            color_scheme="gray",
            variant="soft",
            width="100%",
        ),
        width="100%",
        max_width="760px",
    )


def configuracion_empresa_page() -> rx.Component:
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Configuracion Operativa",
                subtitulo="Politica de nomina y reglas de pago",
                icono="settings",
                color_icono=Colors.PORTAL_ACCENT_SCHEME,
            ),
            toolbar=rx.fragment(),
            content=rx.cond(
                ConfiguracionEmpresaState.loading,
                rx.center(rx.spinner(size="3"), padding_y="60px"),
                rx.cond(
                    ConfiguracionEmpresaState.puede_configurar_nomina,
                    _contenido_habilitado(),
                    _contenido_inactivo(),
                ),
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=ConfiguracionEmpresaState.on_mount_configuracion_empresa,
    )
