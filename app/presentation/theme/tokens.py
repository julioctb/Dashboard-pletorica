"""
Design Tokens - Sistema de Diseño BUAP Administrativo
=====================================================

Este archivo contiene todas las variables de diseño del sistema.
Es la única fuente de verdad para colores, espaciados, tipografía, etc.

Principios:
- Paleta neutral institucional (azul como primario)
- Optimizado para usuarios +42 años (alto contraste, tipografía legible)
- Consistente con WCAG 2.1 AA (contraste mínimo 4.5:1)

Uso:
    from app.presentation.theme import Colors, Spacing, Typography
    
    rx.box(
        padding=Spacing.MD,
        background=Colors.SURFACE,
    )
"""


class Colors:
    """
    Paleta de colores institucional neutral.
    
    Basada en azul institucional con grises cálidos.
    Todos los colores cumplen WCAG 2.1 AA para contraste.
    """
    
    # === PRIMARIOS (Azul Institucional) ===
    PRIMARY = "#1E40AF"           # Azul institucional - botones principales, links
    PRIMARY_HOVER = "#1E3A8A"     # Hover en elementos primarios
    PRIMARY_LIGHT = "#DBEAFE"     # Fondos destacados, selección activa
    PRIMARY_LIGHTER = "#EFF6FF"   # Fondos muy sutiles
    
    # === SECUNDARIOS (Slate) ===
    SECONDARY = "#475569"         # Texto secundario, iconos
    SECONDARY_HOVER = "#334155"   # Hover en elementos secundarios
    SECONDARY_LIGHT = "#F1F5F9"   # Fondos secundarios
    
    # === PORTAL (Teal como primario) ===
    PORTAL_PRIMARY = "var(--teal-9)"          # Color primario del portal
    PORTAL_PRIMARY_HOVER = "var(--teal-10)"   # Hover en elementos primarios
    PORTAL_PRIMARY_TEXT = "var(--teal-11)"    # Texto con color primario
    PORTAL_PRIMARY_LIGHT = "var(--teal-3)"    # Fondos sutiles
    PORTAL_PRIMARY_LIGHTER = "var(--teal-2)"  # Fondos muy sutiles

    # === FONDOS ===
    BG_APP = "#F8FAFC"            # Fondo general de la aplicación
    BACKGROUND = "var(--gray-2)"  # Alias para fondos de contenido (Radix)
    SURFACE = "#FFFFFF"           # Cards, modales, sidebar
    SURFACE_HOVER = "#F8FAFC"     # Hover en superficies
    
    # === BORDES ===
    BORDER = "#E2E8F0"            # Bordes de cards, separadores
    BORDER_STRONG = "#CBD5E1"     # Bordes más visibles
    BORDER_FOCUS = "#1E40AF"      # Borde de focus (accesibilidad)
    
    # === TEXTO ===
    TEXT_PRIMARY = "#0F172A"      # Títulos, contenido principal
    TEXT_SECONDARY = "#64748B"    # Subtítulos, metadata
    TEXT_MUTED = "#94A3B8"        # Placeholders, texto deshabilitado
    TEXT_INVERSE = "#FFFFFF"      # Texto sobre fondos oscuros
    
    # === ESTADOS SEMÁNTICOS ===
    SUCCESS = "#059669"           # Verde - Activo, completado
    SUCCESS_LIGHT = "#D1FAE5"     # Fondo verde suave
    SUCCESS_HOVER = "#047857"     # Hover verde
    
    WARNING = "#D97706"           # Ámbar - Pendiente, atención
    WARNING_LIGHT = "#FEF3C7"     # Fondo ámbar suave
    WARNING_HOVER = "#B45309"     # Hover ámbar
    
    ERROR = "#DC2626"             # Rojo - Error, inactivo
    ERROR_LIGHT = "#FEE2E2"       # Fondo rojo suave
    ERROR_HOVER = "#B91C1C"       # Hover rojo
    
    INFO = "#0284C7"              # Azul info - Información
    INFO_LIGHT = "#E0F2FE"        # Fondo azul info suave
    INFO_HOVER = "#0369A1"        # Hover azul info

    SIDEBAR_BG = "#FFFFFF"            # Fondo del sidebar
    SIDEBAR_BORDER = "#E2E8F0"        # Borde derecho del sidebar
    SIDEBAR_ITEM_HOVER = "#F1F5F9"    # Hover en items del sidebar
    SIDEBAR_ITEM_ACTIVE = "#DBEAFE"   # Fondo del item activo
    SIDEBAR_ITEM_ACTIVE_TEXT = "#1E40AF"  # Texto del item activo


class StatusColors:
    """
    Colores específicos para estados de contratos y documentos.
    
    Diseñados para identificación visual rápida (modelo semafórico).
    Incluye color_scheme para usar directamente con rx.badge().
    """
    
    # Estado: BORRADOR
    BORRADOR = "#64748B"          # Gris slate - neutral/pendiente
    BORRADOR_BG = "#F1F5F9"       # Fondo
    BORRADOR_ICON = "file-pen"    # Icono sugerido
    BORRADOR_SCHEME = "gray"      # Color scheme para rx.badge

    # Estado: ACTIVO
    ACTIVO = "#059669"            # Verde - en operación
    ACTIVO_BG = "#D1FAE5"         # Fondo
    ACTIVO_ICON = "circle-check"  # Icono sugerido
    ACTIVO_SCHEME = "green"       # Color scheme para rx.badge

    # Estado: SUSPENDIDO
    SUSPENDIDO = "#D97706"        # Ámbar - temporalmente detenido
    SUSPENDIDO_BG = "#FEF3C7"     # Fondo
    SUSPENDIDO_ICON = "circle-pause"  # Icono sugerido
    SUSPENDIDO_SCHEME = "amber"   # Color scheme para rx.badge

    # Estado: VENCIDO
    VENCIDO = "#DC2626"           # Rojo - requiere atención urgente
    VENCIDO_BG = "#FEE2E2"        # Fondo
    VENCIDO_ICON = "circle-alert" # Icono sugerido
    VENCIDO_SCHEME = "red"        # Color scheme para rx.badge

    # Estado: CANCELADO
    CANCELADO = "#991B1B"         # Rojo oscuro - terminado negativamente
    CANCELADO_BG = "#FEE2E2"      # Fondo
    CANCELADO_ICON = "circle-x"   # Icono sugerido
    CANCELADO_SCHEME = "red"      # Color scheme para rx.badge

    # Estado: CERRADO
    CERRADO = "#1E40AF"           # Azul - completado correctamente
    CERRADO_BG = "#DBEAFE"        # Fondo
    CERRADO_ICON = "archive"      # Icono sugerido
    CERRADO_SCHEME = "blue"       # Color scheme para rx.badge

    # Estado: INACTIVO (para entidades: empresas, empleados, etc.)
    INACTIVO = "#DC2626"          # Rojo - no activo
    INACTIVO_BG = "#FEE2E2"       # Fondo
    INACTIVO_ICON = "circle-x"    # Icono sugerido
    INACTIVO_SCHEME = "red"       # Color scheme para rx.badge

    # =========================================================================
    # Estados de Plaza
    # =========================================================================

    # Estado: VACANTE
    VACANTE = "#0284C7"           # Azul info - disponible para asignar
    VACANTE_BG = "#E0F2FE"        # Fondo
    VACANTE_ICON = "user-plus"    # Icono sugerido
    VACANTE_SCHEME = "sky"        # Color scheme para rx.badge

    # Estado: OCUPADA
    OCUPADA = "#059669"           # Verde - plaza asignada
    OCUPADA_BG = "#D1FAE5"        # Fondo
    OCUPADA_ICON = "user-check"   # Icono sugerido
    OCUPADA_SCHEME = "green"      # Color scheme para rx.badge

    # Estado: SUSPENDIDA (plaza)
    SUSPENDIDA = "#D97706"        # Ámbar - temporalmente no disponible
    SUSPENDIDA_BG = "#FEF3C7"     # Fondo
    SUSPENDIDA_ICON = "user-x"    # Icono sugerido
    SUSPENDIDA_SCHEME = "amber"   # Color scheme para rx.badge

    # =========================================================================
    # Estados de Entregable
    # =========================================================================

    # Estado: PENDIENTE (entregable - esperando que cliente suba archivos)
    # Nota: Diferente de PENDIENTE de pago, pero mismo color por consistencia
    PENDIENTE_ENTREGABLE = "#64748B"      # Gris slate - neutral/esperando
    PENDIENTE_ENTREGABLE_BG = "#F1F5F9"
    PENDIENTE_ENTREGABLE_ICON = "clock"
    PENDIENTE_ENTREGABLE_SCHEME = "gray"

    # Estado: EN_REVISION (cliente subió archivos, admin debe revisar)
    EN_REVISION = "#0284C7"               # Azul info - requiere atención
    EN_REVISION_BG = "#E0F2FE"
    EN_REVISION_ICON = "search"
    EN_REVISION_SCHEME = "sky"

    # Estado: APROBADO (admin aprobó el entregable)
    APROBADO = "#059669"                  # Verde - completado correctamente
    APROBADO_BG = "#D1FAE5"
    APROBADO_ICON = "circle-check"
    APROBADO_SCHEME = "green"

    # Estado: RECHAZADO (admin rechazó, cliente debe corregir)
    RECHAZADO = "#DC2626"                 # Rojo - requiere corrección
    RECHAZADO_BG = "#FEE2E2"
    RECHAZADO_ICON = "circle-x"
    RECHAZADO_SCHEME = "red"

    # =========================================================================
    # Estados de Pago
    # =========================================================================

    # Estado: PENDIENTE_PAGO (esperando factura del cliente)
    PENDIENTE_PAGO = "#D97706"            # Ámbar - esperando acción
    PENDIENTE_PAGO_BG = "#FEF3C7"
    PENDIENTE_PAGO_ICON = "receipt"
    PENDIENTE_PAGO_SCHEME = "amber"

    # Estado: EN_PROCESO (factura subida, esperando pago)
    EN_PROCESO = "#0284C7"                # Azul info - en trámite
    EN_PROCESO_BG = "#E0F2FE"
    EN_PROCESO_ICON = "loader"
    EN_PROCESO_SCHEME = "sky"

    # Estado: PAGADO (pago realizado)
    PAGADO = "#059669"                    # Verde - completado
    PAGADO_BG = "#D1FAE5"
    PAGADO_ICON = "badge-check"
    PAGADO_SCHEME = "green"

    @classmethod
    def get_color(cls, status: str) -> str:
        """Obtiene el color para un estado dado."""
        mapping = {
            "BORRADOR": cls.BORRADOR,
            "ACTIVO": cls.ACTIVO,
            "SUSPENDIDO": cls.SUSPENDIDO,
            "VENCIDO": cls.VENCIDO,
            "CANCELADO": cls.CANCELADO,
            "CERRADO": cls.CERRADO,
            "INACTIVO": cls.INACTIVO,
            # Estados de Plaza
            "VACANTE": cls.VACANTE,
            "OCUPADA": cls.OCUPADA,
            "SUSPENDIDA": cls.SUSPENDIDA,
            # Estados de Entregable
            "PENDIENTE": cls.PENDIENTE_ENTREGABLE,  # Para entregables
            "EN_REVISION": cls.EN_REVISION,
            "APROBADO": cls.APROBADO,
            "RECHAZADO": cls.RECHAZADO,
            # Estados de Pago
            "PENDIENTE_PAGO": cls.PENDIENTE_PAGO,
            "EN_PROCESO": cls.EN_PROCESO,
            "PAGADO": cls.PAGADO,
        }
        return mapping.get(status.upper(), cls.BORRADOR)
    
    @classmethod
    def get_bg(cls, status: str) -> str:
        """Obtiene el color de fondo para un estado dado."""
        mapping = {
            "BORRADOR": cls.BORRADOR_BG,
            "ACTIVO": cls.ACTIVO_BG,
            "SUSPENDIDO": cls.SUSPENDIDO_BG,
            "VENCIDO": cls.VENCIDO_BG,
            "CANCELADO": cls.CANCELADO_BG,
            "CERRADO": cls.CERRADO_BG,
            "INACTIVO": cls.INACTIVO_BG,
            # Estados de Plaza
            "VACANTE": cls.VACANTE_BG,
            "OCUPADA": cls.OCUPADA_BG,
            "SUSPENDIDA": cls.SUSPENDIDA_BG,
            # Estados de Entregable
            "PENDIENTE": cls.PENDIENTE_ENTREGABLE_BG,
            "EN_REVISION": cls.EN_REVISION_BG,
            "APROBADO": cls.APROBADO_BG,
            "RECHAZADO": cls.RECHAZADO_BG,
            # Estados de Pago
            "PENDIENTE_PAGO": cls.PENDIENTE_PAGO_BG,
            "EN_PROCESO": cls.EN_PROCESO_BG,
            "PAGADO": cls.PAGADO_BG,
        }
        return mapping.get(status.upper(), cls.BORRADOR_BG)
    
    @classmethod
    def get_icon(cls, status: str) -> str:
        """Obtiene el icono sugerido para un estado dado."""
        mapping = {
            "BORRADOR": cls.BORRADOR_ICON,
            "ACTIVO": cls.ACTIVO_ICON,
            "SUSPENDIDO": cls.SUSPENDIDO_ICON,
            "VENCIDO": cls.VENCIDO_ICON,
            "CANCELADO": cls.CANCELADO_ICON,
            "CERRADO": cls.CERRADO_ICON,
            "INACTIVO": cls.INACTIVO_ICON,
            # Estados de Plaza
            "VACANTE": cls.VACANTE_ICON,
            "OCUPADA": cls.OCUPADA_ICON,
            "SUSPENDIDA": cls.SUSPENDIDA_ICON,
            # Estados de Entregable
            "PENDIENTE": cls.PENDIENTE_ENTREGABLE_ICON,
            "EN_REVISION": cls.EN_REVISION_ICON,
            "APROBADO": cls.APROBADO_ICON,
            "RECHAZADO": cls.RECHAZADO_ICON,
            # Estados de Pago
            "PENDIENTE_PAGO": cls.PENDIENTE_PAGO_ICON,
            "EN_PROCESO": cls.EN_PROCESO_ICON,
            "PAGADO": cls.PAGADO_ICON,
        }
        return mapping.get(status.upper(), cls.BORRADOR_ICON)
    
    @classmethod
    def get_color_scheme(cls, status: str) -> str:
        """
        Obtiene el color_scheme para usar con rx.badge().

        Uso:
            rx.badge("ACTIVO", color_scheme=StatusColors.get_color_scheme("ACTIVO"))
        """
        mapping = {
            "BORRADOR": cls.BORRADOR_SCHEME,
            "ACTIVO": cls.ACTIVO_SCHEME,
            "SUSPENDIDO": cls.SUSPENDIDO_SCHEME,
            "VENCIDO": cls.VENCIDO_SCHEME,
            "CANCELADO": cls.CANCELADO_SCHEME,
            "CERRADO": cls.CERRADO_SCHEME,
            "INACTIVO": cls.INACTIVO_SCHEME,
            # Estados de Plaza
            "VACANTE": cls.VACANTE_SCHEME,
            "OCUPADA": cls.OCUPADA_SCHEME,
            "SUSPENDIDA": cls.SUSPENDIDA_SCHEME,
            # Estados de Entregable
            "PENDIENTE": cls.PENDIENTE_ENTREGABLE_SCHEME,
            "EN_REVISION": cls.EN_REVISION_SCHEME,
            "APROBADO": cls.APROBADO_SCHEME,
            "RECHAZADO": cls.RECHAZADO_SCHEME,
            # Estados de Pago
            "PENDIENTE_PAGO": cls.PENDIENTE_PAGO_SCHEME,
            "EN_PROCESO": cls.EN_PROCESO_SCHEME,
            "PAGADO": cls.PAGADO_SCHEME,
        }
        return mapping.get(status.upper(), cls.BORRADOR_SCHEME)


class Spacing:
    """
    Sistema de espaciado basado en múltiplos de 4px.
    
    Proporciona consistencia visual y ritmo en la interfaz.
    """
    
    NONE = "0"
    XS = "4px"        # 4px  - Espaciado mínimo (entre iconos y texto)
    SM = "8px"        # 8px  - Espaciado pequeño (padding interno compacto)
    MD = "12px"       # 12px - Espaciado medio (padding estándar)
    BASE = "16px"     # 16px - Espaciado base (margen entre elementos)
    LG = "20px"       # 20px - Espaciado grande
    XL = "24px"       # 24px - Espaciado extra grande (secciones)
    XXL = "32px"      # 32px - Espaciado muy grande (separación de bloques)
    XXXL = "48px"     # 48px - Espaciado máximo (márgenes de página)
    
    # Alias semánticos
    ICON_GAP = XS           # Espacio entre icono y texto
    INPUT_PADDING = MD      # Padding interno de inputs
    CARD_PADDING = BASE     # Padding de cards
    SECTION_GAP = XL        # Espacio entre secciones
    PAGE_PADDING = XXL      # Padding de página


class Radius:
    """
    Bordes redondeados para diferentes elementos.
    
    Estilo "medium" para apariencia profesional pero moderna.
    """
    
    NONE = "0"
    SM = "4px"        # Badges, tags pequeños
    MD = "6px"        # Botones, inputs
    LG = "8px"        # Cards, modales
    XL = "12px"       # Cards destacadas
    FULL = "9999px"   # Elementos circulares (avatars, pills)


class Shadows:
    """
    Sombras para crear jerarquía visual mediante elevación.
    
    Sutiles para mantener apariencia profesional.
    """
    
    NONE = "none"
    SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)"
    LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)"
    XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)"
    
    # Sombras con color (para estados)
    FOCUS = f"0 0 0 3px {Colors.PRIMARY_LIGHT}"  # Ring de focus
    ERROR = f"0 0 0 3px {Colors.ERROR_LIGHT}"    # Ring de error


class Transitions:
    """
    Duraciones de animación optimizadas para usuarios +42 años.
    
    - Perceptibles pero no lentas
    - Rango 150-200ms es óptimo
    """
    
    FAST = "100ms ease"       # Hover, micro-interacciones
    NORMAL = "200ms ease"     # Sidebar, modales
    SLOW = "300ms ease"       # Animaciones decorativas (poco uso)
    
    # Funciones de easing específicas
    EASE_OUT = "200ms ease-out"     # Elementos que aparecen
    EASE_IN = "150ms ease-in"       # Elementos que desaparecen
    EASE_IN_OUT = "200ms ease-in-out"  # Transformaciones


class Typography:
    """
    Sistema tipográfico optimizado para legibilidad.
    
    - Fuente: Source Sans Pro (oficial BUAP)
    - Tamaño base: 16px (mínimo para usuarios +42)
    - Escala: Modular para jerarquía clara
    """
    
    # Familia tipográfica
    FONT_FAMILY = "'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    
    # Tamaños de fuente
    SIZE_XS = "12px"      # Caption, metadata no crítica
    SIZE_SM = "14px"      # Etiquetas, texto secundario
    SIZE_BASE = "16px"    # Cuerpo de texto (mínimo para +42)
    SIZE_LG = "18px"      # Subtítulos, énfasis
    SIZE_XL = "20px"      # Títulos de sección
    SIZE_2XL = "24px"     # Títulos de card/modal
    SIZE_3XL = "28px"     # Títulos de página
    SIZE_4XL = "32px"     # Títulos principales
    
    # Pesos de fuente
    WEIGHT_REGULAR = "400"
    WEIGHT_MEDIUM = "500"
    WEIGHT_SEMIBOLD = "600"
    WEIGHT_BOLD = "700"
    
    # Altura de línea
    LINE_HEIGHT_TIGHT = "1.25"    # Títulos
    LINE_HEIGHT_NORMAL = "1.5"   # Cuerpo de texto
    LINE_HEIGHT_RELAXED = "1.75" # Texto largo, lectura
    
    # Espaciado entre letras
    LETTER_SPACING_TIGHT = "-0.025em"  # Títulos grandes
    LETTER_SPACING_NORMAL = "0"
    LETTER_SPACING_WIDE = "0.025em"    # Labels, caps


class Breakpoints:
    """
    Puntos de quiebre responsive.
    
    Aunque el sistema es desktop-first, definimos breakpoints
    para componentes que necesiten adaptarse.
    """
    
    SM = "640px"      # Móvil grande
    MD = "768px"      # Tablet
    LG = "1024px"     # Desktop pequeño
    XL = "1280px"     # Desktop
    XXL = "1536px"    # Desktop grande


class Sidebar:
    """
    Configuración específica del sidebar colapsable.
    """
    
    WIDTH_EXPANDED = "240px"     # Ancho expandido
    WIDTH_COLLAPSED = "72px"     # Ancho colapsado (solo iconos)
    TRANSITION = Transitions.NORMAL
    BG_COLOR = Colors.SURFACE
    BORDER_COLOR = Colors.BORDER


class ZIndex:
    """
    Capas de apilamiento (z-index) para elementos superpuestos.
    """
    
    BASE = "0"
    DROPDOWN = "10"
    STICKY = "20"
    FIXED = "30"
    MODAL_BACKDROP = "40"
    MODAL = "50"
    POPOVER = "60"
    TOOLTIP = "70"


# =============================================================================
# ESTILOS COMPUESTOS (Combinaciones frecuentes)
# =============================================================================

class ButtonStyles:
    """Estilos base para botones."""
    
    BASE = {
        "font_family": Typography.FONT_FAMILY,
        "font_weight": Typography.WEIGHT_MEDIUM,
        "font_size": Typography.SIZE_SM,
        "border_radius": Radius.MD,
        "transition": Transitions.FAST,
        "cursor": "pointer",
    }
    
    PRIMARY = {
        **BASE,
        "background": Colors.PRIMARY,
        "color": Colors.TEXT_INVERSE,
        "_hover": {
            "background": Colors.PRIMARY_HOVER,
        },
    }
    
    SECONDARY = {
        **BASE,
        "background": Colors.SECONDARY_LIGHT,
        "color": Colors.TEXT_PRIMARY,
        "_hover": {
            "background": Colors.BORDER,
        },
    }
    
    GHOST = {
        **BASE,
        "background": "transparent",
        "color": Colors.TEXT_PRIMARY,
        "_hover": {
            "background": Colors.SURFACE_HOVER,
        },
    }


class CardStyles:
    """Estilos base para cards."""
    
    BASE = {
        "background": Colors.SURFACE,
        "border_radius": Radius.LG,
        "border": f"1px solid {Colors.BORDER}",
        "padding": Spacing.CARD_PADDING,
        "transition": Transitions.FAST,
    }
    
    INTERACTIVE = {
        **BASE,
        "_hover": {
            "box_shadow": Shadows.MD,
            "border_color": Colors.BORDER_STRONG,
        },
    }


class InputStyles:
    """Estilos base para inputs."""
    
    BASE = {
        "font_family": Typography.FONT_FAMILY,
        "font_size": Typography.SIZE_BASE,
        "padding": Spacing.INPUT_PADDING,
        "border_radius": Radius.MD,
        "border": f"1px solid {Colors.BORDER}",
        "background": Colors.SURFACE,
        "transition": Transitions.FAST,
        "_focus": {
            "border_color": Colors.BORDER_FOCUS,
            "box_shadow": Shadows.FOCUS,
            "outline": "none",
        },
        "_placeholder": {
            "color": Colors.TEXT_MUTED,
        },
    }