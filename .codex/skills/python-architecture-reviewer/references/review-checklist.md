# Review Checklist

## Antes de reportar

- Entender la responsabilidad principal del modulo.
- Identificar la capa: entidad, servicio, repositorio, presentacion, estado o infraestructura.
- Verificar si el patron cuestionado ya existe en otros archivos del proyecto.

## Duplicacion

- Buscar funciones hermanas con mas de un bloque comun.
- Comparar validaciones repetidas entre handlers, services y repositories.
- Revisar builders de payload, serializers y adapters repetidos.
- Revisar `try/except`, logging y mensajes repetidos.

## Centralizacion

- Preguntar si existe una fuente unica de verdad posible.
- Confirmar si la extraccion simplifica la API o la complica.
- Decidir la ubicacion correcta del reusable segun dominio o infraestructura.
- Evitar helpers globales si el reusable sigue siendo local a una feature.

## Consistencia

- Naming homogeneo entre funciones equivalentes.
- Tipos de retorno compatibles.
- Manejo uniforme de `None`, errores y excepciones.
- Firmas y orden de parametros consistentes.
- Misma capa para responsabilidades equivalentes.

## Filtro de calidad

- No proponer una abstraccion si solo elimina tres lineas triviales.
- No mover logica a una capa superior si puede vivir mas abajo.
- No recomendar `utils.py` generico sin nombre y objetivo claros.
- No confundir similitud superficial con duplicacion real.
