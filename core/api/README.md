# API REST - SaaS Nomina BUAP

API REST montada sobre Reflex via `api_transformer`. Coexiste con la UI de Reflex en el mismo servidor.

## Acceso

| Recurso | URL |
|---------|-----|
| Swagger UI | `http://localhost:3000/api/docs` |
| ReDoc | `http://localhost:3000/api/redoc` |
| OpenAPI JSON | `http://localhost:3000/api/openapi.json` |
| Endpoints | `http://localhost:3000/api/v1/...` |

## Variables de entorno

```bash
# .env
API_AUTH_ENABLED=false    # true = exige Bearer token
API_CORS_ORIGINS=*        # Origenes permitidos (separados por coma)
```

## Endpoints disponibles

### Empresas

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/v1/empresas` | Listar empresas |
| GET | `/api/v1/empresas/{id}` | Obtener empresa por ID |

**Query params** (GET /empresas):
- `incluir_inactivas` (bool, default: false)
- `busqueda` (string, min 2 chars)

## Formato de respuesta

Todas las respuestas usan el formato estandar:

```json
{
  "success": true,
  "data": [...],
  "total": 10,
  "message": null
}
```

Error:
```json
{
  "success": false,
  "data": null,
  "total": 0,
  "message": "Descripcion del error"
}
```

## Autenticacion

- `API_AUTH_ENABLED=false`: Sin autenticacion (desarrollo)
- `API_AUTH_ENABLED=true`: Requiere header `Authorization: Bearer <token>`

Rutas excluidas de auth: `/api/docs`, `/api/redoc`, `/api/openapi.json`

## Agregar un nuevo modulo

1. Crear carpeta: `app/api/v1/<modulo>/`
2. Crear `__init__.py`, `router.py`, `schemas.py`
3. Registrar en `app/api/v1/router.py`:

```python
from app.api.v1.<modulo>.router import router as <modulo>_router
api_v1_router.include_router(<modulo>_router)
```

## Arquitectura

```
Presentation (Reflex States)  -->  Services  -->  Repositories  -->  Database
API (FastAPI Endpoints)        -->  Services  -->  Repositories  -->  Database
```

Ambas capas (Presentation y API) consumen los mismos servicios.
Los endpoints no duplican logica de negocio.
