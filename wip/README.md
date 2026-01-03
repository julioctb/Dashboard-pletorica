# 🚧 Work In Progress (WIP)

Código experimental o en desarrollo que **NO debe usarse en producción**.

Este directorio contiene módulos que están siendo desarrollados o refactorizados y aún no están listos para ser integrados al código productivo.

---

## 📋 Archivos en WIP

### `payroll.py`
**Estado**: 🔴 En desarrollo
**Descripción**: Motor principal de cálculo de nómina quincenal/mensual
**Bloqueador**: Necesita integración con módulos de cálculo existentes
**Fecha inicio WIP**: 2026-01-03

**Pendientes**:
- [ ] Conectar con `app/core/calculations/calculadora_imss.py` (línea 92)
- [ ] Conectar con `app/core/calculations/calculadora_isr.py` (línea 97)
- [ ] Implementar cálculo de horas extra dobles/triples
- [ ] Implementar cálculo de prima dominical
- [ ] Agregar soporte para préstamos INFONAVIT/FONACOT
- [ ] Crear tests unitarios completos
- [ ] Validar con datos reales de nómina

**Próximos pasos**:
1. Descomentar imports de CalculadoraIMSS y CalculadoraISR (línea 9-10)
2. Reemplazar `self.calculadora_imss` y `self.calculadora_isr` con instancias reales
3. Probar con datos de prueba
4. Crear tests unitarios
5. **Cuando esté listo**: Mover a `app/core/calculations/` y actualizar imports

**Líneas de código**: 236 líneas

---

## 🔄 Proceso para Mover de WIP a Producción

Cuando un archivo esté listo para producción:

1. **Verificar que funciona**:
   ```bash
   pytest tests/test_[modulo].py
   ```

2. **Mover de vuelta**:
   ```bash
   mv wip/[archivo].py app/[destino]/[archivo].py
   ```

3. **Actualizar imports** en el código que lo use

4. **Eliminar de README.md** la sección del archivo

5. **Commit**:
   ```bash
   git add .
   git commit -m "feat: Integrar [modulo] desde WIP"
   ```

---

## 📝 Notas

- Este directorio **NO está en el árbol de módulos Python** (no tiene `__init__.py`)
- Los archivos aquí **NO pueden ser importados** desde otros módulos
- Si necesitas probar código WIP, copia temporalmente a un notebook o script de prueba
- Mantén este README actualizado cuando agregues/elimines archivos

---

**Última actualización**: 2026-01-03
