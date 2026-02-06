"""
Página de Login.

Proporciona la interfaz de inicio de sesión para el sistema.
Usa AuthState para manejar la autenticación.
"""
import reflex as rx

from app.presentation.components.shared.auth_state import AuthState
from app.presentation.theme import Colors, Spacing


# =============================================================================
# STATE LOCAL PARA EL FORMULARIO
# =============================================================================

class LoginState(AuthState):
    """
    Estado para la página de login.

    Hereda de AuthState para tener acceso a iniciar_sesion().
    Maneja los campos del formulario localmente.
    """

    # Campos del formulario
    email: str = ""
    password: str = ""

    # Errores de validación
    error_email: str = ""
    error_password: str = ""

    # UI
    mostrar_password: bool = False

    # ========================
    # SETTERS
    # ========================

    def set_email(self, value: str):
        """Setter para email con limpieza de error."""
        self.email = value.strip().lower()
        self.error_email = ""

    def set_password(self, value: str):
        """Setter para password con limpieza de error."""
        self.password = value
        self.error_password = ""

    def toggle_mostrar_password(self):
        """Alterna visibilidad de la contraseña."""
        self.mostrar_password = not self.mostrar_password

    # ========================
    # VALIDACIÓN
    # ========================

    def _validar_formulario(self) -> bool:
        """Valida los campos del formulario."""
        es_valido = True

        # Validar email
        if not self.email:
            self.error_email = "El email es requerido"
            es_valido = False
        elif "@" not in self.email or "." not in self.email:
            self.error_email = "Ingresa un email válido"
            es_valido = False

        # Validar password
        if not self.password:
            self.error_password = "La contraseña es requerida"
            es_valido = False
        elif len(self.password) < 6:
            self.error_password = "La contraseña debe tener al menos 6 caracteres"
            es_valido = False

        return es_valido

    # ========================
    # ACCIONES
    # ========================

    async def submit_login(self):
        """Procesa el formulario de login."""
        # Validar primero
        if not self._validar_formulario():
            return

        # Delegar a AuthState.iniciar_sesion
        return await self.iniciar_sesion(self.email, self.password)

    def _limpiar_formulario(self):
        """Limpia el formulario."""
        self.email = ""
        self.password = ""
        self.error_email = ""
        self.error_password = ""
        self.mostrar_password = False

    # ========================
    # ON_MOUNT
    # ========================

    async def on_mount(self):
        """
        Al montar la página de login.

        Si el usuario ya está autenticado, redirigir a home.
        """
        # Resetear loading (BaseState inicia en True para skeletons de datos)
        self.loading = False

        await self.verificar_sesion()

        # Si ya está logueado, redirigir
        if self.esta_autenticado:
            return rx.redirect("/")

    # ========================
    # PROPIEDADES CALCULADAS
    # ========================

    @rx.var
    def puede_enviar(self) -> bool:
        """Indica si el formulario puede enviarse."""
        return bool(self.email and self.password and not self.loading)

    @rx.var
    def tiene_errores(self) -> bool:
        """Indica si hay errores de validación."""
        return bool(self.error_email or self.error_password)


# =============================================================================
# COMPONENTES
# =============================================================================

def _input_email() -> rx.Component:
    """Campo de email."""
    return rx.box(
        rx.text(
            "Email",
            size="2",
            weight="medium",
            color=Colors.TEXT_PRIMARY if hasattr(Colors, 'TEXT_PRIMARY') else "gray",
        ),
        rx.input(
            placeholder="tu@email.com",
            value=LoginState.email,
            on_change=LoginState.set_email,
            type="email",
            size="3",
            width="100%",
            disabled=LoginState.loading,
        ),
        rx.cond(
            LoginState.error_email != "",
            rx.text(
                LoginState.error_email,
                color="red",
                size="1",
            ),
        ),
        width="100%",
        spacing="1",
    )


def _input_password() -> rx.Component:
    """Campo de contraseña con toggle de visibilidad."""
    return rx.box(
        rx.text(
            "Contraseña",
            size="2",
            weight="medium",
            color=Colors.TEXT_PRIMARY if hasattr(Colors, 'TEXT_PRIMARY') else "gray",
        ),
        rx.box(
            rx.input(
                placeholder="••••••••",
                value=LoginState.password,
                on_change=LoginState.set_password,
                type=rx.cond(LoginState.mostrar_password, "text", "password"),
                size="3",
                width="100%",
                #padding_right='2.5rem',
                disabled=LoginState.loading,
            ),
            rx.button(
                rx.cond(
                    LoginState.mostrar_password,
                    rx.icon("eye-off", size=16),
                    rx.icon("eye", size=16),
                ),
                on_click=LoginState.toggle_mostrar_password,
                variant="ghost",
                size="1",
                position="absolute",
                right="8px",
                top="50%",
                transform="translateY(-45%)",
                height="100%",
                display="flex",
                align="center",
                justify="center",
                cursor="pointer",
            ),
            position="relative",
            width="100%",
        ),
        rx.cond(
            LoginState.error_password != "",
            rx.text(
                LoginState.error_password,
                color="red",
                size="1",
            ),
        ),
        width="100%",
        spacing="1",
    )


def _boton_login() -> rx.Component:
    """Botón de inicio de sesión."""
    return rx.button(
        rx.cond(
            LoginState.loading,
            rx.hstack(
                rx.spinner(size="1"),
                rx.text("Iniciando sesión..."),
                spacing="2",
            ),
            rx.text("Iniciar Sesión"),
        ),
        on_click=LoginState.submit_login,
        disabled=~LoginState.puede_enviar,
        size="3",
        width="100%",
        cursor=rx.cond(LoginState.puede_enviar, "pointer", "not-allowed"),
    )


def _formulario_login() -> rx.Component:
    """Formulario completo de login."""
    return rx.form(
        rx.vstack(
            _input_email(),
            _input_password(),
            _boton_login(),
            spacing="4",
            width="100%",
        ),
        on_submit=lambda _: LoginState.submit_login(),
        width="100%",
    )


def _card_login() -> rx.Component:
    """Card contenedor del formulario de login."""
    return rx.card(
        rx.vstack(
            # Logo o título
            rx.vstack(
                rx.icon("shield-check", size=48, color="blue"),
                rx.heading(
                    "Bienvenido",
                    size="6",
                    weight="bold",
                ),
                rx.text(
                    "Sistema de Gestión de la Secretaria de Administración",
                    size="2",
                    color="gray",
                    text_align="center",
                ),
                spacing="2",
                align="center",
            ),

            rx.divider(size="4"),

            # Formulario
            _formulario_login(),

            spacing="5",
            width="100%",
            padding="6",
            align='center'
        ),
        width="100%",
        max_width="400px",
    )


# =============================================================================
# PÁGINA
# =============================================================================

def login_page() -> rx.Component:
    """
    Página de inicio de sesión.

    Muestra un formulario centrado para ingresar credenciales.
    Si el usuario ya está autenticado, redirige a la página principal.
    """
    return rx.center(
        _card_login(),
        width="100%",
        min_height="100vh",
        padding="4",
        background=rx.color("gray", 2),
        on_mount=LoginState.on_mount,
    )
