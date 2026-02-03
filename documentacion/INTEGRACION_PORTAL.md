# Integracion del Portal de Cliente

## Estructura de Archivos

```
app/presentation/portal/
├── __init__.py
├── layout/
│   ├── __init__.py
│   ├── portal_layout.py      # portal_index() - wrapper con sidebar
│   └── portal_sidebar.py     # Sidebar simplificado (teal)
├── pages/
│   ├── __init__.py
│   ├── portal_dashboard.py   # Dashboard con metricas
│   ├── mi_empresa.py         # Datos de empresa (solo lectura)
│   ├── mis_empleados.py      # Lista de empleados (solo lectura)
│   └── mis_contratos.py      # Lista de contratos (solo lectura)
└── state/
    ├── __init__.py
    └── portal_state.py        # State base: auth + metricas
```

## Rutas Registradas en app.py

| Ruta | Pagina | Layout |
|------|--------|--------|
| `/portal` | `portal_dashboard_page` | `portal_index` |
| `/portal/mi-empresa` | `mi_empresa_page` | `portal_index` |
| `/portal/empleados` | `mis_empleados_page` | `portal_index` |
| `/portal/contratos` | `mis_contratos_page` | `portal_index` |

## Redireccion por Rol

En `auth_state.py`, el metodo `iniciar_sesion()` redirige segun el rol:

- `rol == 'client'` -> `/portal`
- Cualquier otro rol (admin) -> `/`

## Proteccion de Rutas

Cada pagina del portal hereda de `PortalState`, que a su vez hereda de `AuthState`.

El metodo `on_mount_portal()` verifica:
1. Sesion valida (via `verificar_y_redirigir()`) - si no, redirige a `/login`
2. Si es admin, redirige a `/` (el admin no debe usar el portal)
3. Si no tiene empresa asignada, muestra error

### Proteccion cruzada

- **Admin accede a `/portal/*`**: Redirigido a `/` por `on_mount_portal()`
- **Client accede a `/*` (backoffice)**: Depende de que cada pagina del backoffice use `verificar_y_redirigir()` en su on_mount. Las paginas que heredan de `AuthState` pueden verificar `self.es_admin` y redirigir.

## Agregar Nueva Pagina al Portal

1. Crear archivo en `app/presentation/portal/pages/nueva_pagina.py`
2. Crear state que herede de `PortalState`
3. Implementar `on_mount_nueva_pagina` que llame a `self.on_mount_portal()`
4. Agregar ruta en `app.py`:
   ```python
   from .presentation.portal.pages.nueva_pagina import nueva_pagina_page
   app.add_page(lambda: portal_index(nueva_pagina_page()), route="/portal/nueva-ruta")
   ```
5. Agregar item en `PORTAL_NAVIGATION` en `portal_sidebar.py`

## Sidebar del Portal

Configuracion de navegacion en `portal_sidebar.py`:

```python
PORTAL_NAVIGATION = [
    {"label": None, "items": [
        {"text": "Dashboard", "icon": "layout-dashboard", "href": "/portal"},
    ]},
    {"label": "Mi Empresa", "items": [
        {"text": "Datos Empresa", "icon": "building-2", "href": "/portal/mi-empresa"},
        {"text": "Empleados", "icon": "users", "href": "/portal/empleados"},
    ]},
    {"label": "Operacion", "items": [
        {"text": "Contratos", "icon": "file-text", "href": "/portal/contratos"},
        {"text": "Plazas", "icon": "briefcase", "href": "/portal/plazas"},
        {"text": "Requisiciones", "icon": "clipboard-list", "href": "/portal/requisiciones"},
    ]},
]
```

Nota: Las rutas `/portal/plazas` y `/portal/requisiciones` estan en el sidebar pero aun no tienen pagina implementada. Se pueden agregar mas adelante.
