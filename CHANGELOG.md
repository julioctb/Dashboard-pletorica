# Changelog

Todas las versiones notables del proyecto se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
versionamiento basado en [Semantic Versioning](https://semver.org/lang/es/).

## [0.5.0] - 2026-02-10

### Added
- Modal detalle/revision reutilizando wizard en modo solo-lectura
- Folio de requisicion (REQ-SA-XXXX) se genera al aprobar
- Modal de confirmacion de folio generado
- Navegacion por pasos sin validacion en modo detalle
- Botones Aprobar/Rechazar en paso 8 del wizard de revision
- Auto-transicion ENVIADA -> EN_REVISION al abrir revision
- Callout con comentario de rechazo anterior visible al creador
- Sistema de permisos granulares por modulo y accion
- Notificaciones al enviar, aprobar y rechazar requisiciones
- Boton centralizado `boton_guardar` / `boton_eliminar` con loading state
- Indicador visual de requisiciones rechazadas en tabla
- Botones de tabla centralizados (`tabla_action_button`)
- Visor de archivos en modo detalle

### Changed
- Columna de tabla muestra "(Sin folio)" en vez de "(Borrador)"
- Migracion 033: permisos granulares

## [0.4.0] - 2026-02-08

### Added
- Modulo de Entregables con detalle por contrato
- Flujo Requisicion -> Contrato (adjudicar -> contratar)
- Dashboard con metricas y graficas
- Auto-borrador en requisiciones para habilitar archivos al crear
- Sistema de archivos con compresion automatica (WebP, PDF)

### Changed
- Modales solo cierran con boton (no click fuera)
- Mejoras UI generales

## [0.3.0] - 2026-02-05

### Added
- Modulo Requisiciones completo (wizard 8 pasos, items, transiciones de estado)
- Modulo Sedes BUAP con contactos
- Sistema de autenticacion (Supabase Auth, JWT, roles)
- Portal de Cliente (dashboard, empresa, empleados, contratos, alta masiva)
- Admin de usuarios con asignacion de empresas
- Restricciones de empleados y reingreso en historial laboral
- Generacion de PDF para requisiciones (fpdf2)
- Configuracion de defaults para requisiciones

### Changed
- Refactoring de BaseState con loading/saving/error handling centralizado
- Modularizacion de paginas grandes (empleados, mis_empleados, alta_masiva)
- Migracion de colores hardcoded a tokens en portal

## [0.2.0] - 2026-01-28

### Added
- Modulo Contratos con tabs y configuracion de personal
- Modulo Plazas con breadcrumb centralizado
- Modulo Empleados con filtros y busqueda
- Modulo Historial Laboral automatico
- Modulo Categorias de Puesto con auto-generacion de clave
- Capa API REST (FastAPI) con Swagger y ReDoc
- Sistema de validacion centralizado (FieldConfig, pydantic_field, campo_validador)
- Catalogos fiscales y laborales en app/core

### Changed
- Centralizar validaciones, mensajes y enums en app/core
- Centralizar normalizacion de texto en text_utils
- BaseRepository generico con CRUD, busqueda y paginacion
- Componentes UI reutilizables (form_input, form_select, tabla, modal)

## [0.1.0] - 2026-01-15

### Added
- Arquitectura inicial: Reflex + Supabase
- Modulo Empresas con CRUD completo, filtros y tarjetas
- Modulo Tipos de Servicio
- Simulador de costo patronal (IMSS, ISR)
- Dashboard basico
- Theme tokens (Colors, Spacing, Typography)
- Migraciones SQL (000-014)
- Configuracion de entorno (.env, Config)
