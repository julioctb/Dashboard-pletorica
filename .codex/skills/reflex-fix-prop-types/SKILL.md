---
name: reflex-fix-prop-types
description: Diagnosticar y corregir errores de compilacion de Reflex causados por props con tipos o tokens invalidos y por uso incorrecto de `Var` en control de flujo de Python. Usar cuando el log muestre `Invalid var passed for prop`, `expected type Literal[...]`, `Cannot convert Var ... to bool`, workers que salen durante compile, o cuando un componente Reflex recibe valores CSS como `4px`, `Spacing.XS` o `Radius.MD` en props que esperan tokens, o usa `if`, `and`, `or` o `not` sobre valores reactivos.
---

# Reflex Fix Prop Types

Resolver primero la familia del error: token/enumeracion de Radix o control de flujo invalido sobre `Var`.

Corregir solo el punto roto y evitar limpiezas masivas. Este skill esta optimizado para dos patrones muy comunes en Reflex: props Radix que parecen CSS y ramas de Python (`if`, `and`, `or`, `not`) ejecutadas sobre valores reactivos.

## Workflow

1. Leer el traceback completo.
   Extraer componente, prop, tipo esperado, valor recibido y archivo.
   Si el error menciona `Literal[...]`, tratarlo como token o enum hasta demostrar lo contrario.
   Si el error menciona `Cannot convert Var ... to bool`, asumir que hay `if`, `and`, `or` o `not` de Python en una ruta de render.
2. Ejecutar el verificador correcto del skill.
   Usar `python3 .codex/skills/reflex-fix-prop-types/scripts/check_reflex_token_props.py app`
   El script revisa `spacing`, `p`, `px`, `py`, `m`, `mx` y props similares que solo aceptan tokens `"0"`..`"9"`.
   Usar `python3 .codex/skills/reflex-fix-prop-types/scripts/check_reflex_var_bool.py app/presentation`
   El script revisa `if`, `and`, `or`, `not` y ternarios de Python en helpers/componentes que operan sobre valores reactivos.
3. Separar props Radix de props CSS o ramas Python de ramas reactivas.
   Usar tokens/enums para props como `spacing`, `size`, `variant`, `radius`, `color_scheme`, `align`, `justify`.
   Usar constantes de tema o longitudes CSS para props como `gap`, `column_gap`, `row_gap`, `padding`, `margin`, `width`, `height`, `border_radius`.
   Usar `rx.cond`, `rx.match`, `&`, `|` y `~` cuando el valor venga de `State`, `rx.foreach`, `dict.get(...)` reactivo o expresiones derivadas.
4. Reemplazar el valor minimo necesario.
   Ejemplo: `spacing=Spacing.XS` no es valido en `rx.hstack`.
   Corregir a `spacing="1"` si quieres el token de stack.
   O mover la intencion a `gap=Spacing.XS` si de verdad necesitas longitud CSS.
   Ejemplo: `if estatus == "INICIADA":` no es valido si `estatus` sale de `baja.get("estatus")` dentro de un renderer.
   Corregir usando `rx.match` o `rx.cond` en el punto donde se construye el valor o el componente.
5. Verificar.
   Reejecutar el script correspondiente.
   Hacer al menos una validacion barata del archivo tocado, por ejemplo `python3 -m py_compile <archivo>`.
   Ejecutar compilacion de Reflex solo si sigue habiendo duda.

## Quick Rules

- Tratar `spacing` como token de Radix, no como CSS.
- No pasar `Spacing.*`, `Radius.*` ni strings tipo `"4px"` a props que esperan `Literal[...]`.
- Preferir tokens string explicitos (`"1"`, `"2"`, `"3"`) sobre numeros enteros.
- No usar `if`, `and`, `or` ni `not` de Python sobre `Var`.
- Si un valor viene de `State`, de `rx.foreach`, de `item["campo"]` o de `item.get("campo")` dentro del render, tratarlo como reactivo hasta demostrar lo contrario.
- Usar el nombre completo del prop CSS si quieres longitudes del theme.
  `gap=Spacing.SM` es razonable.
  `spacing=Spacing.SM` rompe.
- Usar `rx.cond` o `rx.match` para elegir componentes, textos, handlers o colores cuando la condicion sea reactiva.
- Usar `&`, `|`, `~` en lugar de `and`, `or`, `not` cuando combines expresiones reactivas.
- Si el error no es obvio, inspeccionar la fuente instalada de Reflex antes de improvisar.
  Leer `.venv/lib/python*/site-packages/reflex/components/radix/themes/layout/stack.py` o el archivo del componente indicado en el traceback.
  Buscar `LiteralSpacing` en `.venv/lib/python*/site-packages/reflex/components/radix/themes/base.py`.

## Fast Fixes

- `rx.hstack(..., spacing="4px")`
  Cambiar a `spacing="1"` o usar `gap="4px"` si la API del componente permite CSS gap.
- `rx.hstack(..., spacing=Spacing.XS)`
  Cambiar a `spacing="1"`.
- `rx.flex(..., p=Spacing.BASE)`
  Cambiar a `p="4"` si quieres token Radix equivalente, o usar `padding=Spacing.BASE` si quieres CSS.
- `Invalid var passed for prop ... expected type typing.Literal[...]`
  Buscar el keyword exacto en la llamada del componente y corregir ese valor antes de tocar el resto del layout.
- `if baja.get("estatus", "") == "INICIADA":`
  Cambiar a `rx.match(baja.get("estatus", ""), ...)` o a `rx.cond(...)` alrededor del valor/componente final.
- `visible = item["activo"] and state.puede_editar`
  Cambiar a `visible = item["activo"] & state.puede_editar`.
- `texto = "A" if item["estatus"] == "X" else "B"`
  Cambiar a `texto = rx.cond(item["estatus"] == "X", "A", "B")`.

## Local Mapping

Usar este mapeo rapido cuando el repo ya define `Spacing` en pixeles pero el componente pide tokens de Radix:

- `Spacing.XS` (`4px`) -> `"1"`
- `Spacing.SM` (`8px`) -> `"2"`
- `Spacing.MD` (`12px`) -> `"3"`
- `Spacing.BASE` (`16px`) -> `"4"`

Si la equivalencia visual importa mucho, confirmar con el diseno real. El objetivo principal del fix es restaurar compilacion valida de Reflex.

## Resources

- Leer `references/common-failures.md` para un resumen corto de patrones y busquedas utiles.
- Ejecutar `scripts/check_reflex_token_props.py` para detectar usos sospechosos de token props con valores CSS.
- Ejecutar `scripts/check_reflex_var_bool.py` para detectar control de flujo de Python sobre valores reactivos.

No crear una abstraccion nueva en la app para esconder el problema. Corregir el prop, validar y seguir.
