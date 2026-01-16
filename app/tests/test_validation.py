"""
Tests para validación de entidades con FieldConfig.

Verifica que:
- Los validadores transforman valores correctamente (uppercase, strip)
- Los patrones de validación funcionan
- Los mensajes de error son consistentes
"""
import pytest
from decimal import Decimal
from pydantic import ValidationError

from app.entities.empresa import Empresa, EmpresaCreate, EmpresaUpdate
from app.entities.tipo_servicio import TipoServicio, TipoServicioCreate, TipoServicioUpdate
from app.core.enums import TipoEmpresa, EstatusEmpresa, Estatus


class TestEmpresaValidation:
    """Tests de validación para Empresa."""

    def test_nombre_comercial_se_convierte_a_mayusculas(self):
        """nombre_comercial debe convertirse a mayúsculas."""
        empresa = Empresa(
            nombre_comercial="test empresa",
            razon_social="razon social",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="ABC010101AB1"
        )
        assert empresa.nombre_comercial == "TEST EMPRESA"

    def test_razon_social_se_convierte_a_mayusculas(self):
        """razon_social debe convertirse a mayúsculas."""
        empresa = Empresa(
            nombre_comercial="empresa",
            razon_social="mi razon social sa de cv",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="ABC010101AB1"
        )
        assert empresa.razon_social == "MI RAZON SOCIAL SA DE CV"

    def test_rfc_se_convierte_a_mayusculas(self):
        """RFC debe convertirse a mayúsculas."""
        empresa = Empresa(
            nombre_comercial="empresa",
            razon_social="razon",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="abc010101ab1"
        )
        assert empresa.rfc == "ABC010101AB1"

    def test_email_se_convierte_a_minusculas(self):
        """Email debe convertirse a minúsculas."""
        empresa = Empresa(
            nombre_comercial="empresa",
            razon_social="razon",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="ABC010101AB1",
            email="CORREO@EJEMPLO.COM"
        )
        assert empresa.email == "correo@ejemplo.com"

    def test_telefono_elimina_separadores(self):
        """Teléfono debe eliminar espacios, guiones y paréntesis."""
        empresa = Empresa(
            nombre_comercial="empresa",
            razon_social="razon",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="ABC010101AB1",
            telefono="(55) 1234-5678"
        )
        assert empresa.telefono == "5512345678"

    def test_telefono_con_codigo_pais_falla(self):
        """Teléfono con código de país falla porque resulta en 12 dígitos."""
        # +52 55 1234 5678 -> 525512345678 (12 dígitos, patrón requiere 10)
        with pytest.raises(ValidationError) as exc_info:
            Empresa(
                nombre_comercial="empresa",
                razon_social="razon",
                tipo_empresa=TipoEmpresa.NOMINA,
                rfc="ABC010101AB1",
                telefono="+52 55 1234 5678"
            )
        assert "10 dígitos" in str(exc_info.value) or "teléfono" in str(exc_info.value).lower()

    def test_rfc_invalido_falla(self):
        """RFC con formato inválido debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            Empresa(
                nombre_comercial="empresa",
                razon_social="razon",
                tipo_empresa=TipoEmpresa.NOMINA,
                rfc="INVALIDO"
            )
        assert "RFC" in str(exc_info.value)

    def test_rfc_muy_corto_falla(self):
        """RFC muy corto debe fallar con mensaje específico."""
        with pytest.raises(ValidationError) as exc_info:
            Empresa(
                nombre_comercial="empresa",
                razon_social="razon",
                tipo_empresa=TipoEmpresa.NOMINA,
                rfc="ABC"
            )
        # Mensaje de validar_rfc_detallado
        error_msg = str(exc_info.value)
        assert "12" in error_msg or "13" in error_msg or "RFC" in error_msg

    def test_nombre_comercial_muy_corto_falla(self):
        """Nombre comercial menor a 2 caracteres debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            Empresa(
                nombre_comercial="A",
                razon_social="razon social",
                tipo_empresa=TipoEmpresa.NOMINA,
                rfc="ABC010101AB1"
            )
        # Mensaje de FieldConfig o Pydantic Field
        error_msg = str(exc_info.value).lower()
        assert "2" in error_msg or "caracteres" in error_msg or "nombre" in error_msg

    def test_email_invalido_falla(self):
        """Email con formato inválido debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            Empresa(
                nombre_comercial="empresa",
                razon_social="razon",
                tipo_empresa=TipoEmpresa.NOMINA,
                rfc="ABC010101AB1",
                email="correo-invalido"
            )
        assert "email" in str(exc_info.value).lower() or "correo" in str(exc_info.value).lower()

    def test_prima_riesgo_porcentaje_se_convierte(self):
        """Prima de riesgo en porcentaje (2.5) se convierte a decimal (0.025)."""
        empresa = Empresa(
            nombre_comercial="empresa",
            razon_social="razon",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="ABC010101AB1",
            prima_riesgo=Decimal("2.5")  # 2.5%
        )
        assert empresa.prima_riesgo == Decimal("0.025")

    def test_prima_riesgo_decimal_se_mantiene(self):
        """Prima de riesgo ya en decimal se mantiene."""
        empresa = Empresa(
            nombre_comercial="empresa",
            razon_social="razon",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="ABC010101AB1",
            prima_riesgo=Decimal("0.02598")
        )
        assert empresa.prima_riesgo == Decimal("0.02598")

    def test_prima_riesgo_fuera_de_rango_falla(self):
        """Prima de riesgo fuera de 0.5% - 15% debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            Empresa(
                nombre_comercial="empresa",
                razon_social="razon",
                tipo_empresa=TipoEmpresa.NOMINA,
                rfc="ABC010101AB1",
                prima_riesgo=Decimal("20")  # 20% > 15%
            )
        assert "prima" in str(exc_info.value).lower() or "rango" in str(exc_info.value).lower()

    def test_registro_patronal_se_formatea(self):
        """Registro patronal se formatea correctamente."""
        empresa = Empresa(
            nombre_comercial="empresa",
            razon_social="razon",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="ABC010101AB1",
            registro_patronal="Y1234567101"
        )
        assert empresa.registro_patronal == "Y12-34567-10-1"


class TestTipoServicioValidation:
    """Tests de validación para TipoServicio."""

    def test_clave_se_convierte_a_mayusculas(self):
        """Clave debe convertirse a mayúsculas."""
        tipo = TipoServicio(
            clave="jar",
            nombre="Jardinería"
        )
        assert tipo.clave == "JAR"

    def test_nombre_se_convierte_a_mayusculas(self):
        """Nombre debe convertirse a mayúsculas."""
        tipo = TipoServicio(
            clave="JAR",
            nombre="jardinería"
        )
        assert tipo.nombre == "JARDINERÍA"

    def test_clave_muy_corta_falla(self):
        """Clave menor a 2 caracteres debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            TipoServicio(
                clave="J",
                nombre="Jardinería"
            )
        assert "2" in str(exc_info.value)

    def test_clave_muy_larga_falla(self):
        """Clave mayor a 5 caracteres debe fallar."""
        with pytest.raises(ValidationError) as exc_info:
            TipoServicio(
                clave="JARDÍN",  # 6 caracteres
                nombre="Jardinería"
            )
        assert "5" in str(exc_info.value)

    def test_clave_con_numeros_falla(self):
        """Clave con números debe fallar (solo letras permitidas)."""
        with pytest.raises(ValidationError) as exc_info:
            TipoServicio(
                clave="JAR1",
                nombre="Jardinería"
            )
        # El patrón es ^[A-Z]{2,5}$ - no permite números
        assert "pattern" in str(exc_info.value).lower() or "letras" in str(exc_info.value).lower()


class TestTipoServicioCreateValidation:
    """Tests de validación para TipoServicioCreate."""

    def test_clave_se_convierte_a_mayusculas(self):
        """Clave en create debe convertirse a mayúsculas."""
        tipo = TipoServicioCreate(
            clave="lim",
            nombre="limpieza"
        )
        assert tipo.clave == "LIM"
        assert tipo.nombre == "LIMPIEZA"


class TestTipoServicioUpdateValidation:
    """Tests de validación para TipoServicioUpdate."""

    def test_campos_opcionales_none(self):
        """Campos opcionales pueden ser None."""
        update = TipoServicioUpdate()
        assert update.clave is None
        assert update.nombre is None

    def test_clave_se_convierte_si_se_proporciona(self):
        """Si se proporciona clave, debe convertirse a mayúsculas."""
        update = TipoServicioUpdate(clave="mto")
        assert update.clave == "MTO"


class TestValidationConsistency:
    """Tests de consistencia entre entidades."""

    def test_empresa_y_create_mismas_reglas_rfc(self):
        """Empresa y EmpresaCreate deben tener mismas reglas para RFC."""
        # Ambos deben fallar con RFC inválido
        with pytest.raises(ValidationError):
            Empresa(
                nombre_comercial="empresa",
                razon_social="razon",
                tipo_empresa=TipoEmpresa.NOMINA,
                rfc="INVALIDO"
            )

        with pytest.raises(ValidationError):
            EmpresaCreate(
                nombre_comercial="empresa",
                razon_social="razon",
                tipo_empresa=TipoEmpresa.NOMINA,
                rfc="INVALIDO"
            )

    def test_tipo_servicio_estatus_default(self):
        """TipoServicio debe tener estatus ACTIVO por defecto."""
        tipo = TipoServicio(
            clave="JAR",
            nombre="Jardinería"
        )
        assert tipo.estatus == Estatus.ACTIVO

    def test_empresa_estatus_default(self):
        """Empresa debe tener estatus ACTIVO por defecto."""
        empresa = Empresa(
            nombre_comercial="empresa",
            razon_social="razon",
            tipo_empresa=TipoEmpresa.NOMINA,
            rfc="ABC010101AB1"
        )
        assert empresa.estatus == EstatusEmpresa.ACTIVO
