"""Tests unitarios para helpers reutilizables de queries Supabase."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_MODULE_PATH = Path(__file__).resolve().parents[1] / "repositories" / "shared" / "query_helpers.py"
_SPEC = spec_from_file_location("test_query_helpers_module", _MODULE_PATH)
_MOD = module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MOD)

apply_date_range_filter = _MOD.apply_date_range_filter
apply_eq_filters = _MOD.apply_eq_filters
apply_order = _MOD.apply_order
apply_pagination = _MOD.apply_pagination
build_ilike_or = _MOD.build_ilike_or


class FakeQuery:
    """Query fake para registrar llamadas encadenadas."""

    def __init__(self):
        self.calls = []

    def eq(self, field, value):
        self.calls.append(("eq", field, value))
        return self

    def gte(self, field, value):
        self.calls.append(("gte", field, value))
        return self

    def lte(self, field, value):
        self.calls.append(("lte", field, value))
        return self

    def order(self, field, desc=True):
        self.calls.append(("order", field, desc))
        return self

    def range(self, start, end):
        self.calls.append(("range", start, end))
        return self


class TestQueryHelpers:
    """Tests para query_helpers."""

    def test_apply_eq_filters_omite_none_y_vacio(self):
        query = FakeQuery()
        result = apply_eq_filters(query, {"estatus": "ACTIVO", "empresa_id": None, "texto": ""})
        assert result is query
        assert query.calls == [("eq", "estatus", "ACTIVO")]

    def test_apply_eq_filters_sin_filters_regresa_query(self):
        query = FakeQuery()
        assert apply_eq_filters(query, None) is query
        assert query.calls == []

    def test_apply_order_aplica_desc(self):
        query = FakeQuery()
        apply_order(query, "fecha_creacion", desc=True)
        assert query.calls == [("order", "fecha_creacion", True)]

    def test_apply_pagination_aplica_range(self):
        query = FakeQuery()
        apply_pagination(query, 20, 40)
        assert query.calls == [("range", 40, 59)]

    def test_apply_pagination_omite_si_limit_none(self):
        query = FakeQuery()
        assert apply_pagination(query, None, 10) is query
        assert query.calls == []

    def test_apply_date_range_filter_aplica_start_y_end(self):
        query = FakeQuery()
        apply_date_range_filter(query, "fecha_pago", "2026-01-01", "2026-01-31")
        assert query.calls == [
            ("gte", "fecha_pago", "2026-01-01"),
            ("lte", "fecha_pago", "2026-01-31"),
        ]

    def test_build_ilike_or_genera_or_en_campos(self):
        value = build_ilike_or(" acme ", ["nombre_comercial", "razon_social"])
        assert value == (
            "nombre_comercial.ilike.%acme%,"
            "razon_social.ilike.%acme%"
        )

    def test_build_ilike_or_omite_campos_vacios(self):
        value = build_ilike_or("abc", ["nombre", ""])
        assert value == "nombre.ilike.%abc%"
