# Proyecto BUAP - Estructura Modular

## 📁 Nueva Estructura

```
app/
├── modules/           # Módulos de negocio
│   ├── shared/       # Código compartido
│   ├── empresas/     # Módulo de empresas
│   ├── empleados/    # Módulo de empleados
│   ├── sedes/        # Módulo de sedes
│   └── nominas/      # Módulo de nóminas
└── tests/            # Tests unitarios
```

## 🚀 Migración Completada

- Fecha: 2025-10-06 16:48
- Backup en: `backup_migration/20251006_164845`

## 📝 Cambios Principales

1. **Arquitectura Modular**: Cada módulo es independiente
2. **Repository Pattern**: Abstracción de base de datos
3. **Domain Driven Design**: Lógica de negocio en entidades
4. **Inyección de Dependencias**: Services desacoplados

## 🧪 Testing

```bash
pytest tests/empresas
```

## 📚 Estructura de un Módulo

```
modules/empresas/
├── domain/           # Lógica de negocio
├── infrastructure/   # Implementaciones técnicas
├── application/      # Servicios
└── presentation/     # UI (pages, states)
```

## ⚠️ Notas Importantes

- El código original está respaldado en `backup_migration/20251006_164845`
- Para restaurar: `python migrate_to_modular.py --restore`
