"""
Catálogos de datos estáticos para la aplicación.

Centraliza listas de opciones, mapeos y constantes de dominio
reutilizables en toda la aplicación.

Responsabilidad:
- Proveer catálogos de datos maestros (estados, tipos, estatus, etc.)
- Mantener mapeos clave-valor para UI
- Facilitar búsquedas y validaciones de catálogos

Uso:
    from app.core.catalogos import ESTADOS_DISPLAY, ESTADOS_LISTA

    # En formularios
    rx.select(ESTADOS_LISTA, ...)

    # Validaciones
    if estado_key in ESTADOS_DISPLAY:
        ...
"""

# =============================================================================
# ESTADOS DE MÉXICO (32 estados)
# =============================================================================

ESTADOS_DISPLAY = {
    "aguascalientes": "Aguascalientes",
    "baja_california": "Baja California",
    "baja_california_sur": "Baja California Sur",
    "campeche": "Campeche",
    "chiapas": "Chiapas",
    "chihuahua": "Chihuahua",
    "ciudad_de_mexico": "Ciudad de México",
    "coahuila": "Coahuila",
    "colima": "Colima",
    "durango": "Durango",
    "estado_de_mexico": "Estado de México",
    "guanajuato": "Guanajuato",
    "guerrero": "Guerrero",
    "hidalgo": "Hidalgo",
    "jalisco": "Jalisco",
    "michoacan": "Michoacán",
    "morelos": "Morelos",
    "nayarit": "Nayarit",
    "nuevo_leon": "Nuevo León",
    "oaxaca": "Oaxaca",
    "puebla": "Puebla",
    "queretaro": "Querétaro",
    "quintana_roo": "Quintana Roo",
    "san_luis_potosi": "San Luis Potosí",
    "sinaloa": "Sinaloa",
    "sonora": "Sonora",
    "tabasco": "Tabasco",
    "tamaulipas": "Tamaulipas",
    "tlaxcala": "Tlaxcala",
    "veracruz": "Veracruz",
    "yucatan": "Yucatán",
    "zacatecas": "Zacatecas"
}

# Lista ordenada alfabéticamente para select/dropdown
ESTADOS_LISTA = sorted(ESTADOS_DISPLAY.values())

# Diccionario inverso: "Puebla" -> "puebla"
ESTADOS_DISPLAY_INVERSO = {v: k for k, v in ESTADOS_DISPLAY.items()}


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def obtener_clave_estado(nombre_display: str) -> str | None:
    """
    Convierte nombre display a clave interna.

    Args:
        nombre_display: Nombre visible del estado (ej: "Puebla")

    Returns:
        Clave interna (ej: "puebla") o None si no existe

    Ejemplo:
        >>> obtener_clave_estado("Puebla")
        "puebla"
        >>> obtener_clave_estado("Ciudad de México")
        "ciudad_de_mexico"
    """
    return ESTADOS_DISPLAY_INVERSO.get(nombre_display)


def validar_estado(clave: str) -> bool:
    """
    Valida si una clave de estado existe.

    Args:
        clave: Clave interna del estado

    Returns:
        True si existe, False en caso contrario

    Ejemplo:
        >>> validar_estado("puebla")
        True
        >>> validar_estado("invalid")
        False
    """
    return clave in ESTADOS_DISPLAY


# =============================================================================
# FUTUROS CATÁLOGOS (Preparados para expansión)
# =============================================================================

# Descomentar y completar según necesidad:

TIPO_SALARIO_CALCULO ={
    "salario_bruto" : "Salario Bruto",
    "salario_neto"  : "Salario Neto (inverso)",
    "salario_min"   : "Salario Mínimo"
}

# TIPOS_EMPRESA_DISPLAY = {
#     "nomina": "Nómina",
#     "subcontratacion": "Subcontratación",
#     "mixto": "Mixto"
# }

# ESTATUS_DISPLAY = {
#     "activo": "Activo",
#     "inactivo": "Inactivo",
#     "suspendido": "Suspendido"
# }

# PERIODICIDADES_PAGO_DISPLAY = {
#     "semanal": "Semanal",
#     "quincenal": "Quincenal",
#     "mensual": "Mensual"
# }

# BANCOS_MEXICO = {
#     "banamex": "Citibanamex",
#     "bancomer": "BBVA México",
#     "santander": "Santander",
#     "banorte": "Banorte",
#     # ... más bancos
# }
