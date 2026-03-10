"""Tests del wizard de contratos en creación y edición."""

from app.presentation.pages.contratos import contratos_state as contratos_state_module


class _DummyWizardContratosState:
    _validar_paso = contratos_state_module.ContratosState._validar_paso
    _usa_folio_en_formulario = (
        contratos_state_module.ContratosState._usa_folio_en_formulario
    )

    def __init__(self, *, es_edicion: bool):
        self.es_edicion = es_edicion
        self.form_tipo_contrato = contratos_state_module.TipoContrato.SERVICIOS.value
        self.form_fecha_fin = ""
        self.error_empresa_id = ""
        self.error_tipo_contrato = ""
        self.error_tipo_servicio_id = ""
        self.error_folio_buap = ""
        self.error_fecha_inicio = ""
        self.error_fecha_fin = ""
        self.error_descripcion_objeto = ""
        self.folio_validado = False

    def limpiar_mensajes(self):
        pass

    def _limpiar_errores(self):
        self.error_empresa_id = ""
        self.error_tipo_contrato = ""
        self.error_tipo_servicio_id = ""
        self.error_folio_buap = ""
        self.error_fecha_inicio = ""
        self.error_fecha_fin = ""
        self.error_descripcion_objeto = ""

    def validar_empresa_id_campo(self):
        pass

    def validar_tipo_contrato_campo(self):
        pass

    def validar_fecha_inicio_campo(self):
        pass

    def validar_descripcion_objeto_campo(self):
        pass

    def validar_tipo_servicio_id_campo(self):
        pass

    def validar_fecha_fin_campo(self):
        pass

    def _validar_campo(self, campo: str):
        if campo == "folio_buap":
            self.folio_validado = True
            self.error_folio_buap = "Formato inválido"


def test_validar_paso_datos_creacion_omite_folio():
    dummy = _DummyWizardContratosState(es_edicion=False)

    result = dummy._validar_paso(1)

    assert dummy.folio_validado is False
    assert dummy.error_folio_buap == ""
    assert "Folio institución" not in result


def test_validar_paso_datos_edicion_mantiene_validacion_de_folio():
    dummy = _DummyWizardContratosState(es_edicion=True)

    result = dummy._validar_paso(1)

    assert dummy.folio_validado is True
    assert dummy.error_folio_buap == "Formato inválido"
    assert "Folio institución: Formato inválido" in result
