# Reflex Guidelines

## Scope

Usar esta referencia cuando el trabajo toque componentes Reflex, `rx.State`, event handlers, computed vars, routing o decisiones de performance.

Base usada:
- UI Overview: <https://reflex.dev/docs/ui/overview>
- State Overview: <https://reflex.dev/docs/state/overview/>
- Events Overview: <https://reflex.dev/docs/events/events-overview>
- State Structure Overview: <https://reflex.dev/docs/state-structure/overview>
- Component State: <https://reflex.dev/docs/state-structure/component-state/>

## Core Model

- Construir UI con funciones Python que retornan componentes.
- Pasar children como argumentos posicionales y props como keyword args.
- Modelar interactividad con clases que heredan de `rx.State`.
- Recordar que cada usuario y cada pestaña tienen su propia copia de estado en el servidor.
- Recordar que los eventos se ejecutan en el servidor y Reflex sincroniza cambios al cliente.

## State Discipline

- Declarar vars mutables como atributos del `State`.
- Modificar vars solo desde event handlers.
- Usar `@rx.var` para valores derivados; no intentar asignarlos manualmente.
- Mantener helpers internos con prefijo `_` cuando no deban ser disparados desde el cliente.
- Mantener el estado serializable. Evitar clientes HTTP, conexiones, servicios, cursores o componentes dentro del state.

## Event Discipline

- Conectar handlers mediante props como `on_click`, `on_change`, `on_mount` y equivalentes.
- Preferir `@rx.event` para handlers públicos o parametrizados porque mejora tipado y legibilidad.
- Hacer handlers pequeños: actualizar estado, llamar servicios, devolver toasts o navegación cuando aplique.
- Mover trabajo de apoyo a helpers privados o servicios para que el handler no se convierta en una fachada gigante.

## State Structure

- Empezar con estados separados por página o feature.
- Mantener substates planos. Reflex carga el substate del evento, sus padres y sus hijos; una jerarquía profunda encarece eventos.
- Evitar computed vars en estados enormes o padres de muchos substates, porque fuerzan carga y recálculo.
- Usar acceso entre estados solo cuando el flujo realmente lo pida; no convertirlo en acoplamiento transversal por defecto.

## ComponentState

- Usar `rx.ComponentState` solo para componentes reutilizables y autocontenidos.
- Elegirlo cuando cada instancia del componente deba mantener su propio estado.
- Evitarlo para páginas enteras o listas generadas con `rx.foreach()`, porque compartirían el mismo estado por iteración.
- Si la lógica es de toda la página o del flujo de negocio, volver a `rx.State`.

## Python and System Design Heuristics

- Dejar el render declarativo y delgado.
- Dejar reglas de negocio, agregaciones, acceso a base de datos y servicios externos fuera del componente.
- Diseñar handlers como fronteras de aplicación, no como lugares para mezclar consultas, validación, serialización y presentación al mismo tiempo.
- Mantener modelos y contratos cerca del dominio y la API, no dentro de la UI.

## Anti-Patterns

- Meter consultas o lógica fiscal compleja dentro de una función que devuelve UI.
- Guardar objetos no serializables en vars del state.
- Crear un único `State` monstruoso para toda la app.
- Encadenar muchos substates con herencia solo para compartir utilidades.
- Usar `ComponentState` para resolver acoplamiento de página.
- Meter efectos secundarios dentro de `@rx.var`.

## Practical Checklist

Antes de cerrar un cambio en Reflex, confirmar:

1. La UI solo compone componentes y props.
2. Las mutaciones pasan por handlers.
3. Los helpers privados no exponen acciones sensibles al cliente.
4. El state contiene datos serializables.
5. Los valores derivados viven en `@rx.var` o en servicios, según costo y alcance.
6. La estructura de state sigue siendo plana y entendible.
