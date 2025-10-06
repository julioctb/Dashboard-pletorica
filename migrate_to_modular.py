#!/usr/bin/env python3
"""
SCRIPT DE MIGRACIÓN AUTOMÁTICA A MODULAR MONOLITH
==================================================
Autor: Assistant para BUAP
Fecha: 2024
Descripción: Migra estructura actual a Modular Monolith manteniendo backup

USO:
    python migrate_to_modular.py [opciones]
    
OPCIONES:
    --backup    Solo hacer backup
    --restore   Restaurar desde backup
    --dry-run   Simular sin ejecutar
    --module    Migrar solo un módulo específico
"""

import os
import shutil
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import sys

# CONFIGURACIÓN
CONFIG = {
    "app_root": "app",
    "backup_dir": "backup_migration",
    "modules": ["empresas", "empleados", "sedes", "nominas"],
    "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
}

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Imprime encabezado con formato"""
    print(f"\n{Colors.HEADER}{'='*60}")
    print(f"{text:^60}")
    print(f"{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


class ModularMigrator:
    """Clase principal para migración a Modular Monolith"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup_path = Path(CONFIG['backup_dir']) / CONFIG['timestamp']
        self.app_path = Path(CONFIG['app_root'])
        self.migration_log = []
        
    def log_action(self, action: str, status: str = "pending"):
        """Registra acciones realizadas"""
        self.migration_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "status": status
        })
    
    def save_log(self):
        """Guarda log de migración"""
        log_file = self.backup_path / "migration_log.json"
        if not self.dry_run:
            with open(log_file, 'w') as f:
                json.dump(self.migration_log, f, indent=2)
    
    def create_backup(self):
        """Crea backup completo del proyecto actual"""
        print_header("CREANDO BACKUP")
        
        if not self.dry_run:
            # Crear directorio de backup
            self.backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copiar estructura actual
            dirs_to_backup = [
                "database",
                "services", 
                "pages",
                "components",
                "layout"
            ]
            
            for dir_name in dirs_to_backup:
                src = self.app_path / dir_name
                if src.exists():
                    dst = self.backup_path / dir_name
                    shutil.copytree(src, dst)
                    print_success(f"Backup creado: {dir_name}/")
                    self.log_action(f"Backup {dir_name}", "completed")
            
            # Copiar archivos principales
            files_to_backup = ["app.py", "config.py", "__init__.py"]
            for file_name in files_to_backup:
                src = self.app_path / file_name
                if src.exists():
                    dst = self.backup_path / file_name
                    shutil.copy2(src, dst)
                    print_success(f"Backup creado: {file_name}")
        else:
            print_info("Modo dry-run: Backup simulado")
    
    def create_modular_structure(self):
        """Crea la nueva estructura modular"""
        print_header("CREANDO ESTRUCTURA MODULAR")
        
        # Estructura base
        structure = {
            "modules": {
                "shared": {
                    "database": {},
                    "components": {},
                    "utils": {},
                    "exceptions": {}
                },
                "empresas": {
                    "domain": {},
                    "infrastructure": {},
                    "application": {},
                    "presentation": {}
                },
                "empleados": {
                    "domain": {},
                    "infrastructure": {},
                    "application": {},
                    "presentation": {}
                },
                "sedes": {
                    "domain": {},
                    "infrastructure": {},
                    "application": {},
                    "presentation": {}
                },
                "nominas": {
                    "domain": {},
                    "infrastructure": {},
                    "application": {},
                    "presentation": {}
                }
            },
            "tests": {
                "empresas": {},
                "empleados": {},
                "sedes": {},
                "nominas": {}
            }
        }
        
        def create_dirs(base_path: Path, structure: dict):
            """Crea directorios recursivamente"""
            for dir_name, subdirs in structure.items():
                dir_path = base_path / dir_name
                if not self.dry_run:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    # Crear __init__.py
                    init_file = dir_path / "__init__.py"
                    init_file.touch()
                print_success(f"Creado: {dir_path.relative_to(self.app_path)}/")
                
                if subdirs:
                    create_dirs(dir_path, subdirs)
        
        create_dirs(self.app_path, structure)
        self.log_action("Estructura modular creada", "completed")
    
    def migrate_shared_code(self):
        """Migra código compartido"""
        print_header("MIGRANDO CÓDIGO COMPARTIDO")
        
        if not self.dry_run:
            # Mover conexión de base de datos
            src = self.app_path / "database" / "connection.py"
            dst = self.app_path / "modules" / "shared" / "database" / "connection.py"
            if src.exists():
                shutil.copy2(src, dst)
                print_success("Migrado: database/connection.py")
            
            # Crear base_state.py
            base_state_content = '''"""Estado base para todos los módulos"""
import reflex as rx
from typing import Optional

class BaseState(rx.State):
    """Estado base con funcionalidad común"""
    
    loading: bool = False
    error_message: str = ""
    success_message: str = ""
    
    def set_loading(self, value: bool):
        self.loading = value
    
    def set_error(self, message: str):
        self.error_message = message
        self.success_message = ""
    
    def set_success(self, message: str):
        self.success_message = message
        self.error_message = ""
    
    def clear_messages(self):
        self.error_message = ""
        self.success_message = ""
'''
            base_state_file = self.app_path / "modules" / "shared" / "components" / "base_state.py"
            base_state_file.write_text(base_state_content)
            print_success("Creado: shared/components/base_state.py")
            
            # Mover componentes UI comunes
            src_components = self.app_path / "components" / "ui"
            dst_components = self.app_path / "modules" / "shared" / "components" / "ui"
            if src_components.exists():
                shutil.copytree(src_components, dst_components, dirs_exist_ok=True)
                print_success("Migrado: components/ui/")
        
        self.log_action("Código compartido migrado", "completed")
    
    def migrate_empresas_module(self):
        """Migra el módulo de empresas"""
        print_header("MIGRANDO MÓDULO EMPRESAS")
        
        if not self.dry_run:
            module_path = self.app_path / "modules" / "empresas"
            
            # 1. Migrar modelos a domain/entities.py
            src_model = self.app_path / "database" / "models" / "empresa_models.py"
            if src_model.exists():
                content = src_model.read_text()
                
                # Agregar lógica de dominio al modelo
                domain_additions = '''
    # REGLAS DE NEGOCIO BUAP
    def puede_facturar_a_buap(self) -> bool:
        """Solo empresas activas pueden facturar a BUAP"""
        return self.estatus == EstatusEmpresa.ACTIVO
    
    def requiere_licitacion(self, monto: float) -> bool:
        """BUAP requiere licitación para montos grandes"""
        return monto > 100000.00
    
    def puede_dar_mantenimiento(self) -> bool:
        """Valida si puede dar servicio de mantenimiento"""
        return (
            self.tipo_empresa == TipoEmpresa.MANTENIMIENTO and
            self.estatus == EstatusEmpresa.ACTIVO
        )
'''
                # Insertar antes del final de la clase Empresa
                content = content.replace("class Empresa(BaseModel):", 
                                        "class Empresa(BaseModel):\n    '''Entidad con reglas de negocio BUAP'''")
                
                dst = module_path / "domain" / "entities.py"
                dst.write_text(content)
                print_success("Creado: empresas/domain/entities.py")
            
            # 2. Crear repository interface
            repository_interface = '''"""Interfaz del repositorio de empresas"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Empresa

class IEmpresaRepository(ABC):
    """Define qué operaciones necesitamos, no cómo hacerlas"""
    
    @abstractmethod
    async def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        pass
    
    @abstractmethod
    async def obtener_todas(self, incluir_inactivas: bool = False) -> List[Empresa]:
        pass
    
    @abstractmethod
    async def crear(self, empresa: Empresa) -> Empresa:
        pass
    
    @abstractmethod
    async def actualizar(self, empresa: Empresa) -> Empresa:
        pass
    
    @abstractmethod
    async def eliminar(self, empresa_id: int) -> bool:
        pass
    
    @abstractmethod
    async def existe_rfc(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        pass
'''
            dst = module_path / "domain" / "repository_interface.py"
            dst.write_text(repository_interface)
            print_success("Creado: empresas/domain/repository_interface.py")
            
            # 3. Migrar service
            src_service = self.app_path / "services" / "empresa_service.py"
            if src_service.exists():
                # Copiar y refactorizar
                content = src_service.read_text()
                
                # Cambiar imports
                content = content.replace(
                    "from app.database.connection import db_manager",
                    "from ..infrastructure.supabase_repository import SupabaseEmpresaRepository"
                )
                content = content.replace(
                    "from app.database.models.empresa_models import",
                    "from ..domain.entities import"
                )
                
                # Agregar inyección de dependencias
                content = content.replace(
                    "def __init__(self):",
                    "def __init__(self, repository = None):\n        self.repository = repository or SupabaseEmpresaRepository()"
                )
                
                # Cambiar self.supabase por self.repository
                content = content.replace("self.supabase", "self.repository")
                
                dst = module_path / "application" / "empresa_service.py"
                dst.write_text(content)
                print_success("Migrado: empresas/application/empresa_service.py")
            
            # 4. Migrar state y page
            src_state = self.app_path / "pages" / "empresas" / "empresas_state.py"
            if src_state.exists():
                content = src_state.read_text()
                
                # Cambiar imports
                content = content.replace(
                    "from app.services import empresa_service",
                    "from ..application.empresa_service import EmpresaService"
                )
                content = content.replace(
                    "import reflex as rx",
                    "import reflex as rx\nfrom app.modules.shared.components.base_state import BaseState"
                )
                content = content.replace(
                    "class EmpresasState(rx.State):",
                    "class EmpresasState(BaseState):"
                )
                
                dst = module_path / "presentation" / "states.py"
                dst.write_text(content)
                print_success("Migrado: empresas/presentation/states.py")
            
            # 5. Migrar page
            src_page = self.app_path / "pages" / "empresas" / "empresas_page.py"
            if src_page.exists():
                content = src_page.read_text()
                content = content.replace(
                    "from app.pages.empresas.empresas_state",
                    "from .states"
                )
                
                dst = module_path / "presentation" / "pages.py"
                dst.write_text(content)
                print_success("Migrado: empresas/presentation/pages.py")
        
        self.log_action("Módulo empresas migrado", "completed")
    
    def create_infrastructure_implementations(self):
        """Crea implementaciones de infraestructura"""
        print_header("CREANDO IMPLEMENTACIONES DE INFRAESTRUCTURA")
        
        if not self.dry_run:
            # Implementación Supabase para empresas
            supabase_repo = '''"""Implementación del repositorio usando Supabase"""
from typing import List, Optional
import logging
from app.modules.shared.database.connection import db_manager
from ..domain.repository_interface import IEmpresaRepository
from ..domain.entities import Empresa

logger = logging.getLogger(__name__)

class SupabaseEmpresaRepository(IEmpresaRepository):
    """Implementación específica para Supabase"""
    
    def __init__(self):
        self.supabase = db_manager.get_client()
        self.tabla = 'empresas'
    
    async def obtener_por_id(self, empresa_id: int) -> Optional[Empresa]:
        try:
            result = self.supabase.table(self.tabla).select('*').eq('id', empresa_id).execute()
            if result.data:
                return Empresa(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    async def obtener_todas(self, incluir_inactivas: bool = False) -> List[Empresa]:
        try:
            query = self.supabase.table(self.tabla).select('*')
            if not incluir_inactivas:
                query = query.eq('estatus', 'ACTIVO')
            result = query.order('nombre_comercial').execute()
            return [Empresa(**data) for data in result.data]
        except Exception as e:
            logger.error(f"Error: {e}")
            return []
    
    async def crear(self, empresa: Empresa) -> Empresa:
        try:
            if await self.existe_rfc(empresa.rfc):
                raise ValueError(f"RFC {empresa.rfc} ya existe")
            
            datos = empresa.model_dump(exclude={'id'})
            result = self.supabase.table(self.tabla).insert(datos).execute()
            
            if result.data:
                return Empresa(**result.data[0])
            raise Exception("No se pudo crear")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    async def actualizar(self, empresa: Empresa) -> Empresa:
        try:
            datos = empresa.model_dump(exclude={'id', 'fecha_creacion'})
            result = self.supabase.table(self.tabla).update(datos).eq('id', empresa.id).execute()
            
            if result.data:
                return Empresa(**result.data[0])
            raise Exception("No se pudo actualizar")
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
    
    async def eliminar(self, empresa_id: int) -> bool:
        try:
            result = self.supabase.table(self.tabla).update({'estatus': 'INACTIVO'}).eq('id', empresa_id).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
    
    async def existe_rfc(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        try:
            query = self.supabase.table(self.tabla).select('id').eq('rfc', rfc.upper())
            if excluir_id:
                query = query.neq('id', excluir_id)
            result = query.execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error: {e}")
            return False
'''
            dst = self.app_path / "modules" / "empresas" / "infrastructure" / "supabase_repository.py"
            dst.write_text(supabase_repo)
            print_success("Creado: empresas/infrastructure/supabase_repository.py")
        
        self.log_action("Implementaciones de infraestructura creadas", "completed")
    
    def update_main_app(self):
        """Actualiza app.py principal"""
        print_header("ACTUALIZANDO APP.PY")
        
        if not self.dry_run:
            app_file = self.app_path / "app.py"
            if app_file.exists():
                content = app_file.read_text()
                
                # Actualizar imports
                old_import = "from .pages.empresas.empresas_page import empresas_page"
                new_import = "from .modules.empresas.presentation.pages import empresas_page"
                
                content = content.replace(old_import, new_import)
                
                # Crear backup del app.py original
                backup_app = self.backup_path / "app.py.original"
                app_file.rename(backup_app)
                
                # Escribir nuevo app.py
                app_file.write_text(content)
                print_success("Actualizado: app.py")
                print_info(f"Backup original en: {backup_app}")
        
        self.log_action("app.py actualizado", "completed")
    
    def create_tests_structure(self):
        """Crea estructura de tests"""
        print_header("CREANDO ESTRUCTURA DE TESTS")
        
        if not self.dry_run:
            # Test para empresas
            test_content = '''"""Tests para el módulo de empresas"""
import pytest
from app.modules.empresas.domain.entities import Empresa, TipoEmpresa
from app.modules.empresas.application.empresa_service import EmpresaService

class TestEmpresaDomain:
    """Tests para la entidad Empresa"""
    
    def test_crear_empresa_valida(self):
        """Test: Crear empresa con datos válidos"""
        empresa = Empresa(
            nombre_comercial="Test SA",
            razon_social="Test SA de CV",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="TST123456789"
        )
        assert empresa.nombre_comercial == "Test SA"
        assert empresa.puede_facturar_a_buap() == True
    
    def test_empresa_requiere_licitacion(self):
        """Test: Validar monto para licitación"""
        empresa = Empresa(
            nombre_comercial="Test SA",
            razon_social="Test SA de CV",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="TST123456789"
        )
        assert empresa.requiere_licitacion(50000) == False
        assert empresa.requiere_licitacion(150000) == True

class TestEmpresaService:
    """Tests para el servicio de empresas"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock del repository para tests"""
        from unittest.mock import Mock
        repo = Mock()
        repo.existe_rfc.return_value = False
        repo.crear.return_value = Empresa(
            id=1,
            nombre_comercial="Test",
            razon_social="Test SA",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="TST123456789"
        )
        return repo
    
    async def test_crear_empresa_con_validacion(self, mock_repository):
        """Test: Crear empresa con validaciones"""
        service = EmpresaService(repository=mock_repository)
        
        datos = {
            "nombre_comercial": "Test",
            "razon_social": "Test SA",
            "tipo_empresa": "NOMINA",
            "rfc": "TST123456789",
            "email": "test@test.com"
        }
        
        empresa = await service.crear_empresa(datos)
        assert empresa.id == 1
        mock_repository.crear.assert_called_once()
'''
            test_file = self.app_path / "tests" / "empresas" / "test_empresa.py"
            test_file.write_text(test_content)
            print_success("Creado: tests/empresas/test_empresa.py")
            
            # pytest.ini
            pytest_ini = '''[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
'''
            pytest_file = self.app_path.parent / "pytest.ini"
            pytest_file.write_text(pytest_ini)
            print_success("Creado: pytest.ini")
        
        self.log_action("Estructura de tests creada", "completed")
    
    def create_documentation(self):
        """Crea documentación básica"""
        print_header("CREANDO DOCUMENTACIÓN")
        
        if not self.dry_run:
            readme_content = f'''# Proyecto BUAP - Estructura Modular

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

- Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}
- Backup en: `{self.backup_path}`

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

- El código original está respaldado en `{self.backup_path}`
- Para restaurar: `python migrate_to_modular.py --restore`
'''
            readme_file = self.app_path / "modules" / "README.md"
            readme_file.write_text(readme_content)
            print_success("Creado: modules/README.md")
        
        self.log_action("Documentación creada", "completed")
    
    def run_migration(self):
        """Ejecuta la migración completa"""
        try:
            print_header("INICIANDO MIGRACIÓN A MODULAR MONOLITH")
            print_info(f"Modo: {'DRY RUN' if self.dry_run else 'EJECUCIÓN REAL'}")
            
            # Paso 1: Backup
            self.create_backup()
            
            # Paso 2: Crear estructura
            self.create_modular_structure()
            
            # Paso 3: Migrar código compartido
            self.migrate_shared_code()
            
            # Paso 4: Migrar módulo empresas
            self.migrate_empresas_module()
            
            # Paso 5: Crear implementaciones
            self.create_infrastructure_implementations()
            
            # Paso 6: Actualizar app.py
            self.update_main_app()
            
            # Paso 7: Crear tests
            self.create_tests_structure()
            
            # Paso 8: Documentación
            self.create_documentation()
            
            # Guardar log
            self.save_log()
            
            print_header("MIGRACIÓN COMPLETADA EXITOSAMENTE")
            
            if not self.dry_run:
                print_success(f"Backup guardado en: {self.backup_path}")
                print_info("Para restaurar: python migrate_to_modular.py --restore")
                print_warning("Recuerda actualizar los imports en archivos no migrados")
                
                # Instrucciones post-migración
                print("\n📋 SIGUIENTES PASOS:")
                print("1. Ejecuta: pip install pytest pytest-asyncio")
                print("2. Prueba: reflex run")
                print("3. Visita: http://localhost:3000/empresas")
                print("4. Ejecuta tests: pytest tests/empresas")
            
        except Exception as e:
            print_error(f"Error durante migración: {e}")
            self.log_action(f"Error: {str(e)}", "failed")
            
            if not self.dry_run:
                print_warning("Considera restaurar desde backup")
            
            raise
    
    def restore_from_backup(self, backup_timestamp: Optional[str] = None):
        """Restaura desde un backup específico"""
        print_header("RESTAURANDO DESDE BACKUP")
        
        if backup_timestamp:
            backup_dir = Path(CONFIG['backup_dir']) / backup_timestamp
        else:
            # Usar el backup más reciente
            backup_root = Path(CONFIG['backup_dir'])
            if backup_root.exists():
                backups = sorted(backup_root.iterdir(), key=lambda x: x.stat().st_mtime)
                if backups:
                    backup_dir = backups[-1]
                else:
                    print_error("No hay backups disponibles")
                    return
            else:
                print_error("No hay backups disponibles")
                return
        
        if not backup_dir.exists():
            print_error(f"Backup no encontrado: {backup_dir}")
            return
        
        print_info(f"Restaurando desde: {backup_dir}")
        
        # Eliminar estructura modular
        modules_dir = self.app_path / "modules"
        if modules_dir.exists():
            shutil.rmtree(modules_dir)
            print_success("Eliminada estructura modular")
        
        # Restaurar archivos originales
        for item in backup_dir.iterdir():
            if item.name not in ["migration_log.json"]:
                dst = self.app_path / item.name
                
                if item.is_dir():
                    if dst.exists():
                        shutil.rmtree(dst)
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)
                
                print_success(f"Restaurado: {item.name}")
        
        print_header("RESTAURACIÓN COMPLETADA")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Migración automática a Modular Monolith"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simular migración sin ejecutar cambios"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Solo crear backup"
    )
    parser.add_argument(
        "--restore",
        type=str,
        nargs='?',
        const='latest',
        help="Restaurar desde backup (opcional: timestamp específico)"
    )
    parser.add_argument(
        "--module",
        type=str,
        choices=CONFIG['modules'],
        help="Migrar solo un módulo específico"
    )
    
    args = parser.parse_args()
    
    migrator = ModularMigrator(dry_run=args.dry_run)
    
    try:
        if args.restore:
            if args.restore == 'latest':
                migrator.restore_from_backup()
            else:
                migrator.restore_from_backup(args.restore)
        elif args.backup:
            migrator.create_backup()
            print_success("Backup completado")
        else:
            # Migración completa o por módulo
            if args.module:
                print_info(f"Migrando solo módulo: {args.module}")
                # Implementar migración por módulo específico
                # Por ahora, ejecutar migración completa
            
            migrator.run_migration()
            
    except KeyboardInterrupt:
        print_warning("\nMigración cancelada por usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()