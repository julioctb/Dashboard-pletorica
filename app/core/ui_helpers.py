"""
UI Helpers - Utilidades para componentes de interfaz.

Centraliza:
- Generación de opciones para selects desde enums
- Formateo de datos para display
- Constantes de filtros
- Helpers para formularios

Uso:
    from app.core.ui_helpers import (
        opciones_desde_enum,
        opciones_si_no,
        FILTRO_TODOS,
        FILTRO_SIN_SELECCION,
    )

    # En state:
    @rx.var
    def opciones_estatus(self) -> List[dict]:
        return opciones_desde_enum(EstatusEmpleado, incluir_todos=True)
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Type
from decimal import Decimal, InvalidOperation


# =============================================================================
# CONSTANTES DE FILTROS
# =============================================================================

FILTRO_TODOS = "__TODOS__"
FILTRO_SIN_SELECCION = ""
FILTRO_TODAS = "__TODAS__"  # Alias femenino


# =============================================================================
# GENERADORES DE OPCIONES
# =============================================================================

def opciones_desde_enum(
    enum_class: Type[Enum],
    incluir_todos: bool = False,
    todos_label: str = "Todos",
    todos_value: str = FILTRO_TODOS,
    usar_descripcion: bool = True
) -> List[Dict[str, str]]:
    """
    Genera lista de opciones para rx.select desde un Enum.

    Args:
        enum_class: Clase Enum a convertir
        incluir_todos: Si True, agrega opción "Todos" al inicio
        todos_label: Texto para la opción "Todos"
        todos_value: Valor para la opción "Todos"
        usar_descripcion: Si True, usa .descripcion si existe, sino .value

    Returns:
        Lista de dicts con 'value' y 'label'

    Ejemplo:
        >>> opciones_desde_enum(EstatusEmpleado, incluir_todos=True)
        [
            {"value": "__TODOS__", "label": "Todos"},
            {"value": "ACTIVO", "label": "Activo"},
            {"value": "INACTIVO", "label": "Inactivo"},
            {"value": "SUSPENDIDO", "label": "Suspendido"},
        ]
    """
    opciones = []

    if incluir_todos:
        opciones.append({"value": todos_value, "label": todos_label})

    for item in enum_class:
        # Intentar usar .descripcion si existe
        if usar_descripcion and hasattr(item, 'descripcion'):
            label = item.descripcion
        else:
            # Capitalizar el value: "ACTIVO" -> "Activo"
            label = item.value.replace('_', ' ').title()

        opciones.append({
            "value": item.value,
            "label": label
        })

    return opciones


def opciones_desde_lista(
    items: List[Any],
    value_field: str = 'id',
    label_field: str = 'nombre',
    incluir_vacio: bool = False,
    vacio_label: str = "Seleccione...",
    vacio_value: str = FILTRO_SIN_SELECCION
) -> List[Dict[str, str]]:
    """
    Genera lista de opciones desde una lista de dicts u objetos.

    Args:
        items: Lista de dicts u objetos
        value_field: Campo a usar como value
        label_field: Campo a usar como label
        incluir_vacio: Si True, agrega opción vacía al inicio
        vacio_label: Texto para la opción vacía
        vacio_value: Valor para la opción vacía

    Returns:
        Lista de dicts con 'value' y 'label'

    Ejemplo:
        >>> empresas = [{"id": 1, "nombre": "ACME"}, {"id": 2, "nombre": "Corp"}]
        >>> opciones_desde_lista(empresas, incluir_vacio=True)
        [
            {"value": "", "label": "Seleccione..."},
            {"value": "1", "label": "ACME"},
            {"value": "2", "label": "Corp"},
        ]
    """
    opciones = []

    if incluir_vacio:
        opciones.append({"value": vacio_value, "label": vacio_label})

    for item in items:
        if isinstance(item, dict):
            value = item.get(value_field, '')
            label = item.get(label_field, '')
        else:
            value = getattr(item, value_field, '')
            label = getattr(item, label_field, '')

        opciones.append({
            "value": str(value),
            "label": str(label)
        })

    return opciones


def opciones_si_no(
    si_label: str = "Sí",
    no_label: str = "No",
    incluir_todos: bool = False,
    todos_label: str = "Todos"
) -> List[Dict[str, str]]:
    """
    Genera opciones para filtros booleanos Sí/No.

    Args:
        si_label: Texto para True
        no_label: Texto para False
        incluir_todos: Si True, agrega opción "Todos"
        todos_label: Texto para "Todos"

    Returns:
        Lista de opciones
    """
    opciones = []

    if incluir_todos:
        opciones.append({"value": FILTRO_TODOS, "label": todos_label})

    opciones.extend([
        {"value": "true", "label": si_label},
        {"value": "false", "label": no_label},
    ])

    return opciones


# =============================================================================
# FORMATEO DE DATOS
# =============================================================================

def formatear_moneda(valor: Any, prefijo: str = "$", decimales: int = 2) -> str:
    """
    Formatea un valor como moneda mexicana.

    Args:
        valor: Número, string o Decimal a formatear
        prefijo: Símbolo de moneda
        decimales: Número de decimales

    Returns:
        String formateado (ej: "$1,234.56")

    Ejemplo:
        >>> formatear_moneda(1234.5)
        "$1,234.50"
        >>> formatear_moneda("1234.567", decimales=2)
        "$1,234.57"
    """
    try:
        if valor is None or valor == "":
            return ""

        # Limpiar string
        if isinstance(valor, str):
            valor = valor.replace("$", "").replace(",", "").strip()
            if not valor:
                return ""

        numero = Decimal(str(valor))
        formateado = f"{numero:,.{decimales}f}"
        return f"{prefijo}{formateado}"

    except (InvalidOperation, ValueError):
        return str(valor) if valor else ""


def parsear_moneda(valor: str) -> Optional[Decimal]:
    """
    Parsea un string de moneda a Decimal.

    Args:
        valor: String con formato moneda (ej: "$1,234.56")

    Returns:
        Decimal o None si no es válido

    Ejemplo:
        >>> parsear_moneda("$1,234.56")
        Decimal('1234.56')
    """
    try:
        if not valor:
            return None
        limpio = valor.replace("$", "").replace(",", "").strip()
        if not limpio:
            return None
        return Decimal(limpio)
    except (InvalidOperation, ValueError):
        return None


def formatear_telefono(valor: str) -> str:
    """
    Formatea un teléfono a formato mexicano (10 dígitos).

    Args:
        valor: String con dígitos

    Returns:
        Formato "(55) 1234-5678" o string original si no tiene 10 dígitos
    """
    if not valor:
        return ""

    # Solo dígitos
    digitos = ''.join(c for c in valor if c.isdigit())

    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"

    return valor


def truncar_texto(texto: str, max_length: int = 50, sufijo: str = "...") -> str:
    """
    Trunca texto largo agregando sufijo.

    Args:
        texto: Texto a truncar
        max_length: Longitud máxima
        sufijo: Sufijo a agregar si se trunca

    Returns:
        Texto truncado o original si es más corto
    """
    if not texto:
        return ""
    if len(texto) <= max_length:
        return texto
    return texto[:max_length - len(sufijo)] + sufijo


# =============================================================================
# HELPERS DE FORMULARIOS
# =============================================================================

def normalizar_para_busqueda(texto: str) -> str:
    """
    Normaliza texto para búsquedas (mayúsculas, sin espacios extra).

    Args:
        texto: Texto a normalizar

    Returns:
        Texto normalizado
    """
    if not texto:
        return ""
    return " ".join(texto.upper().split())


def es_filtro_activo(valor: str) -> bool:
    """
    Verifica si un valor de filtro está activo (no es "todos" ni vacío).

    Args:
        valor: Valor del filtro

    Returns:
        True si el filtro está activo
    """
    return valor not in (FILTRO_TODOS, FILTRO_TODAS, FILTRO_SIN_SELECCION, "", None)


def limpiar_filtros_dict(filtros: Dict[str, Any]) -> Dict[str, Any]:
    """
    Limpia un dict de filtros removiendo valores vacíos/todos.

    Args:
        filtros: Dict con filtros

    Returns:
        Dict solo con filtros activos
    """
    return {k: v for k, v in filtros.items() if es_filtro_activo(v)}


# =============================================================================
# PAGINACIÓN
# =============================================================================

def calcular_paginas(total: int, por_pagina: int) -> int:
    """
    Calcula número total de páginas.

    Args:
        total: Total de registros
        por_pagina: Registros por página

    Returns:
        Número de páginas (mínimo 1)
    """
    if total <= 0 or por_pagina <= 0:
        return 1
    return (total + por_pagina - 1) // por_pagina


def calcular_offset(pagina: int, por_pagina: int) -> int:
    """
    Calcula offset para paginación.

    Args:
        pagina: Página actual (1-indexed)
        por_pagina: Registros por página

    Returns:
        Offset para query
    """
    if pagina < 1:
        pagina = 1
    return (pagina - 1) * por_pagina


def rango_paginacion(pagina: int, total_paginas: int, visible: int = 5) -> List[int]:
    """
    Genera rango de páginas visibles para paginador.

    Args:
        pagina: Página actual
        total_paginas: Total de páginas
        visible: Cantidad de páginas a mostrar

    Returns:
        Lista de números de página

    Ejemplo:
        >>> rango_paginacion(5, 10, visible=5)
        [3, 4, 5, 6, 7]
    """
    if total_paginas <= visible:
        return list(range(1, total_paginas + 1))

    mitad = visible // 2
    inicio = max(1, pagina - mitad)
    fin = min(total_paginas, inicio + visible - 1)

    # Ajustar si estamos cerca del final
    if fin - inicio < visible - 1:
        inicio = max(1, fin - visible + 1)

    return list(range(inicio, fin + 1))
