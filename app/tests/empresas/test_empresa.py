"""Tests para el módulo de empresas"""
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
