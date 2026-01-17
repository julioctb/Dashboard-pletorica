"""
Tests para validación de entidades con FieldConfig.

Verifica que:
- Los validadores transforman valores correctamente (uppercase, strip)
- Los patrones de validación funcionan
- Los mensajes de error son consistentes
- Los helpers pydantic_field y campo_validador funcionan correctamente
"""
import pytest
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ValidationError

from app.entities.empresa import Empresa, EmpresaCreate, EmpresaUpdate
from app.entities.tipo_servicio import TipoServicio, TipoServicioCreate, TipoServicioUpdate
from app.core.enums import TipoEmpresa, EstatusEmpresa, Estatus
from app.core.validation import (
    CAMPO_RFC,
    CAMPO_EMAIL,
    CAMPO_TELEFONO,
    CAMPO_NOMBRE_COMERCIAL,
    pydantic_field,
    campo_validador,
)


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


# =============================================================================
# TESTS PARA PYDANTIC HELPERS
# =============================================================================

class TestPydanticField:
    """Tests para pydantic_field() helper."""

    def test_genera_field_requerido(self):
        """pydantic_field genera Field requerido correctamente."""

        class ModeloTest(BaseModel):
            rfc: str = pydantic_field(CAMPO_RFC)

        # Debe fallar sin RFC
        with pytest.raises(ValidationError):
            ModeloTest()

    def test_genera_field_opcional(self):
        """pydantic_field genera Field opcional correctamente."""

        class ModeloTest(BaseModel):
            email: Optional[str] = pydantic_field(CAMPO_EMAIL)

        # No debe fallar sin email
        modelo = ModeloTest()
        assert modelo.email is None

    def test_respeta_min_length(self):
        """pydantic_field aplica min_length del FieldConfig."""

        class ModeloTest(BaseModel):
            nombre: str = pydantic_field(CAMPO_NOMBRE_COMERCIAL)

        # Debe fallar con nombre muy corto (min=2)
        with pytest.raises(ValidationError) as exc_info:
            ModeloTest(nombre="A")
        assert "2" in str(exc_info.value) or "short" in str(exc_info.value).lower()

    def test_respeta_max_length(self):
        """pydantic_field aplica max_length del FieldConfig."""

        class ModeloTest(BaseModel):
            nombre: str = pydantic_field(CAMPO_NOMBRE_COMERCIAL)

        # Debe fallar con nombre muy largo (max=100)
        with pytest.raises(ValidationError):
            ModeloTest(nombre="A" * 101)

    def test_override_funciona(self):
        """pydantic_field permite override de valores."""

        class ModeloTest(BaseModel):
            nombre: str = pydantic_field(CAMPO_NOMBRE_COMERCIAL, min_length=5)

        # Ahora min_length es 5 en lugar de 2
        with pytest.raises(ValidationError):
            ModeloTest(nombre="ABC")  # 3 < 5


class TestCampoValidador:
    """Tests para campo_validador() helper."""

    def test_transforma_a_mayusculas(self):
        """campo_validador aplica transformación str.upper."""

        class ModeloTest(BaseModel):
            rfc: str = pydantic_field(CAMPO_RFC)
            validar_rfc = campo_validador('rfc', CAMPO_RFC)

        modelo = ModeloTest(rfc="abc010101ab1")
        assert modelo.rfc == "ABC010101AB1"

    def test_transforma_email_a_minusculas(self):
        """campo_validador aplica transformación str.lower para email."""

        class ModeloTest(BaseModel):
            email: Optional[str] = pydantic_field(CAMPO_EMAIL)
            validar_email = campo_validador('email', CAMPO_EMAIL)

        modelo = ModeloTest(email="CORREO@EJEMPLO.COM")
        assert modelo.email == "correo@ejemplo.com"

    def test_valida_patron(self):
        """campo_validador valida patrón regex."""

        class ModeloTest(BaseModel):
            rfc: str = pydantic_field(CAMPO_RFC)
            validar_rfc = campo_validador('rfc', CAMPO_RFC)

        with pytest.raises(ValidationError) as exc_info:
            ModeloTest(rfc="INVALIDO123")
        assert "RFC" in str(exc_info.value)

    def test_permite_none_en_opcional(self):
        """campo_validador permite None en campos opcionales."""

        class ModeloTest(BaseModel):
            email: Optional[str] = pydantic_field(CAMPO_EMAIL)
            validar_email = campo_validador('email', CAMPO_EMAIL)

        modelo = ModeloTest(email=None)
        assert modelo.email is None

    def test_permite_vacio_en_opcional(self):
        """campo_validador permite string vacío en campos opcionales."""

        class ModeloTest(BaseModel):
            email: Optional[str] = pydantic_field(CAMPO_EMAIL)
            validar_email = campo_validador('email', CAMPO_EMAIL)

        modelo = ModeloTest(email="")
        assert modelo.email == ""


class TestIntegracionCompleta:
    """Tests de integración usando ambos helpers juntos."""

    def test_modelo_completo_con_helpers(self):
        """Modelo usando pydantic_field y campo_validador funciona correctamente."""

        class EmpleadoTest(BaseModel):
            rfc: str = pydantic_field(CAMPO_RFC)
            email: Optional[str] = pydantic_field(CAMPO_EMAIL)
            telefono: Optional[str] = pydantic_field(CAMPO_TELEFONO)

            validar_rfc = campo_validador('rfc', CAMPO_RFC)
            validar_email = campo_validador('email', CAMPO_EMAIL)
            validar_telefono = campo_validador('telefono', CAMPO_TELEFONO)

        # Crear con valores válidos
        empleado = EmpleadoTest(
            rfc="abc010101ab1",
            email="CORREO@EJEMPLO.COM",
            telefono="(55) 1234-5678"
        )

        # Verificar transformaciones
        assert empleado.rfc == "ABC010101AB1"  # Mayúsculas
        assert empleado.email == "correo@ejemplo.com"  # Minúsculas
        assert empleado.telefono == "5512345678"  # Sin separadores

    def test_modelo_falla_con_datos_invalidos(self):
        """Modelo con helpers falla correctamente con datos inválidos."""

        class EmpleadoTest(BaseModel):
            rfc: str = pydantic_field(CAMPO_RFC)
            validar_rfc = campo_validador('rfc', CAMPO_RFC)

        # RFC inválido debe fallar
        with pytest.raises(ValidationError):
            EmpleadoTest(rfc="INVALIDO")
