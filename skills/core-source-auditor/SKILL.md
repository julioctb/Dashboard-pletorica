---
name: core-source-auditor
description: Auditar proyectos Python o Reflex donde `app/core` concentra validaciones, enums, constants, utils, catálogos y helpers transversales. Usar cuando Codex deba extraer esas fuentes de verdad, detectar wrappers o facades fuera de `core`, localizar lógica repetida, proponer centralización, o revisar código muerto y redundante antes de refactors.
---

# Core Source Auditor

Tratar `app/core` como contrato canónico del sistema. Antes de proponer mover, borrar o duplicar lógica, ubicar si la regla ya vive en `core` y si fuera de `core` solo existe una capa de compatibilidad.

Leer `references/core-source-map.md` al inicio para el mapa del repo. Ejecutar `scripts/audit_core_sources.py` cuando haga falta evidencia rápida sobre consumidores, wrappers, duplicación estructural y candidatos de código muerto.

## Workflow

1. Construir el mapa de verdad.
   Revisar `app/core` por áreas: `validation/`, `catalogs/`, `calculations/`, `enums.py`, `error_messages.py`, `text_utils.py`, `ui_helpers.py`, `ui_options.py`, `ui_option_sets.py`, `constants/`, `config/`, `exceptions.py`.
2. Separar verdad vs compatibilidad.
   Marcar como adaptadores los módulos fuera de `core` que solo reexportan o renombran símbolos desde `app.core.*`.
3. Buscar duplicación real.
   Priorizar validaciones repetidas, builders de opciones, helpers de fecha/vigencia, normalizadores de texto y reglas de negocio que aparezcan en `presentation`, `services` o `entities`.
4. Verificar código muerto con cautela.
   Tomar los resultados estáticos como candidatos, no como permiso automático para borrar. Confirmar runtime, reexports y contratos públicos antes de eliminar.
5. Entregar hallazgos accionables.
   Priorizar riesgo funcional y costo de mantenimiento. Señalar dónde centralizar y cuál es la capa correcta.

## Heurísticas de decisión

- Si una regla ya existe en `app/core/validation`, no volver a implementarla en `presentation`.
- Si un módulo fuera de `core` solo renombra imports desde `core`, tratarlo como facade temporal y evitar agregar lógica nueva ahí.
- Si la misma regla aparece en UI, estado y servicio, bajar la lógica a la capa más baja que siga siendo correcta.
- Si la duplicación solo cambia en constantes o labels, parametrizar antes de copiar.
- Si un símbolo parece muerto pero está reexportado por `__init__.py`, confirmarlo antes de marcarlo para eliminación.
- Si una abstracción nueva solo envuelve un alias, probablemente conviene consolidar imports y no agregar más capas.

## Quick Start

1. Leer `references/core-source-map.md`.
2. Ejecutar:

```bash
python3 skills/core-source-auditor/scripts/audit_core_sources.py --root .
```

3. Si quieres dejar reporte en disco:

```bash
python3 skills/core-source-auditor/scripts/audit_core_sources.py --root . --write wip/CORE_SOURCE_AUDIT.md
```

4. Profundizar manualmente en los hotspots con `rg` antes de proponer cambios.

## Searches utiles

- `rg -n "from app\\.core|import app\\.core" app`
- `rg -n "Compatibilidad de validadores|wrapper sobre core\\.validation" app`
- `rg -n "_coerce_fecha|aplica_a\\(" app/core`
- `rg -n "descripcion\\(self\\) -> str" app/core/enums.py`
- `rg -n "from app\\.presentation\\.pages\\..*_validators" app`

## Recursos

- `references/core-source-map.md`: mapa del repo, áreas canónicas y hotspots ya conocidos.
- `scripts/audit_core_sources.py`: auditoría estática de imports, wrappers, duplicación estructural y símbolos candidatos a estar muertos.
