"""Pruebas numéricas de cuotas IMSS."""

from datetime import date
from decimal import Decimal

from app.core.calculations.calculadora_imss import CalculadoraIMSS
from app.core.calculations.calculadora_isr import CalculadoraISR
from app.core.calculations.simulador_costo_patronal import CalculadoraCostoPatronal
from app.core.catalogs import CatalogoIMSS, CatalogoISR, CatalogoUMA, Tolerancias
from app.domain.models.costo_patronal import ConfiguracionEmpresa, Trabajador


def test_uma_2026_oficial_y_tope_sbc():
    assert CatalogoUMA.diario_vigente("2026-01-15") == Decimal("113.14")
    assert CatalogoUMA.diario_vigente("2026-02-15") == Decimal("117.31")
    assert CatalogoUMA.tope_sbc_vigente("2026-02-15") == Decimal("2932.75")
    assert CatalogoUMA.DIARIO == Decimal("117.31")
    assert CatalogoUMA.TOPE_SBC == Decimal("2932.75")


def test_tasa_cesantia_vejez_patronal_2026_por_rango():
    assert CatalogoIMSS.tasa_cesantia_vejez_patronal(
        Decimal("315.04"),
        Decimal("117.31"),
        salario_minimo_diario=Decimal("315.04"),
        ano=2026,
    ) == Decimal("0.03150")
    assert CatalogoIMSS.tasa_cesantia_vejez_patronal(
        Decimal("234.62"),
        Decimal("117.31"),
        ano=2026,
    ) == Decimal("0.04851")
    assert CatalogoIMSS.tasa_cesantia_vejez_patronal(
        Decimal("351.93"),
        Decimal("117.31"),
        salario_minimo_diario=Decimal("315.04"),
        ano=2026,
    ) == Decimal("0.06026")
    assert CatalogoIMSS.tasa_cesantia_vejez_patronal(
        Decimal("500.00"),
        Decimal("117.31"),
        salario_minimo_diario=Decimal("315.04"),
        ano=2026,
    ) == Decimal("0.07513")


def test_calculadora_imss_patronal_usa_cesantia_progresiva():
    resultado = CalculadoraIMSS().calcular_patronal(
        sbc_diario=500.00,
        dias=30,
        prima_riesgo=0.025984,
        uma_diaria=117.31,
        salario_minimo_diario=315.04,
        ano=2026,
    )

    assert resultado["cuota_fija"] == 717.94
    assert resultado["cesantia_vejez"] == 1126.95
    assert resultado["riesgo_trabajo"] == 389.76


def test_art36_solo_aplica_a_salario_minimo_exacto():
    assert Tolerancias.es_salario_minimo(Decimal("315.04"), Decimal("315.04"))
    assert not Tolerancias.es_salario_minimo(Decimal("318.00"), Decimal("315.04"))

    trabajador = Trabajador(nombre="Caso prueba", salario_diario=318.00)
    assert not trabajador.es_salario_minimo(315.04)


def test_configuracion_empresa_resuelve_fecha_fiscal_estable():
    config = ConfiguracionEmpresa(
        nombre="Empresa prueba",
        estado="puebla",
        prima_riesgo=0.025984,
    )

    assert config.fecha_calculo == date(2026, 2, 1)
    assert config.salario_minimo_aplicable == 315.04


def test_isr_subsidio_2026_usa_uma_vigente():
    assert CatalogoISR.calcular_subsidio(
        Decimal("10000.00"),
        date(2026, 3, 15),
    ) == Decimal("535.65")

    resultado = CalculadoraISR().calcular(
        10000.00,
        es_salario_minimo=False,
        fecha_referencia=date(2026, 3, 15),
    )

    assert resultado["isr_antes_subsidio"] == 729.02
    assert resultado["subsidio_empleo"] == 535.65
    assert resultado["isr_a_retener"] == 193.37


def test_simulador_costo_patronal_usa_fecha_fiscal_en_isr():
    config = ConfiguracionEmpresa(
        nombre="Empresa prueba",
        estado="puebla",
        prima_riesgo=0.025984,
        fecha_referencia=date(2026, 3, 15),
    )
    trabajador = Trabajador(
        nombre="Trabajador prueba",
        salario_diario=333.34,
        antiguedad_anos=1,
    )

    resultado = CalculadoraCostoPatronal(config).calcular(trabajador)

    assert round(resultado.salario_mensual, 2) == 10000.20
    assert resultado.subsidio_empleo == 535.65
