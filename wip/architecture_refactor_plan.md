# Architecture Refactor Plan

## Objetivo

Ejecutar la reducción de duplicación y la centralización arquitectónica del dashboard en tres frentes:

1. Servicios con acceso directo a Supabase.
2. States grandes de CRUD y formularios.
3. Contratos compartidos de serialización, carga y manejo de errores.

## Orden de ejecución

### 1. Servicios

- Consolidar patrones repetidos en `app/services/direct_service.py`.
- Migrar primero servicios singleton por empresa:
  - `configuracion_fiscal_service.py`
  - `configuracion_operativa_service.py`
- Migrar después catálogos directos:
  - `contacto_buap_service.py`
  - `institucion_service.py`
  - `sede_service.py`

### 2. State compartido

- Consolidar en `BaseState`:
  - serialización de modelos para Reflex,
  - carga/asignación estándar de listas,
  - manejo uniforme de error y limpieza de listas.

### 3. States de alto impacto

- Aplicar helpers compartidos primero en:
  - `app/presentation/pages/empleados/empleados_state.py`
  - `app/presentation/portal/pages/mis_empleados/state.py`
  - `app/presentation/pages/contratos/contratos_state.py`

## Pendientes siguientes

- Migrar `sede_service.py` al helper de acceso directo.
- Reusar `serializar_lista_state` donde todavía hay `model_dump()` inline.
- Partir módulos monolíticos:
  - `asistencia_service.py`
  - `user_service.py`
  - `contratos_state.py`
  - `empleados_state.py`
