# Migraciones de Base de Datos - Sistema Dashboard Pletórica

**Fecha**: 2026-01-31
**Base de datos**: Supabase (PostgreSQL)
**Método de ejecución**: Manual (Supabase Dashboard SQL Editor)

---

## 📋 Orden de Ejecución (CRÍTICO)

Las migraciones **DEBEN ejecutarse en este orden exacto** para respetar las dependencias entre tablas:

| # | Archivo | Descripción | Dependencias |
|---|---------|-------------|--------------|
| **000** | `000_create_empresas.sql` | ✅ **NUEVA** - Tabla base de empresas | Ninguna |
| **001** | `001_create_tipos_servicio.sql` | ✅ **NUEVA** - Catálogo de tipos de servicio | Ninguna |
| **002** | `002_create_categorias_puesto.sql` | ✅ **NUEVA** - Categorías de puesto por tipo | tipos_servicio |
| **003** | `003_create_contratos.sql` | ✅ **NUEVA** - Contratos de servicio | empresas, tipos_servicio |
| **004** | `004_create_pagos.sql` | ✅ **NUEVA** - Pagos de contratos | contratos |
| **005** | `005_create_contrato_categorias.sql` | ✅ **NUEVA** - Relación contrato-categoría | contratos, categorias_puesto |
| **006** | `006_create_plazas_table.sql` | Plazas (puestos de trabajo) | contrato_categorias |
| **007** | `007_create_empleados_table.sql` | Empleados | empresas |
| **008** | `008_create_historial_laboral_table.sql` | Historial de asignaciones | empleados, plazas |
| **009** | `009_create_requisiciones.sql` | Requisiciones + items | empresas |
| **010** | `010_create_lugares_entrega.sql` | Lugares de entrega | Ninguna |
| **011** | `011_permitir_borradores_requisicion.sql` | Permite estatus BORRADOR | requisiciones |
| **012** | `012_create_archivo_sistema.sql` | Sistema de archivos genérico | Ninguna |
| **013** | `013_add_search_indices.sql` | Índices de búsqueda (empresas) | empresas |

---

## 🚀 Cómo Ejecutar las Migraciones

### Método 1: Ejecución Individual (Recomendado)

1. **Abre Supabase Dashboard**
   - URL: https://app.supabase.com/
   - Selecciona tu proyecto

2. **Ve a SQL Editor**
   - Menú lateral → **SQL Editor**

3. **Ejecuta una por una en orden**
   ```sql
   -- Copia y pega el contenido completo de cada archivo
   -- Empezando por 000_create_empresas.sql
   ```

4. **Verifica éxito**
   - Mensaje: "Success. No rows returned"
   - O: "Rows affected: X"

5. **Repite para cada migración** (000 → 013)

### Método 2: Verificación de Tablas Existentes

**IMPORTANTE**: Algunas tablas pueden ya existir en tu BD. Antes de ejecutar, verifica:

```sql
-- Ver todas las tablas existentes
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Si una tabla ya existe**:
- ✅ **Salta esa migración** (las migraciones usan `IF NOT EXISTS`)
- ⚠️ **Revisa la estructura** (puede estar desactualizada)
- 🔧 **Opción**: Elimina y recrea (solo en desarrollo)

---

## 📊 Resumen de Cambios

### Tablas Creadas (6 nuevas)

| Tabla | Propósito | ENUMs Creados |
|-------|-----------|---------------|
| **empresas** | Proveedores de servicios | tipo_empresa_enum, estatus_empresa_enum |
| **tipos_servicio** | Catálogo de servicios | estatus_enum |
| **categorias_puesto** | Categorías por tipo | - (reutiliza estatus_enum) |
| **contratos** | Contratos de servicio | tipo_contrato_enum, modalidad_adjudicacion_enum, tipo_duracion_enum, estatus_contrato_enum |
| **pagos** | Pagos a proveedores | - |
| **contrato_categorias** | Relación contrato-categoría | - |

### Índices Creados

- **Total**: 31 índices nuevos
- **Búsqueda**: LOWER() indices para case-insensitive search
- **Rendimiento**: Composite indices para filtros frecuentes
- **Integridad**: Unique indices para claves de negocio (RFC, código)

### Triggers Creados

- 6 triggers `update_*_fecha_actualizacion()` para auditoría automática

---

## 🔧 Verificación Post-Migración

### 1. Verificar Tablas Creadas

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

**Esperado** (14 tablas):
- empresas
- tipos_servicio
- categorias_puesto
- contratos
- pagos
- contrato_categorias
- plazas
- empleados
- historial_laboral
- requisicion
- requisicion_item
- requisicion_partida
- lugar_entrega
- archivo_sistema

### 2. Verificar Foreign Keys

```sql
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;
```

### 3. Verificar ENUMs Creados

```sql
SELECT
    t.typname AS enum_name,
    string_agg(e.enumlabel, ', ' ORDER BY e.enumsortorder) AS enum_values
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
WHERE n.nspname = 'public'
GROUP BY t.typname
ORDER BY t.typname;
```

### 4. Insertar Datos de Prueba (Opcional)

```sql
-- Ver comentarios al final de cada migración
-- Ejemplo: 000_create_empresas.sql tiene INSERT de prueba comentado
```

---

## 🔄 Dependencias entre Tablas (Diagrama)

```
┌──────────────┐
│  empresas    │◄──────────┐
└──────┬───────┘           │
       │                   │
       │ FK                │ FK
       ▼                   │
┌──────────────┐    ┌──────┴───────┐
│  contratos   │◄───│  empleados   │
│              │    └──────────────┘
│- empresa_id  │
│- tipo_servicio_id
└──┬───┬───────┘
   │   │
   │   └─────────────┐
   │                 │
   │ FK              │ FK
   ▼                 ▼
┌─────────────────┐  ┌──────────────────────┐
│     pagos       │  │ contrato_categorias  │
│                 │  │                      │
│- contrato_id    │  │- contrato_id         │
└─────────────────┘  │- categoria_puesto_id │
                     └───────┬──────────────┘
                             │
                             │ FK
                             ▼
┌──────────────┐      ┌──────────────────┐
│tipos_servicio│◄─────│categorias_puesto │
└──────────────┘      └──────────────────┘
       ▲                      │
       │                      │
       │ FK                   │ FK
       │                      │
       └──────────┐           │
                  │           │
           ┌──────┴───────────▼──┐
           │  plazas              │
           │                      │
           │- contrato_categoria_id
           └──────────────────────┘
```

---

## ⚠️ Notas Importantes

### Antes de Ejecutar

1. **Backup**: Haz backup de tu BD (Supabase Dashboard → Database → Backups)
2. **Ambiente**: Ejecuta primero en **desarrollo**, luego en producción
3. **Tiempo**: Las migraciones son rápidas (<30 segundos total)

### Durante la Ejecución

1. **Orden estricto**: SIEMPRE ejecuta en orden 000 → 013
2. **Errores comunes**:
   - "relation already exists" → Tabla ya existe, salta la migración
   - "type already exists" → ENUM ya existe, salta CREATE TYPE
   - "violates foreign key" → Ejecutaste fuera de orden, reinicia

### Después de Ejecutar

1. **Verifica estructura**: Ejecuta queries de verificación (arriba)
2. **Prueba conexión**: `poetry run reflex run` debe iniciar sin errores
3. **Inserta datos**: Usa los INSERT de ejemplo para probar

---

## 🐛 Rollback (Revertir Migraciones)

⚠️ **SOLO EN DESARROLLO** - Esto eliminará TODOS los datos

```sql
-- Ejecutar en orden INVERSO (013 → 000)
-- Al final de cada migración hay instrucciones de rollback comentadas

-- Ejemplo (013 → empresas):
DROP TABLE IF EXISTS public.empresas CASCADE;
DROP TYPE IF EXISTS estatus_empresa_enum;
DROP TYPE IF EXISTS tipo_empresa_enum;
```

---

## 📞 Soporte

Si encuentras errores:

1. Lee el mensaje de error completo
2. Verifica que ejecutaste en orden correcto
3. Revisa la sección "Verificación" de la migración
4. Contacta: julioc.tello@me.com

---

## ✅ Checklist de Ejecución

Marca conforme ejecutas:

- [ ] 000_create_empresas.sql
- [ ] 001_create_tipos_servicio.sql
- [ ] 002_create_categorias_puesto.sql
- [ ] 003_create_contratos.sql
- [ ] 004_create_pagos.sql
- [ ] 005_create_contrato_categorias.sql
- [ ] 006_create_plazas_table.sql
- [ ] 007_create_empleados_table.sql
- [ ] 008_create_historial_laboral_table.sql
- [ ] 009_create_requisiciones.sql
- [ ] 010_create_lugares_entrega.sql
- [ ] 011_permitir_borradores_requisicion.sql
- [ ] 012_create_archivo_sistema.sql
- [ ] 013_add_search_indices.sql
- [ ] Verificar tablas creadas (SELECT from information_schema)
- [ ] Verificar foreign keys
- [ ] Probar aplicación: `poetry run reflex run`

---

**FIN - Migraciones Completadas** 🎉
