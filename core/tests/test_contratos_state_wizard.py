"""Tests del wizard de contratos en creación y edición."""

from core.presentation.pages.backoffice.contratos import contratos_state as contratos_state_module


class _DummyWizardContratosState:
    _validar_paso = contratos_state_module.ContratosState._validar_paso
    _usa_folio_en_formulario = (
        contratos_state_module.ContratosState._usa_folio_en_formulario
    )
    _errores_paso_datos_formulario = (
        contratos_state_module.ContratosState._errores_paso_datos_formulario
    )

    def __init__(self, *, es_edicion: bool):
        self.es_edicion = es_edicion
        self.form_empresa_id = ""
        self.form_folio_buap = ""
        self.form_tipo_contrato = contratos_state_module.TipoContrato.SERVICIOS.value
        self.form_tipo_servicio_id = ""
        self.form_fecha_inicio = ""
        self.form_fecha_fin = ""
        self.form_tipo_duracion = ""
        self.form_descripcion_objeto = ""
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
    dummy.form_folio_buap = "X" * 200

    result = dummy._validar_paso(1)

    assert dummy.folio_validado is True
    assert dummy.error_folio_buap == "Formato inválido"
    assert "Folio institución:" in result


class _DummyDescripcionOpcionalState:
    def __init__(self, valor: str):
        self.form_descripcion_objeto = valor
        self.error_descripcion_objeto = "Error previo"

    def validar_y_asignar_error(self, *, valor, validador, error_attr):
        setattr(self, error_attr, validador(valor))


class _DummyPuedeGuardarState:
    _usa_desglose_categorias_plazas = lambda self: False

    def __init__(self):
        self.form_empresa_id = "1"
        self.form_tipo_contrato = contratos_state_module.TipoContrato.ADQUISICION.value
        self.form_modalidad_adjudicacion = (
            contratos_state_module.ModalidadAdjudicacion.ADJUDICACION_DIRECTA.value
        )
        self.form_fecha_inicio = "2026-03-11"
        self.form_descripcion_objeto = ""
        self.form_tipo_servicio_id = ""
        self.form_tipo_duracion = ""
        self.form_fecha_fin = ""
        self.form_tiene_personal = False
        self.form_cantidad_plazas_minima = ""
        self.form_cantidad_plazas_maxima = ""
        self.tiene_errores_formulario = False
        self.saving = False


class _DummyWizardLayoutState:
    _mostrar_paso_plazas_wizard = (
        contratos_state_module.ContratosState._mostrar_paso_plazas_wizard
    )
    _obtener_total_pasos_wizard = (
        contratos_state_module.ContratosState._obtener_total_pasos_wizard
    )
    _ajustar_paso_actual_wizard = (
        contratos_state_module.ContratosState._ajustar_paso_actual_wizard
    )

    def __init__(self, *, es_edicion: bool, tiene_personal: bool, paso_actual: int):
        self.es_edicion = es_edicion
        self.form_tipo_contrato = contratos_state_module.TipoContrato.SERVICIOS.value
        self.form_tiene_personal = tiene_personal
        self.form_paso_actual = paso_actual


class _DummyContratoDateSetterState:
    def __init__(self):
        self.form_fecha_inicio = ""
        self.form_fecha_fin = ""

    def _sincronizar_tipo_duracion(self):
        pass


class _DummyWizardRequiredFieldsState:
    _validar_paso = contratos_state_module.ContratosState._validar_paso
    _usa_folio_en_formulario = (
        contratos_state_module.ContratosState._usa_folio_en_formulario
    )
    _errores_paso_datos_formulario = (
        contratos_state_module.ContratosState._errores_paso_datos_formulario
    )
    _errores_paso_plazas_formulario = (
        contratos_state_module.ContratosState._errores_paso_plazas_formulario
    )
    _errores_guardado_borrador_formulario = (
        contratos_state_module.ContratosState._errores_guardado_borrador_formulario
    )
    _usa_desglose_categorias_plazas = lambda self: False

    def __init__(self, tipo_contrato: str):
        self.es_edicion = False
        self.saving = False
        self.form_tipo_contrato = tipo_contrato
        self.form_empresa_id = ""
        self.form_tipo_servicio_id = ""
        self.form_fecha_inicio = ""
        self.form_fecha_fin = ""
        self.form_descripcion_objeto = ""
        self.form_tipo_duracion = ""
        self.form_tiene_personal = False
        self.form_cantidad_plazas_minima = ""
        self.form_cantidad_plazas_maxima = ""
        self.form_paso_actual = 1
        self.error_empresa_id = ""
        self.error_tipo_contrato = ""
        self.error_tipo_servicio_id = ""
        self.error_folio_buap = ""
        self.error_fecha_inicio = ""
        self.error_fecha_fin = ""
        self.error_descripcion_objeto = ""

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

    def validar_y_asignar_error(self, *, valor, validador, error_attr):
        setattr(self, error_attr, validador(valor))

    def validar_empresa_id_campo(self):
        contratos_state_module.ContratosState.validar_empresa_id_campo.fn(self)

    def validar_tipo_contrato_campo(self):
        contratos_state_module.ContratosState.validar_tipo_contrato_campo.fn(self)

    def validar_fecha_inicio_campo(self):
        contratos_state_module.ContratosState.validar_fecha_inicio_campo.fn(self)

    def validar_descripcion_objeto_campo(self):
        contratos_state_module.ContratosState.validar_descripcion_objeto_campo.fn(self)

    def validar_tipo_servicio_id_campo(self):
        contratos_state_module.ContratosState.validar_tipo_servicio_id_campo.fn(self)

    def validar_fecha_fin_campo(self):
        contratos_state_module.ContratosState.validar_fecha_fin_campo.fn(self)

    def _validar_campo(self, campo: str):
        if campo == "folio_buap":
            self.error_folio_buap = ""

    @property
    def puede_avanzar_desde_datos_wizard(self):
        return contratos_state_module.ContratosState.puede_avanzar_desde_datos_wizard.fget(self)

    @property
    def puede_avanzar_desde_plazas_wizard(self):
        return contratos_state_module.ContratosState.puede_avanzar_desde_plazas_wizard.fget(self)


def test_setters_de_fecha_normalizan_captura_manual():
    dummy = _DummyContratoDateSetterState()

    contratos_state_module.ContratosState.set_form_fecha_inicio.fn(dummy, "13/03/2026")
    contratos_state_module.ContratosState.set_form_fecha_fin.fn(dummy, "15/03/2026")

    assert dummy.form_fecha_inicio == "2026-03-13"
    assert dummy.form_fecha_fin == "2026-03-15"


def test_setters_de_fecha_conservan_captura_parcial():
    dummy = _DummyContratoDateSetterState()

    contratos_state_module.ContratosState.set_form_fecha_inicio.fn(dummy, "13/03/")

    assert dummy.form_fecha_inicio == "13/03/"

    @property
    def puede_guardar_borrador_contrato(self):
        return contratos_state_module.ContratosState.puede_guardar_borrador_contrato.fget(self)


class _DummyWizardNextStepState(_DummyWizardRequiredFieldsState):
    _mostrar_paso_plazas_wizard = (
        contratos_state_module.ContratosState._mostrar_paso_plazas_wizard
    )
    _obtener_total_pasos_wizard = (
        contratos_state_module.ContratosState._obtener_total_pasos_wizard
    )

    def __init__(self, tipo_contrato: str):
        super().__init__(tipo_contrato)
        self.form_paso_actual = 1
        self.form_tiene_personal = False
        self.mensajes = []

    def mostrar_mensaje(self, mensaje: str, tipo: str):
        self.mensajes.append((mensaje, tipo))


def test_validar_objeto_del_contrato_vacio_es_valido():
    dummy = _DummyDescripcionOpcionalState("")

    contratos_state_module.ContratosState.validar_descripcion_objeto_campo.fn(dummy)

    assert dummy.error_descripcion_objeto == ""


def test_puede_guardar_no_depende_del_objeto_del_contrato():
    dummy = _DummyPuedeGuardarState()

    result = contratos_state_module.ContratosState.puede_guardar.fget(dummy)

    assert result is True


def test_incluye_personal_arranca_desactivado_por_default():
    assert contratos_state_module.FORM_DEFAULTS["tiene_personal"] is False


def test_wizard_salta_plazas_cuando_no_hay_personal_en_creacion():
    dummy = _DummyWizardLayoutState(es_edicion=False, tiene_personal=False, paso_actual=2)
    dummy.mostrar_paso_plazas = (
        contratos_state_module.ContratosState.mostrar_paso_plazas.fget(dummy)
    )
    dummy.mostrar_paso_entregables = (
        contratos_state_module.ContratosState.mostrar_paso_entregables.fget(dummy)
    )

    assert dummy._obtener_total_pasos_wizard() == 2
    assert contratos_state_module.ContratosState.paso_actual_wizard.fget(dummy) == "entregables"


def test_wizard_elimina_plazas_en_edicion_si_no_hay_personal():
    dummy = _DummyWizardLayoutState(es_edicion=True, tiene_personal=False, paso_actual=2)

    dummy._ajustar_paso_actual_wizard()

    assert dummy._obtener_total_pasos_wizard() == 1
    assert dummy.form_paso_actual == 1


def test_paso_datos_bloquea_campos_base_requeridos_vacios():
    dummy = _DummyWizardRequiredFieldsState("")

    result = dummy._validar_paso(1)

    assert "Empresa:" in result
    assert "Tipo de contrato:" in result
    assert "Fecha de inicio:" in result
    assert "Tipo de servicio:" not in result
    assert "Fecha de fin:" not in result
    assert "Objeto del contrato:" not in result
    assert "Folio institución:" not in result


def test_paso_datos_bloquea_tipo_servicio_en_contratos_de_servicios():
    dummy = _DummyWizardRequiredFieldsState(
        contratos_state_module.TipoContrato.SERVICIOS.value
    )

    result = dummy._validar_paso(1)

    assert "Tipo de servicio:" in result
    assert "Fecha de inicio:" in result
    assert "Fecha de fin:" not in result
    assert "Objeto del contrato:" not in result
    assert "Folio institución:" not in result


def test_no_avanza_a_plazas_si_hay_pendientes_en_datos():
    dummy = _DummyWizardNextStepState(
        contratos_state_module.TipoContrato.SERVICIOS.value
    )

    contratos_state_module.ContratosState.ir_paso_siguiente.fn(dummy)

    assert dummy.form_paso_actual == 1
    assert dummy.mensajes
    mensaje, tipo = dummy.mensajes[-1]
    assert tipo == "error"
    assert "Empresa:" in mensaje
    assert "Tipo de servicio:" in mensaje
    assert "Fecha de inicio:" in mensaje


def test_click_en_paso_2_no_avanza_si_hay_pendientes_en_datos():
    dummy = _DummyWizardNextStepState(
        contratos_state_module.TipoContrato.SERVICIOS.value
    )

    contratos_state_module.ContratosState.set_form_paso_actual.fn(dummy, 2)

    assert dummy.form_paso_actual == 1
    assert dummy.mensajes
    mensaje, tipo = dummy.mensajes[-1]
    assert tipo == "error"
    assert "Empresa:" in mensaje
    assert "Tipo de servicio:" in mensaje
    assert "Fecha de inicio:" in mensaje


def test_paso_2_permanece_bloqueado_si_datos_esta_incompleto():
    dummy = _DummyWizardRequiredFieldsState(
        contratos_state_module.TipoContrato.SERVICIOS.value
    )

    assert contratos_state_module.ContratosState.puede_avanzar_desde_datos_wizard.fget(dummy) is False
    assert contratos_state_module.ContratosState.puede_navegar_a_paso_2_wizard.fget(dummy) is False


def test_paso_2_se_habilita_solo_cuando_datos_esta_completo():
    dummy = _DummyWizardRequiredFieldsState(
        contratos_state_module.TipoContrato.SERVICIOS.value
    )
    dummy.form_empresa_id = "1"
    dummy.form_tipo_servicio_id = "2"
    dummy.form_fecha_inicio = "2026-03-12"

    assert contratos_state_module.ContratosState.puede_avanzar_desde_datos_wizard.fget(dummy) is True
    assert contratos_state_module.ContratosState.puede_navegar_a_paso_2_wizard.fget(dummy) is True


def test_guardar_borrador_requiere_minimo_del_paso_datos():
    dummy = _DummyWizardRequiredFieldsState(
        contratos_state_module.TipoContrato.SERVICIOS.value
    )

    assert contratos_state_module.ContratosState.puede_guardar_borrador_contrato.fget(dummy) is False


def test_guardar_borrador_se_habilita_con_datos_minimos_validos():
    dummy = _DummyWizardRequiredFieldsState(
        contratos_state_module.TipoContrato.SERVICIOS.value
    )
    dummy.form_empresa_id = "1"
    dummy.form_tipo_servicio_id = "2"
    dummy.form_fecha_inicio = "2026-03-12"

    assert contratos_state_module.ContratosState.puede_guardar_borrador_contrato.fget(dummy) is True


def test_guardar_borrador_se_bloquea_si_plazas_queda_incompleto():
    dummy = _DummyWizardRequiredFieldsState(
        contratos_state_module.TipoContrato.SERVICIOS.value
    )
    dummy.form_empresa_id = "1"
    dummy.form_tipo_servicio_id = "2"
    dummy.form_fecha_inicio = "2026-03-12"
    dummy.form_tiene_personal = True
    dummy.form_cantidad_plazas_minima = "5"
    dummy.form_cantidad_plazas_maxima = ""

    assert contratos_state_module.ContratosState.puede_guardar_borrador_contrato.fget(dummy) is False
