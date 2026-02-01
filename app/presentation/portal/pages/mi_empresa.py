"""
Pagina Mi Empresa del portal de cliente.

Muestra los datos de la empresa del usuario en modo solo lectura.
Si el usuario tiene multiples empresas, muestra selector.
"""
import reflex as rx

from app.presentation.portal.state.portal_state import PortalState
from app.presentation.layout import page_layout, page_header
from app.presentation.theme import Colors, Typography, Spacing


# =============================================================================
# STATE
# =============================================================================

class MiEmpresaState(PortalState):
    """State para la pagina Mi Empresa."""

    async def on_mount_mi_empresa(self):
        resultado = await self.on_mount_portal()
        if resultado:
            return resultado
        await self.cargar_datos_empresa()


# =============================================================================
# COMPONENTES
# =============================================================================

def _campo_info(label: str, valor: rx.Var, icono: str = "") -> rx.Component:
    """Campo de informacion en modo solo lectura."""
    return rx.vstack(
        rx.text(
            label,
            font_size=Typography.SIZE_XS,
            font_weight=Typography.WEIGHT_SEMIBOLD,
            color=Colors.TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing="0.05em",
        ),
        rx.cond(
            valor,
            rx.text(
                valor,
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_PRIMARY,
            ),
            rx.text(
                "No disponible",
                font_size=Typography.SIZE_SM,
                color=Colors.TEXT_MUTED,
                font_style="italic",
            ),
        ),
        spacing="1",
        width="100%",
    )


def _seccion(titulo: str, icono: str, *campos: rx.Component) -> rx.Component:
    """Seccion agrupada de campos."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icono, size=18, color="var(--teal-9)"),
                rx.text(
                    titulo,
                    font_size=Typography.SIZE_SM,
                    font_weight=Typography.WEIGHT_BOLD,
                    color=Colors.TEXT_PRIMARY,
                ),
                spacing="2",
                align="center",
            ),
            rx.separator(),
            rx.grid(
                *campos,
                columns=rx.breakpoints(initial="1", sm="2"),
                spacing="4",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
    )


def _datos_empresa() -> rx.Component:
    """Vista de datos de la empresa."""
    datos = MiEmpresaState.datos_empresa

    return rx.cond(
        MiEmpresaState.loading,
        rx.center(rx.spinner(size="3"), padding="12"),
        rx.cond(
            datos,
            rx.vstack(
                # Datos generales
                _seccion(
                    "Datos Generales",
                    "building-2",
                    _campo_info("Nombre Comercial", datos["nombre_comercial"]),
                    _campo_info("Razon Social", datos["razon_social"]),
                    _campo_info("RFC", datos["rfc"]),
                    _campo_info("Tipo de Empresa", datos["tipo_empresa"]),
                    _campo_info("Codigo Corto", datos["codigo_corto"]),
                    _campo_info("Estatus", datos["estatus"]),
                ),
                # Contacto
                _seccion(
                    "Contacto",
                    "phone",
                    _campo_info("Telefono", datos["telefono"]),
                    _campo_info("Email", datos["email"]),
                    _campo_info("Pagina Web", datos["pagina_web"]),
                    _campo_info("Direccion", datos["direccion"]),
                    _campo_info("Codigo Postal", datos["codigo_postal"]),
                ),
                # Datos laborales
                _seccion(
                    "Datos Laborales",
                    "briefcase",
                    _campo_info("Registro Patronal", datos["registro_patronal"]),
                    _campo_info("Prima de Riesgo", datos["prima_riesgo"]),
                ),
                spacing="4",
                width="100%",
            ),
            rx.center(
                rx.text("No se encontraron datos de la empresa", color="gray"),
                padding="12",
            ),
        ),
    )


# =============================================================================
# SELECTOR DE EMPRESA (multiples empresas)
# =============================================================================

def _empresa_selector() -> rx.Component:
    """Selector de empresa si el usuario tiene multiples asignadas."""
    return rx.cond(
        MiEmpresaState.tiene_multiples_empresas,
        rx.card(
            rx.hstack(
                rx.icon("repeat", size=16, color=Colors.TEXT_SECONDARY),
                rx.text(
                    "Tienes acceso a multiples empresas. Selecciona cual deseas ver:",
                    font_size=Typography.SIZE_SM,
                    color=Colors.TEXT_SECONDARY,
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            variant="surface",
        ),
        rx.fragment(),
    )


# =============================================================================
# PAGINA
# =============================================================================

def mi_empresa_page() -> rx.Component:
    """Pagina de datos de la empresa (solo lectura)."""
    return rx.box(
        page_layout(
            header=page_header(
                titulo="Mi Empresa",
                subtitulo="Datos generales de la empresa",
                icono="building-2",
            ),
            content=rx.vstack(
                _empresa_selector(),
                _datos_empresa(),
                spacing="4",
                width="100%",
            ),
        ),
        width="100%",
        min_height="100vh",
        on_mount=MiEmpresaState.on_mount_mi_empresa,
    )
