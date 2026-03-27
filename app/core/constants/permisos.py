"""
Constantes compartidas para el sistema de permisos de usuarios por empresa.

Usadas en el backoffice (admin/usuarios) y en el portal (usuarios_empresa).
"""

# Permisos por defecto (todo desactivado)
PERMISOS_DEFAULT: dict = {
    "requisiciones": {"operar": False, "autorizar": False},
    "entregables": {"operar": False, "autorizar": False},
    "pagos": {"operar": False, "autorizar": False},
    "contratos": {"operar": False, "autorizar": False},
    "empresas": {"operar": False, "autorizar": False},
    "empleados": {"operar": False, "autorizar": False},
}

# Módulos que tienen flujo de autorización (dos acciones: operar + autorizar)
MODULOS_CON_AUTORIZACION: set = {"requisiciones", "entregables", "pagos"}

# Definición estática de módulos para la matriz de permisos
MODULOS_PERMISOS: list[dict] = [
    {"modulo": "requisiciones", "label": "Requisiciones", "tiene_autorizar": True},
    {"modulo": "entregables", "label": "Entregables", "tiene_autorizar": True},
    {"modulo": "pagos", "label": "Pagos", "tiene_autorizar": True},
    {"modulo": "contratos", "label": "Contratos", "tiene_autorizar": False},
    {"modulo": "empresas", "label": "Empresas", "tiene_autorizar": False},
    {"modulo": "empleados", "label": "Empleados", "tiene_autorizar": False},
]

# Todos los roles asignables por un superadmin/admin backoffice
OPCIONES_ROLES_EMPRESA: list[dict] = [
    {"label": "Administrador de Empresa", "value": "admin_empresa"},
    {"label": "RRHH", "value": "rrhh"},
    {"label": "Operaciones", "value": "operaciones"},
    {"label": "Contabilidad", "value": "contabilidad"},
    {"label": "Solo lectura", "value": "lectura"},
]

# Roles asignables por un admin_empresa (no puede crear otro admin_empresa)
ROLES_ASIGNABLES_POR_ADMIN_EMPRESA: list[dict] = [
    {"label": "RRHH", "value": "rrhh"},
    {"label": "Operaciones", "value": "operaciones"},
    {"label": "Contabilidad", "value": "contabilidad"},
    {"label": "Solo lectura", "value": "lectura"},
]
