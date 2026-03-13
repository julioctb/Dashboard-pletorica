from datetime import date

from app.core.utils import (
    format_date_input_display,
    get_date_input_inline_error,
    normalize_date_input,
    parse_date_input,
)
from app.core.validation import validar_fecha_requerida, validar_fecha_rango


def test_parse_date_input_acepta_iso_y_ddmmyyyy():
    assert parse_date_input("2026-03-13") == date(2026, 3, 13)
    assert parse_date_input("13/03/2026") == date(2026, 3, 13)


def test_normalize_date_input_convierte_ddmmyyyy_a_iso():
    assert normalize_date_input("13/03/2026") == "2026-03-13"


def test_normalize_date_input_autoformatea_digitos_corridos():
    assert normalize_date_input("12012025") == "2025-01-12"


def test_normalize_date_input_autoformatea_captura_parcial_sin_slashes():
    assert normalize_date_input("1201") == "12/01"


def test_normalize_date_input_conserva_captura_parcial():
    assert normalize_date_input("13/03/") == "13/03/"


def test_format_date_input_display_muestra_ddmmyyyy():
    assert format_date_input_display("2026-03-13") == "13/03/2026"


def test_get_date_input_inline_error_detecta_anio_incompleto():
    assert (
        get_date_input_inline_error("13/03/26")
        == "Capture el año completo en formato AAAA"
    )


def test_get_date_input_inline_error_omite_anio_completo():
    assert get_date_input_inline_error("13/03/2026") == ""


def test_validadores_comunes_aceptan_ddmmyyyy():
    assert validar_fecha_requerida("13/03/2026", "fecha de inicio") == ""
    assert (
        validar_fecha_rango(
            "13/03/2026",
            "14/03/2026",
            nombre_inicio="fecha de inicio",
            nombre_fin="fecha de fin",
        )
        == ""
    )
