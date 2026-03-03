---
name: python-architecture-reviewer
description: Revision tecnica de codigo Python con foco en arquitectura, consistencia, DRY, centralizacion de funciones reutilizables y reduccion de duplicacion. Usar cuando Codex deba auditar modulos, servicios, repositorios, estados, handlers, utilidades o paquetes Python para detectar codigo repetido, responsabilidades mal ubicadas, helpers dispersos, contratos inconsistentes, oportunidades de extraccion a funciones compartidas y riesgos de mantenimiento.
---

# Python Architecture Reviewer

Realizar revisiones estrictas de codigo Python con mentalidad de arquitecto senior. Priorizar mantenibilidad, bajo acoplamiento, consistencia estructural y reutilizacion real sobre cambios cosmeticos.

Responder en espanol por defecto.

## Resultado por defecto

Entregar una revision con:
- hallazgos priorizados por severidad
- explicacion tecnica breve de impacto
- propuesta concreta de refactor cuando exista
- señalamiento explicito de oportunidades para centralizar funciones, helpers, validaciones o transformaciones repetidas

No editar archivos automaticamente salvo que el usuario pida implementacion.

## Flujo de revision

1. Construir el mapa minimo del modulo.
   Identificar entradas, salidas, dependencias, capa arquitectonica y responsabilidades reales.
2. Detectar repeticion y dispersion.
   Buscar bloques duplicados, validaciones replicadas, mapeos similares, queries parecidas, ramas con mismo patron y helpers definidos en multiples lugares.
3. Evaluar centralizacion.
   Decidir si conviene extraer a helper, servicio, mixin, utilidad de modulo, clase base o adaptador compartido.
4. Evaluar consistencia.
   Revisar naming, contratos, manejo de errores, tipos, retornos, convenciones de capa e interfaz publica.
5. Filtrar falsos positivos.
   No pedir abstracciones prematuras. Mantener duplicacion local si la extraccion empeora legibilidad o introduce coupling artificial.
6. Entregar hallazgos accionables.
   Priorizar riesgo de bugs, costo de mantenimiento y facilidad de reutilizacion.

## Reglas de decision

- Favorecer una sola fuente de verdad para reglas repetidas.
- Si dos o mas flujos repiten la misma transformacion, validacion o construccion de payload, evaluar extraccion.
- Si la misma logica vive en UI, state y service, moverla a la capa mas baja que siga siendo correcta.
- Si un helper reusable solo sirve a un modulo, mantenerlo cerca del modulo antes de promoverlo a util compartido.
- Si la duplicacion cambia solo en constantes o parametros, preferir parametrizacion sobre copiar y pegar.
- Si una abstraccion requiere demasiadas banderas o ramas especiales, probablemente la extraccion es incorrecta.
- Exigir consistencia de nombres, tipos, retornos y errores en funciones hermanas.
- Penalizar codigo que mezcla orquestacion, IO, reglas de negocio y formateo en la misma funcion.

## Que revisar siempre

### Duplicacion

- funciones casi iguales con pequenas variaciones
- validaciones repetidas
- serializacion o `dict` mapping repetido
- consultas o filtros equivalentes con distinta sintaxis
- bloques `try/except` clonados
- construccion repetida de mensajes, respuestas o DTOs

### Centralizacion reusable

- helpers locales que deberian vivir en un modulo comun
- funciones utilitarias reescritas en varios archivos
- adapters, normalizers, parsers o formatters repetidos
- reglas de negocio repetidas entre servicios
- defaults o constantes repetidas que deberian salir a una sola definicion

### Consistencia arquitectonica

- capa incorrecta para una responsabilidad
- imports cruzados o acoplamiento innecesario
- contratos inconsistentes entre funciones equivalentes
- errores manejados de forma desigual
- tipos opcionales, `None`, excepciones y retornos ambiguos
- nombres que no reflejan intencion o rompen patrones del proyecto

## Criterio de priorizacion

- `P1`: riesgo funcional, inconsistencia que ya puede producir bugs, logica duplicada critica, reglas de negocio divergentes.
- `P2`: deuda clara de mantenibilidad, helper reusable no centralizado, acoplamiento o dispersion relevante.
- `P3`: mejoras de limpieza, naming, homogeneizacion y pequenos refactors.

## Formato de salida

Usar `references/output-template.md`.

Cada hallazgo debe incluir:
- prioridad
- ubicacion
- que se repite o que es inconsistente
- por que conviene centralizar, extraer o mantener como esta
- refactor propuesto en terminos concretos

## Heuristicas de extraccion

- Extraer a funcion si el patron se repite y la firma resultante es simple.
- Extraer a clase o servicio compartido solo si hay estado, estrategia o multiples operaciones cohesionadas.
- Extraer a modulo `utils` solo si el nombre del modulo sigue siendo especifico; evitar `utils.py` genericos.
- Preferir nombres orientados al dominio o a la responsabilidad (`build_employee_payload`, `normalize_curp`) sobre nombres vagos (`process_data`, `handle_item`).
- Si la reutilizacion es de infraestructura, ubicarla cerca de repositorios, clientes o adapters.
- Si la reutilizacion es de dominio, ubicarla cerca de servicios o entidades del dominio.

## Busquedas utiles

- `rg -n "def " app`
- `rg -n "try:|except " app`
- `rg -n "model_dump|dict\\(|json\\(" app`
- `rg -n "validate|normalize|serialize|build_|to_dict|from_" app`
- `rg -n "class .*Service|class .*Repository|class .*State" app`
- `rg -n "TODO|FIXME|duplic|reutil|helper|utils" app`

## Referencias

- Leer `references/review-checklist.md` para una lista breve de revision.
- Leer `references/output-template.md` para mantener un formato uniforme de entrega.
