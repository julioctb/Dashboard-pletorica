# Changelog

Todas las versiones notables del proyecto se documentan en este archivo.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
versionamiento basado en [Semantic Versioning](https://semver.org/lang/es/).

## [0.6.0] - 2026-02-25

### Added
- Pivot SaaS de roles y modelo institucional (roles de plataforma/empresa, instituciones e instituciones_empresas)
- Panel Super Admin con dashboard y dispatcher de ruta raiz por rol/contexto
- Modulo de Instituciones (CRUD y gestion de empresas vinculadas)
- Modulo Admin Onboarding para gestion administrativa del flujo de alta
- Portal de onboarding (alta de empleado) y autoservicio de empleado (`mis_datos`)
- Portal de expedientes digitales con carga/consulta de documentos de empleado
- Configuracion operativa por empresa en portal (parametros de pago/bloqueo)
- API v1 para onboarding y validacion CURP (RENAPO), con helpers comunes de respuestas/errores
- Flujo de documentos de empleado con validacion, rechazo y versionamiento
- Historial inmutable de cambios de cuenta bancaria con auditoria
- Componentes reutilizables para formularios/listas de empleados, onboarding y documentos
- Validadores centralizados por dominio (empresa, empleado, contrato, pagos, sedes, usuarios)

### Changed
- Sidebar del portal filtrado por `rol_empresa` del usuario
- Guards del portal para usuarios sin empresa y header dinamico por contexto
- Refactor de States/Repositories/Services para reducir duplicacion
- Refactor de navegacion/layout y primitives reutilizables de tablas/UI
- Paralelizacion de metricas de dashboard y mejoras de logging en excepciones silenciadas
- Migraciones 034-039 para soportar pivot SaaS, onboarding extendido y configuracion operativa
- Version visible del sidebar y metadata de API alineadas a `APP_VERSION`

### Fixed
- Crash del sidebar y manejo de `Var` booleana en secciones de formulario
- Restauracion del panel super admin tras perdida por force push
- Compatibilidad legacy en `ui_helpers` (`es_filtro_activo` y constantes relacionadas)

### Tests
- Pruebas para helpers comunes de API y `query_helpers`

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
