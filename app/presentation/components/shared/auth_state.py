"""
Estado de Autenticación para Reflex.

Este state maneja la sesión del usuario, tokens JWT, y selección de empresa.
Hereda de BaseState para mantener los helpers de errores y carga.

ARQUITECTURA:
    rx.State (Reflex)
        └── BaseState (helpers de errores, loading, etc.)
                └── AuthState (sesión, usuario, empresas)
                        └── TuModuloState (hereda auth si necesita protección)

USO EN MÓDULOS QUE REQUIEREN AUTENTICACIÓN:
    # En lugar de heredar de BaseState:
    from app.presentation.components.shared.auth_state import AuthState

    class MiModuloProtegidoState(AuthState):
        # Ahora tienes acceso a:
        # - self.usuario_actual (dict con perfil)
        # - self.esta_autenticado (bool)
        # - self.es_admin (bool)
        # - self.empresa_actual (dict con empresa seleccionada)
        pass

USO EN PÁGINAS PARA VERIFICAR AUTH:
    def mi_pagina_protegida() -> rx.Component:
        return rx.cond(
            AuthState.requiere_login & ~AuthState.esta_autenticado,
            rx.redirect("/login"),
            contenido_de_la_pagina(),
        )

NOTA SOBRE SKIP_AUTH:
    Si Config.SKIP_AUTH=True, la propiedad `requiere_login` retorna False,
    permitiendo acceso sin autenticación durante desarrollo/testing.
"""
import reflex as rx
import logging
from typing import List, Optional
from uuid import UUID

from app.core.config import Config
from app.presentation.components.shared.base_state import BaseState

logger = logging.getLogger(__name__)


class AuthState(BaseState):
    """
    Estado de autenticación que extiende BaseState.

    Proporciona:
    - Manejo de sesión (tokens JWT)
    - Información del usuario actual
    - Selección de empresa activa
    - Propiedades para verificar permisos

    Los módulos que requieran autenticación deben heredar de este state
    en lugar de BaseState.
    """

    # =========================================================================
    # ESTADO DE SESIÓN
    # =========================================================================

    # Tokens JWT de Supabase Auth
    _access_token: str = ""
    _refresh_token: str = ""
    _token_expires_at: int = 0

    # Perfil del usuario logueado (dict para serialización en Reflex)
    usuario_actual: dict = {}

    # Empresa actualmente seleccionada
    empresa_actual: dict = {}

    # Lista de empresas a las que el usuario tiene acceso
    empresas_disponibles: List[dict] = []

    # Flag para saber si ya se intentó cargar la sesión
    _sesion_verificada: bool = False

    # =========================================================================
    # SIMULACIÓN DE CLIENTE (solo DEBUG)
    # =========================================================================
    _simulando_cliente: bool = False
    _empresas_simulacion: List[dict] = []

    # =========================================================================
    # PROPIEDADES CALCULADAS
    # =========================================================================

    @rx.var
    def simulando_cliente(self) -> bool:
        """Indica si se está simulando vista de cliente (solo en DEBUG)."""
        return self._simulando_cliente

    @rx.var
    def requiere_login(self) -> bool:
        """
        Indica si el sistema requiere autenticación.

        Retorna False si SKIP_AUTH=True.
        Usar en páginas para decidir si redirigir a login.
        """
        return Config.requiere_autenticacion()

    @rx.var
    def esta_autenticado(self) -> bool:
        """
        Indica si hay un usuario con sesión activa.

        Verifica que exista un usuario cargado y un token válido.
        """
        tiene_usuario = bool(self.usuario_actual and self.usuario_actual.get('id'))
        tiene_token = bool(self._access_token)
        return tiene_usuario and tiene_token

    @rx.var
    def es_admin(self) -> bool:
        """
        Indica si el usuario actual tiene rol de administrador.

        Los admins tienen acceso a todas las empresas y funciones
        administrativas como gestión de usuarios.
        Si SKIP_AUTH=True, siempre retorna True (acceso completo en dev).
        Retorna False si se está simulando vista de cliente.
        """
        if self._simulando_cliente:
            return False
        if not Config.requiere_autenticacion():
            return True
        if not self.usuario_actual:
            return False
        rol = self.usuario_actual.get('rol', '')
        return rol == 'admin'

    @rx.var
    def es_client(self) -> bool:
        """Indica si el usuario actual es cliente (empresa proveedora).
        Retorna True si se está simulando vista de cliente."""
        if self._simulando_cliente:
            return True
        if not self.usuario_actual:
            return False
        rol = self.usuario_actual.get('rol', '')
        return rol == 'client'

    @rx.var
    def nombre_usuario(self) -> str:
        """Nombre del usuario para mostrar en UI (navbar, sidebar, etc.)."""
        if not self.usuario_actual:
            return ""
        return self.usuario_actual.get('nombre_completo', 'Usuario')

    @rx.var
    def email_usuario(self) -> str:
        """Email del usuario actual."""
        if not self.usuario_actual:
            return ""
        return self.usuario_actual.get('email', '')

    @rx.var
    def id_usuario(self) -> str:
        """UUID del usuario actual como string."""
        if not self.usuario_actual:
            return ""
        return str(self.usuario_actual.get('id', ''))

    @rx.var
    def nombre_empresa_actual(self) -> str:
        """Nombre de la empresa actualmente seleccionada."""
        if not self.empresa_actual:
            return "Sin empresa"
        return self.empresa_actual.get('empresa_nombre', 'Empresa')

    @rx.var
    def id_empresa_actual(self) -> int:
        """ID de la empresa actualmente seleccionada."""
        if not self.empresa_actual:
            return 0
        return self.empresa_actual.get('empresa_id', 0)

    @rx.var
    def tiene_multiples_empresas(self) -> bool:
        """Indica si el usuario tiene acceso a más de una empresa."""
        return len(self.empresas_disponibles) > 1

    @rx.var
    def usuario_activo(self) -> bool:
        """Indica si el usuario está activo (no deshabilitado)."""
        if not self.usuario_actual:
            return False
        return self.usuario_actual.get('activo', False)

    # =========================================================================
    # PERMISOS GRANULARES
    # =========================================================================

    @rx.var
    def es_super_admin(self) -> bool:
        """Puede gestionar usuarios y permisos."""
        if not Config.requiere_autenticacion():
            return True
        if self._simulando_cliente:
            return False
        return self.usuario_actual.get("puede_gestionar_usuarios", False)

    @rx.var
    def permisos_usuario(self) -> dict:
        """Dict de permisos del usuario actual."""
        if not Config.requiere_autenticacion():
            return {
                "requisiciones": {"operar": True, "autorizar": True},
                "entregables": {"operar": True, "autorizar": True},
                "pagos": {"operar": True, "autorizar": True},
                "contratos": {"operar": True, "autorizar": True},
                "empresas": {"operar": True, "autorizar": True},
                "empleados": {"operar": True, "autorizar": True},
            }
        if self._simulando_cliente:
            return {}
        return self.usuario_actual.get("permisos", {})

    # --- Requisiciones ---
    @rx.var
    def puede_operar_requisiciones(self) -> bool:
        return self.permisos_usuario.get("requisiciones", {}).get("operar", False)

    @rx.var
    def puede_autorizar_requisiciones(self) -> bool:
        return self.permisos_usuario.get("requisiciones", {}).get("autorizar", False)

    # --- Entregables ---
    @rx.var
    def puede_operar_entregables(self) -> bool:
        return self.permisos_usuario.get("entregables", {}).get("operar", False)

    @rx.var
    def puede_autorizar_entregables(self) -> bool:
        return self.permisos_usuario.get("entregables", {}).get("autorizar", False)

    # --- Pagos ---
    @rx.var
    def puede_autorizar_pagos(self) -> bool:
        return self.permisos_usuario.get("pagos", {}).get("autorizar", False)

    # --- Contratos ---
    @rx.var
    def puede_operar_contratos(self) -> bool:
        return self.permisos_usuario.get("contratos", {}).get("operar", False)

    # --- Empresas ---
    @rx.var
    def puede_operar_empresas(self) -> bool:
        return self.permisos_usuario.get("empresas", {}).get("operar", False)

    # --- Empleados ---
    @rx.var
    def puede_operar_empleados(self) -> bool:
        return self.permisos_usuario.get("empleados", {}).get("operar", False)

    # =========================================================================
    # PERMISOS POR EMPRESA (SaaS pivot)
    # =========================================================================

    @rx.var
    def rol_empresa_actual(self) -> str:
        """Rol del usuario en la empresa actualmente seleccionada."""
        if not self.empresa_actual:
            return ""
        return self.empresa_actual.get('rol_empresa', 'lectura')

    @rx.var
    def es_superadmin(self) -> bool:
        """Indica si el usuario es dueño de la plataforma SaaS."""
        if not Config.requiere_autenticacion():
            return True
        if self._simulando_cliente:
            return False
        if not self.usuario_actual:
            return False
        rol = self.usuario_actual.get('rol', '')
        return rol in ('superadmin', 'admin')

    @rx.var
    def es_admin_empresa(self) -> bool:
        """Indica si el usuario administra la empresa actual."""
        if self.es_superadmin:
            return True
        return self.rol_empresa_actual == 'admin_empresa'

    @rx.var
    def es_rrhh(self) -> bool:
        """Puede gestionar personal, expedientes, cuentas bancarias."""
        if self.es_superadmin:
            return True
        return self.rol_empresa_actual in ('rrhh', 'admin_empresa')

    @rx.var
    def es_operaciones(self) -> bool:
        """Puede gestionar evidencias, asistencias, reportes de campo."""
        if self.es_superadmin:
            return True
        return self.rol_empresa_actual in ('operaciones', 'admin_empresa')

    @rx.var
    def es_contabilidad(self) -> bool:
        """Puede gestionar entregables fiscales, nómina."""
        if self.es_superadmin:
            return True
        return self.rol_empresa_actual in ('contabilidad', 'admin_empresa')

    @rx.var
    def es_validador_externo(self) -> bool:
        """Es personal de institución cliente (solo ve entregables)."""
        return self.rol_empresa_actual == 'validador_externo'

    @rx.var
    def es_empleado_portal(self) -> bool:
        """Es empleado con acceso al portal de autoservicio."""
        if not self.usuario_actual:
            return False
        rol = self.usuario_actual.get('rol', '')
        return rol == 'empleado' or self.rol_empresa_actual == 'empleado'

    @rx.var
    def puede_gestionar_personal(self) -> bool:
        """Helper: ¿puede ver/editar empleados y expedientes?"""
        return self.es_rrhh

    @rx.var
    def puede_aprobar_documentos(self) -> bool:
        """Helper: ¿puede aprobar/rechazar docs de empleados?"""
        return self.es_rrhh

    @rx.var
    def puede_configurar_empresa(self) -> bool:
        """Helper: ¿puede cambiar configuración de la empresa?"""
        return self.es_admin_empresa

    # =========================================================================
    # MÉTODOS DE AUTENTICACIÓN
    # =========================================================================

    async def iniciar_sesion(self, email: str, password: str):
        """
        Inicia sesión con email y contraseña.

        Args:
            email: Email del usuario
            password: Contraseña

        Returns:
            rx.redirect a la página principal si es exitoso,
            rx.toast.error si falla

        Ejemplo de uso en página de login:
            rx.button(
                "Iniciar Sesión",
                on_click=AuthState.iniciar_sesion(
                    LoginState.email,
                    LoginState.password
                )
            )
        """
        self.loading = True

        try:
            from app.services import user_service

            # Autenticar con el servicio
            profile, session_data = await user_service.login(email, password)

            # Guardar tokens
            self._access_token = session_data.get('access_token', '')
            self._refresh_token = session_data.get('refresh_token', '')
            self._token_expires_at = session_data.get('expires_at', 0)

            # Guardar perfil como dict
            self.usuario_actual = profile.model_dump(mode='json')

            # Cargar empresas del usuario
            await self._cargar_empresas_usuario()

            # Marcar sesión como verificada
            self._sesion_verificada = True

            logger.info(f"Login exitoso: {email}")

            # Redirigir segun rol
            rol = self.usuario_actual.get('rol', '')
            if rol == 'client':
                return rx.redirect("/portal")
            return rx.redirect("/")

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Error en login: {error_msg}")

            # Mensajes amigables para errores comunes
            if "inválid" in error_msg.lower() or "incorrect" in error_msg.lower():
                return rx.toast.error(
                    "Email o contraseña incorrectos",
                    position="top-center"
                )
            elif "desactivad" in error_msg.lower() or "inactiv" in error_msg.lower():
                return rx.toast.error(
                    "Tu cuenta está desactivada. Contacta al administrador.",
                    position="top-center"
                )
            else:
                return rx.toast.error(
                    f"Error al iniciar sesión: {error_msg}",
                    position="top-center"
                )

        finally:
            self.loading = False

    async def cerrar_sesion(self):
        """
        Cierra la sesión actual y limpia el estado.

        Redirige a la página de login después de cerrar sesión.
        """
        try:
            from app.services import user_service
            await user_service.logout()
        except Exception as e:
            logger.warning(f"Error en logout del servidor (no crítico): {e}")

        # Limpiar estado local (siempre, aunque falle el servidor)
        self._limpiar_sesion()

        logger.info("Sesión cerrada")
        return rx.redirect("/login")

    async def verificar_sesion(self):
        """
        Verifica si hay una sesión válida al cargar la aplicación.

        Este método debe llamarse en el on_mount de páginas protegidas
        o en el layout principal.

        Si el token es válido, carga el perfil del usuario.
        Si no es válido, limpia la sesión.
        """
        # Si ya verificamos, no repetir
        if self._sesion_verificada:
            return

        # Si no hay token, no hay nada que verificar
        if not self._access_token:
            self._sesion_verificada = True
            return

        try:
            from app.services import user_service

            # Validar token con el servicio
            profile = await user_service.validar_token(self._access_token)

            if profile:
                # Token válido, actualizar perfil
                self.usuario_actual = profile.model_dump(mode='json')
                await self._cargar_empresas_usuario()
                logger.debug("Sesión verificada correctamente")
            else:
                # Token inválido, intentar refrescar
                await self._refrescar_sesion()

        except Exception as e:
            logger.warning(f"Error verificando sesión: {e}")
            self._limpiar_sesion()

        finally:
            self._sesion_verificada = True

    async def _refrescar_sesion(self):
        """Intenta refrescar el token de acceso usando el refresh token."""
        if not self._refresh_token:
            self._limpiar_sesion()
            return

        try:
            from app.services import user_service

            nuevos_tokens = await user_service.refrescar_token(self._refresh_token)

            if nuevos_tokens:
                self._access_token = nuevos_tokens.get('access_token', '')
                self._refresh_token = nuevos_tokens.get('refresh_token', '')
                self._token_expires_at = nuevos_tokens.get('expires_at', 0)
                logger.debug("Token refrescado exitosamente")
            else:
                # No se pudo refrescar, sesión expirada
                self._limpiar_sesion()
                logger.info("Sesión expirada, requiere nuevo login")

        except Exception as e:
            logger.warning(f"Error refrescando token: {e}")
            self._limpiar_sesion()

    # =========================================================================
    # DEV VIEW SWITCHER - COMPUTED VARS (solo DEBUG)
    # =========================================================================

    @rx.var
    def dev_modo_cliente_activo(self) -> bool:
        """True si el dev switcher está en modo cliente (empresas cargadas o simulando)."""
        return len(self._empresas_simulacion) > 0 or self._simulando_cliente

    @rx.var
    def opciones_empresas_simulacion(self) -> List[dict]:
        """Opciones de empresas para el select de simulación."""
        return [
            {"label": e["nombre"], "value": str(e["id"])}
            for e in self._empresas_simulacion
        ]

    @rx.var
    def valor_empresa_simulada(self) -> str:
        """Valor actual del select de empresa simulada."""
        if self._simulando_cliente and self.empresa_actual:
            return str(self.empresa_actual.get("empresa_id", ""))
        return ""

    async def on_dev_view_change(self, vista: str):
        """Handler para toggle Admin/Cliente en dev switcher."""
        if vista == "cliente":
            await self.cargar_empresas_simulacion()
        else:
            return self.desactivar_simulacion_cliente()

    # =========================================================================
    # MÉTODOS DE SIMULACIÓN (solo DEBUG)
    # =========================================================================

    async def cargar_empresas_simulacion(self):
        """Carga todas las empresas desde DB para el selector de simulación."""
        if not Config.DEBUG:
            return
        try:
            from app.services import empresa_service
            empresas = await empresa_service.obtener_todas(incluir_inactivas=False)
            self._empresas_simulacion = [
                {
                    "id": e.id,
                    "nombre": e.nombre_comercial,
                }
                for e in empresas
            ]
        except Exception as e:
            logger.error(f"Error cargando empresas para simulación: {e}")
            self._empresas_simulacion = []

    async def activar_simulacion_cliente(self, empresa_id: str):
        """Activa simulación de vista cliente con la empresa seleccionada."""
        if not Config.DEBUG or not empresa_id:
            return
        eid = int(empresa_id)
        empresa = next(
            (e for e in self._empresas_simulacion if e["id"] == eid),
            None,
        )
        if not empresa:
            return
        self._simulando_cliente = True
        self.empresa_actual = {
            "empresa_id": empresa["id"],
            "empresa_nombre": empresa["nombre"],
        }
        logger.info(f"Simulación cliente activada: {empresa['nombre']} (ID {eid})")
        return rx.redirect("/portal")

    def desactivar_simulacion_cliente(self):
        """Desactiva simulación y vuelve a vista admin."""
        self._simulando_cliente = False
        self.empresa_actual = {}
        self._empresas_simulacion = []
        logger.info("Simulación cliente desactivada")
        return rx.redirect("/")

    def _limpiar_sesion(self):
        """Limpia todos los datos de sesión del estado."""
        self._access_token = ""
        self._refresh_token = ""
        self._token_expires_at = 0
        self.usuario_actual = {}
        self.empresa_actual = {}
        self.empresas_disponibles = []
        self._sesion_verificada = False
        self._simulando_cliente = False
        self._empresas_simulacion = []

    # =========================================================================
    # GESTIÓN DE EMPRESAS
    # =========================================================================

    async def _cargar_empresas_usuario(self):
        """
        Carga las empresas a las que el usuario tiene acceso.

        Selecciona automáticamente la empresa principal como activa.
        """
        if not self.usuario_actual:
            return

        try:
            from app.services import user_service

            user_id = UUID(str(self.usuario_actual.get('id')))
            empresas = await user_service.obtener_empresas_usuario(user_id)

            # Convertir a dict para Reflex
            self.empresas_disponibles = [e.model_dump(mode='json') for e in empresas]

            # Seleccionar empresa principal (o la primera disponible)
            empresa_principal = next(
                (e for e in self.empresas_disponibles if e.get('es_principal')),
                self.empresas_disponibles[0] if self.empresas_disponibles else None
            )

            if empresa_principal:
                self.empresa_actual = empresa_principal

            logger.debug(f"Cargadas {len(self.empresas_disponibles)} empresas para usuario")

        except Exception as e:
            logger.error(f"Error cargando empresas del usuario: {e}")
            self.empresas_disponibles = []

    async def cambiar_empresa(self, empresa_id: int):
        """
        Cambia la empresa actualmente seleccionada.

        Args:
            empresa_id: ID de la empresa a seleccionar

        Note:
            Solo permite seleccionar empresas a las que el usuario tiene acceso.
        """
        # Buscar la empresa en las disponibles
        empresa = next(
            (e for e in self.empresas_disponibles if e.get('empresa_id') == empresa_id),
            None
        )

        if not empresa:
            return rx.toast.error(
                "No tienes acceso a esa empresa",
                position="top-center"
            )

        self.empresa_actual = empresa
        logger.info(f"Empresa cambiada a: {empresa.get('empresa_nombre')}")

        return rx.toast.success(
            f"Empresa cambiada a {empresa.get('empresa_nombre')}",
            position="top-center"
        )

    def obtener_empresa_id_para_filtro(self) -> Optional[int]:
        """
        Retorna el ID de empresa para filtrar datos.

        - Si es admin: retorna None (ve todas las empresas)
        - Si es client: retorna el ID de la empresa actual

        Útil en servicios que necesitan filtrar por empresa del usuario.
        """
        if self.es_admin:
            return None  # Admins ven todo
        return self.id_empresa_actual or None

    # =========================================================================
    # UTILIDADES PARA PÁGINAS
    # =========================================================================

    @rx.var
    def debe_redirigir_login(self) -> bool:
        """
        Indica si se debe redirigir a login.

        Combina la verificación de si requiere login Y si no está autenticado.
        Útil para usar directamente en rx.cond de páginas.
        """
        if not self.requiere_login:
            return False
        return not self.esta_autenticado

    async def verificar_y_redirigir(self):
        """
        Verifica sesión y redirige a login si es necesario.

        Llamar en on_mount de páginas protegidas:
            async def on_mount(self):
                resultado = await self.verificar_y_redirigir()
                if resultado:
                    return resultado
                # ... resto del on_mount
        """
        await self.verificar_sesion()

        if self.requiere_login and not self.esta_autenticado:
            return rx.redirect("/login")

        return None

    async def _montar_pagina_auth(self, *operaciones):
        """
        _montar_pagina con verificación de autenticación.

        Verifica auth primero, si falla redirige a login.
        Si pasa, delega a _montar_pagina para skeleton + fetch.

        Uso:
            async def on_mount(self):
                async for _ in self._montar_pagina_auth(
                    self._fetch_datos,
                ):
                    yield
        """
        resultado = await self.verificar_y_redirigir()
        if resultado:
            self.loading = False
            yield resultado
            return

        async for _ in self._montar_pagina(*operaciones):
            yield

    def puede_acceder_empresa(self, empresa_id: int) -> bool:
        """
        Verifica si el usuario puede acceder a una empresa específica.

        Args:
            empresa_id: ID de la empresa a verificar

        Returns:
            True si es admin o tiene la empresa asignada
        """
        if self.es_admin:
            return True

        return any(
            e.get('empresa_id') == empresa_id
            for e in self.empresas_disponibles
        )


# =============================================================================
# HELPER PARA PROTEGER PÁGINAS
# =============================================================================

def pagina_protegida(contenido: rx.Component) -> rx.Component:
    """
    Wrapper que protege una página requiriendo autenticación.

    Uso:
        def mi_pagina() -> rx.Component:
            return pagina_protegida(
                rx.box(
                    rx.text("Contenido protegido"),
                )
            )

    Si SKIP_AUTH=True, muestra el contenido sin verificar auth.
    Si SKIP_AUTH=False y no hay sesión, redirige a /login.
    """
    return rx.cond(
        AuthState.debe_redirigir_login,
        # Si debe redirigir, mostrar loading mientras redirige
        rx.center(
            rx.spinner(size="3"),
            height="100vh",
        ),
        # Si está autenticado (o no requiere login), mostrar contenido
        contenido,
    )
