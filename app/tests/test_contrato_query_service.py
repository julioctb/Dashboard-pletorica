"""Tests para sincronización automática de vigencia en consultas de contratos."""

import asyncio

from app.services.contratos.queries import ContratoQueryService


class FakeContratoRepository:
    """Repositorio fake para validar orden de llamadas."""

    def __init__(self):
        self.calls = []

    async def sincronizar_vigencia_automatica(self):
        self.calls.append(("sincronizar_vigencia_automatica",))

    async def obtener_por_id(self, contrato_id: int):
        self.calls.append(("obtener_por_id", contrato_id))
        return {"id": contrato_id}

    async def obtener_todos(self, incluir_inactivos=False, limite=None, offset=0):
        self.calls.append(("obtener_todos", incluir_inactivos, limite, offset))
        return []

    async def buscar_por_texto(self, termino: str, limite: int = 10):
        self.calls.append(("buscar_por_texto", termino, limite))
        return []


class FakeContratoRoot:
    """Servicio root fake con solo el repositorio requerido."""

    def __init__(self):
        self.repository = FakeContratoRepository()


class TestContratoQueryService:
    """Protege la automatización de vigencia antes de leer contratos."""

    def test_obtener_por_id_sincroniza_vigencia_antes_de_leer(self):
        root = FakeContratoRoot()
        service = ContratoQueryService(root)

        result = asyncio.run(service.obtener_por_id(42))

        assert result == {"id": 42}
        assert root.repository.calls == [
            ("sincronizar_vigencia_automatica",),
            ("obtener_por_id", 42),
        ]

    def test_obtener_todos_sincroniza_vigencia_antes_de_listar(self):
        root = FakeContratoRoot()
        service = ContratoQueryService(root)

        result = asyncio.run(
            service.obtener_todos(incluir_inactivos=True, limite=25, offset=10)
        )

        assert result == []
        assert root.repository.calls == [
            ("sincronizar_vigencia_automatica",),
            ("obtener_todos", True, 25, 10),
        ]

    def test_busqueda_corta_no_dispara_sincronizacion(self):
        root = FakeContratoRoot()
        service = ContratoQueryService(root)

        result = asyncio.run(service.buscar_por_texto("a"))

        assert result == []
        assert root.repository.calls == []

    def test_busqueda_valida_sincroniza_vigencia_antes_de_busqueda(self):
        root = FakeContratoRoot()
        service = ContratoQueryService(root)

        result = asyncio.run(service.buscar_por_texto("BUAP", limite=5))

        assert result == []
        assert root.repository.calls == [
            ("sincronizar_vigencia_automatica",),
            ("buscar_por_texto", "BUAP", 5),
        ]
