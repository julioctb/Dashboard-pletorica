# Common Failures

## Stack spacing vs CSS gap

- `rx.hstack(..., spacing=Spacing.XS)` falla porque `spacing` espera tokens `"0"`..`"9"`.
- `rx.hstack(..., gap=Spacing.XS)` suele ser valido porque `gap` es CSS.
- Si el traceback muestra `HStack.spacing`, arreglar primero ese keyword exacto.

## Var truthiness en render

- `Cannot convert Var ... to bool` significa que entro `if`, `and`, `or` o `not` de Python sobre una expresion reactiva.
- Esto aparece mucho en helpers usados por `rx.foreach`, porque el item de la fila llega como `Var`, no como `dict` normal.
- Patrones tipicos:
  - `if baja.get("estatus") == "INICIADA":`
  - `texto = "A" if item["x"] else "B"`
  - `visible = item["activo"] and state.puede_editar`
- Correcciones tipicas:
  - `rx.match(baja.get("estatus", ""), ...)`
  - `rx.cond(item["x"], "A", "B")`
  - `item["activo"] & state.puede_editar`

## Token props revisados por el script

El script de este skill revisa estas familias de props:

- `spacing`
- `p`, `px`, `py`, `pt`, `pr`, `pb`, `pl`
- `m`, `mx`, `my`, `mt`, `mr`, `mb`, `ml`

Patrones sospechosos:

- `Spacing.*`
- `Radius.*`
- `Typography.*`
- strings CSS como `"4px"`, `"1rem"`, `"50%"`
- enteros como `spacing=2`

## Control de flujo revisado por el script

El segundo script revisa patrones sospechosos en archivos de presentacion:

- `if` sobre valores que dependen de parametros reactivos
- ternarios de Python (`a if cond else b`) sobre valores reactivos
- `and`, `or`, `not` de Python sobre valores reactivos

El resultado es heuristico. Usarlo como lista de sospechosos y confirmar con el traceback.

## Busquedas utiles

```bash
rg -n "spacing=Spacing\\.|spacing=['\\\"][0-9]+px|spacing=[0-9]+" app
rg -n "\\b(p|px|py|pt|pr|pb|pl|m|mx|my|mt|mr|mb|ml)=Spacing\\." app
rg -n "\\bif\\b|\\band\\b|\\bor\\b|\\bnot\\b" app/presentation -g '*components.py' -g '*page.py'
```

## Fuente local de verdad

Cuando haya duda, inspeccionar la instalacion local de Reflex:

Leer la fuente instalada correspondiente, por ejemplo:

- `.venv/lib/python*/site-packages/reflex/components/radix/themes/layout/stack.py`
- `.venv/lib/python*/site-packages/reflex/components/radix/themes/layout/flex.py`
- Buscar `LiteralSpacing` en `.venv/lib/python*/site-packages/reflex/components/radix/themes/base.py`.
