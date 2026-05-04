"""Tests unitarios del servicio de incapacidades."""

import asyncio
from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from app.domain.enums import (
    EstatusIncapacidad,
    OrigenIncapacidad,
    TipoCertificado,
    TipoIncapacidad,
)
from app.core.exceptions import BusinessRuleError
from app.domain.models.incapacidad import (
    CertificadoIncapacidadCreate,
    IncapacidadCreate,
)
from app.domain.services import (
    IncapacidadService as InitIncapacidadService,
    incapacidad_service as init_incapacidad_service,
)
from app.domain.services.incapacidad_service import (
    IncapacidadService,
    incapacidad_service,
)


class _FakeIncapacidadRepository:
    """Repositorio fake para validar lógica del servicio."""

    def __init__(self):
        self.contexto_plaza: dict | None = None
        self.contexto_laboral = {
            "plaza_id": 18,
            "contrato_id": 301,
            "sede_id": 7,
            "categoria_puesto_id": 11,
        }
        self.incapacidades: dict[int, dict] = {}
        self.certificados: dict[int, list[dict]] = {}
        self.incidencias_existentes: dict[str, dict] = {}
        self.registros_existentes: dict[str, dict] = {}
        self.upserted_incidencias: list[dict] = []
        self.upserted_registros: list[dict] = []
        self.actualizaciones_fecha_fin: list[tuple[int, date]] = []
        self.actualizaciones_estatus: list[tuple[int, str, date | None]] = []
        self.next_incapacidad_id = 1
        self.next_certificado_id = 1

    def seed_incapacidad(
        self,
        *,
        incapacidad_id: int = 1,
        empleado_id: int = 9,
        plaza_id: int = 18,
        empresa_id: int = 44,
        origen: str = "FORMAL",
        tipo: str = "ENF_GENERAL",
        fecha_inicio: str = "2030-03-01",
        fecha_fin_estimada: str = "2030-03-03",
        estatus: str = "ACTIVA",
        porcentaje_pago: str = "100.00",
        registrado_por: str | None = "00000000-0000-0000-0000-000000000111",
    ) -> int:
        self.incapacidades[incapacidad_id] = {
            "id": incapacidad_id,
            "empleado_id": empleado_id,
            "plaza_id": plaza_id,
            "empresa_id": empresa_id,
            "origen": origen,
            "tipo": tipo,
            "fecha_inicio": fecha_inicio,
            "fecha_fin_estimada": fecha_fin_estimada,
            "estatus": estatus,
            "porcentaje_pago": porcentaje_pago,
            "requiere_cobertura": False,
            "notas": None,
            "registrado_por": registrado_por,
        }
        self.certificados.setdefault(incapacidad_id, [])
        self.next_incapacidad_id = max(self.next_incapacidad_id, incapacidad_id + 1)
        return incapacidad_id

    def seed_certificado(
        self,
        *,
        incapacidad_id: int = 1,
        certificado_id: int = 1,
        fecha_inicio: str = "2030-03-01",
        fecha_fin: str = "2030-03-03",
        dias_certificado: int = 3,
        folio_imss: str = "IMSS-001",
        tipo_certificado: str = "INICIAL",
    ) -> int:
        self.certificados.setdefault(incapacidad_id, []).append(
            {
                "id": certificado_id,
                "incapacidad_id": incapacidad_id,
                "folio_imss": folio_imss,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "dias_certificado": dias_certificado,
                "tipo_certificado": tipo_certificado,
                "archivo_id": None,
            }
        )
        self.next_certificado_id = max(self.next_certificado_id, certificado_id + 1)
        return certificado_id

    async def crear_incapacidad(self, data: dict) -> dict:
        incapacidad_id = self.next_incapacidad_id
        self.next_incapacidad_id += 1
        row = {"id": incapacidad_id, **data}
        self.incapacidades[incapacidad_id] = row
        self.certificados.setdefault(incapacidad_id, [])
        return dict(row)

    async def crear_certificado(self, data: dict) -> dict:
        certificado_id = self.next_certificado_id
        self.next_certificado_id += 1
        row = {"id": certificado_id, **data}
        self.certificados.setdefault(row["incapacidad_id"], []).append(row)
        return dict(row)

    async def obtener_por_id(self, incapacidad_id: int) -> dict | None:
        incapacidad = self.incapacidades.get(incapacidad_id)
        if incapacidad is None:
            return None
        plaza_id = int(
            incapacidad.get("plaza_id")
            or (self.contexto_plaza or {}).get("id")
            or self.contexto_laboral.get("plaza_id")
            or 0
        )
        contrato_id = int(
            (self.contexto_plaza or {}).get("contrato_id")
            or self.contexto_laboral.get("contrato_id")
            or 0
        )
        return {
            **incapacidad,
            "empleados": {
                "id": incapacidad["empleado_id"],
                "uuid": "00000000-0000-0000-0000-000000000999",
                "clave": "EMP-009",
                "nombre": "ANA",
                "apellido_paterno": "PEREZ",
                "apellido_materno": "LOPEZ",
            },
            "plazas": {
                "id": plaza_id,
                "contrato_id": contrato_id,
                "categorias_puesto": {"nombre": "Auxiliar"},
                "sedes": {"nombre": "Ciudad Universitaria", "codigo": "CU"},
            },
            "certificados_incapacidad": [
                dict(item)
                for item in self.certificados.get(incapacidad_id, [])
            ],
        }

    async def listar_por_empleado(self, empleado_id: int) -> list[dict]:
        resultados = []
        for incapacidad_id, row in self.incapacidades.items():
            if int(row.get("empleado_id") or 0) == empleado_id:
                resultados.append(await self.obtener_por_id(incapacidad_id))
        return resultados

    async def listar_activas_por_empresa(self, empresa_id: int) -> list[dict]:
        resultados = []
        for incapacidad_id, row in self.incapacidades.items():
            if (
                int(row.get("empresa_id") or 0) == empresa_id
                and str(row.get("estatus") or "").upper() == EstatusIncapacidad.ACTIVA.value
            ):
                resultados.append(await self.obtener_por_id(incapacidad_id))
        return resultados

    async def listar_por_empresa(self, empresa_id: int) -> list[dict]:
        resultados = []
        for incapacidad_id, row in self.incapacidades.items():
            if int(row.get("empresa_id") or 0) == empresa_id:
                resultados.append(await self.obtener_por_id(incapacidad_id))
        return resultados

    async def obtener_abierta_por_empleado(self, empleado_id: int) -> dict | None:
        for incapacidad_id, row in sorted(
            self.incapacidades.items(),
            key=lambda item: item[1].get("fecha_inicio", ""),
            reverse=True,
        ):
            if (
                int(row.get("empleado_id") or 0) == empleado_id
                and str(row.get("estatus") or "").upper() != EstatusIncapacidad.CERRADA.value
            ):
                return await self.obtener_por_id(incapacidad_id)
        return None

    async def obtener_activa_por_plaza(self, plaza_id: int) -> dict | None:
        for incapacidad_id, row in self.incapacidades.items():
            if (
                int(row.get("plaza_id") or 0) == plaza_id
                and str(row.get("estatus") or "").upper() == EstatusIncapacidad.ACTIVA.value
            ):
                return await self.obtener_por_id(incapacidad_id)
        return None

    async def actualizar_estatus(
        self,
        incapacidad_id: int,
        estatus: str,
        fecha_fin_real: date | None = None,
    ) -> dict:
        self.actualizaciones_estatus.append((incapacidad_id, estatus, fecha_fin_real))
        self.incapacidades[incapacidad_id]["estatus"] = estatus
        self.incapacidades[incapacidad_id]["fecha_fin_real"] = (
            fecha_fin_real.isoformat() if fecha_fin_real else None
        )
        return dict(self.incapacidades[incapacidad_id])

    async def actualizar_fecha_fin_estimada(
        self,
        incapacidad_id: int,
        fecha_fin_estimada: date,
    ) -> dict:
        self.actualizaciones_fecha_fin.append((incapacidad_id, fecha_fin_estimada))
        self.incapacidades[incapacidad_id]["fecha_fin_estimada"] = fecha_fin_estimada.isoformat()
        return dict(self.incapacidades[incapacidad_id])

    async def contar_por_empresa(self, empresa_id: int) -> dict:
        rows = await self.listar_por_empresa(empresa_id)
        return {
            "activas": sum(
                1
                for row in rows
                if str(row.get("estatus") or "").upper() == EstatusIncapacidad.ACTIVA.value
            ),
            "vencidas": sum(
                1
                for row in rows
                if str(row.get("estatus") or "").upper() == EstatusIncapacidad.VENCIDA.value
            ),
            "total": len(rows),
        }

    async def obtener_contexto_plaza(self, plaza_id: int) -> dict | None:
        if self.contexto_plaza is None:
            return None
        return dict(self.contexto_plaza)

    async def obtener_contexto_laboral_empleado(self, empleado_id: int) -> dict | None:
        return dict(self.contexto_laboral)

    async def obtener_incidencia_asistencia(self, empleado_id: int, fecha: date) -> dict | None:
        return self.incidencias_existentes.get(fecha.isoformat())

    async def upsert_incidencia_asistencia(self, data: dict) -> dict:
        row = {"id": len(self.upserted_incidencias) + 1, **data}
        self.upserted_incidencias.append(row)
        return row

    async def obtener_registro_asistencia(self, empleado_id: int, fecha: date) -> dict | None:
        return self.registros_existentes.get(fecha.isoformat())

    async def upsert_registro_asistencia(self, data: dict) -> dict:
        row = {"id": len(self.upserted_registros) + 1, **data}
        self.upserted_registros.append(row)
        return row


def _build_datos(**overrides) -> IncapacidadCreate:
    data = IncapacidadCreate(
        empleado_id=9,
        plaza_id=None,
        contrato_id=None,
        empresa_id=44,
        origen=OrigenIncapacidad.FORMAL,
        tipo=TipoIncapacidad.ENF_GENERAL,
        fecha_inicio=date(2030, 3, 1),
        fecha_fin_estimada=date(2030, 3, 3),
        porcentaje_pago=Decimal("100.00"),
        requiere_cobertura=False,
        notas="Seguimiento clínico",
        registrado_por=UUID("00000000-0000-0000-0000-000000000111"),
        folio_imss="IMSS-001",
        dias_certificado=None,
        archivo_id=77,
    )
    return data.model_copy(update=overrides)


def test_app_services_expone_servicio_y_singleton_canonicos():
    assert InitIncapacidadService is IncapacidadService
    assert init_incapacidad_service is incapacidad_service


def test_registrar_incapacidad_formal_exige_folio_imss():
    service = IncapacidadService(repository=_FakeIncapacidadRepository())
    datos = _build_datos(folio_imss=None)

    with pytest.raises(BusinessRuleError) as raised:
        asyncio.run(service.registrar_incapacidad(datos))

    assert "folio IMSS" in str(raised.value)


def test_registrar_incapacidad_por_acuerdo_solo_acepta_tipo_acuerdo():
    service = IncapacidadService(repository=_FakeIncapacidadRepository())
    datos = _build_datos(
        origen=OrigenIncapacidad.POR_ACUERDO,
        tipo=TipoIncapacidad.ENF_GENERAL,
        folio_imss=None,
    )

    with pytest.raises(BusinessRuleError) as raised:
        asyncio.run(service.registrar_incapacidad(datos))

    assert "Por acuerdo" in str(raised.value)


def test_registrar_incapacidad_rechaza_fecha_final_previa_y_porcentaje_fuera_de_rango():
    service = IncapacidadService(repository=_FakeIncapacidadRepository())

    with pytest.raises(BusinessRuleError) as raised_fecha:
        asyncio.run(
            service.registrar_incapacidad(
                _build_datos(
                    fecha_fin_estimada=date(2030, 2, 28),
                    folio_imss="IMSS-001",
                )
            )
        )
    assert "fecha de inicio" in str(raised_fecha.value)

    with pytest.raises(BusinessRuleError) as raised_porcentaje:
        asyncio.run(
            service.registrar_incapacidad(
                _build_datos(
                    origen=OrigenIncapacidad.POR_ACUERDO,
                    tipo=TipoIncapacidad.ACUERDO,
                    folio_imss=None,
                    porcentaje_pago=Decimal("120"),
                )
            )
        )
    assert "porcentaje de pago" in str(raised_porcentaje.value)


def test_registrar_incapacidad_crea_certificado_inicial_y_sincroniza_todo_el_rango():
    repository = _FakeIncapacidadRepository()
    service = IncapacidadService(repository=repository)

    incapacidad = asyncio.run(service.registrar_incapacidad(_build_datos()))

    assert incapacidad.id == 1
    assert incapacidad.plaza_id == 18
    assert incapacidad.tipo == TipoIncapacidad.ENF_GENERAL
    assert incapacidad.estatus == EstatusIncapacidad.ACTIVA
    assert incapacidad.certificados[0].tipo_certificado == TipoCertificado.INICIAL
    assert incapacidad.certificados[0].folio_imss == "IMSS-001"
    assert len(repository.upserted_incidencias) == 3
    assert len(repository.upserted_registros) == 3
    assert {
        item["tipo_incidencia"]
        for item in repository.upserted_incidencias
    } == {"INCAPACIDAD_ENFERMEDAD"}
    assert {
        item["tipo_registro"]
        for item in repository.upserted_registros
    } == {"INCAPACIDAD_ENFERMEDAD"}
    assert {
        item["contrato_id"]
        for item in repository.upserted_registros
    } == {301}


def test_registrar_incapacidad_por_acuerdo_mapea_a_falta_justificada():
    repository = _FakeIncapacidadRepository()
    service = IncapacidadService(repository=repository)

    asyncio.run(
        service.registrar_incapacidad(
            _build_datos(
                origen=OrigenIncapacidad.POR_ACUERDO,
                tipo=TipoIncapacidad.ACUERDO,
                folio_imss=None,
                porcentaje_pago=Decimal("50.00"),
                fecha_fin_estimada=date(2030, 3, 2),
            )
        )
    )

    assert {
        item["tipo_incidencia"]
        for item in repository.upserted_incidencias
    } == {"FALTA_JUSTIFICADA"}
    assert {
        item["tipo_registro"]
        for item in repository.upserted_registros
    } == {"FALTA_JUSTIFICADA"}


def test_agregar_certificado_subsecuente_extiende_vigencia_y_sincroniza_rango_nuevo():
    repository = _FakeIncapacidadRepository()
    repository.seed_incapacidad()
    repository.seed_certificado()
    service = IncapacidadService(repository=repository)

    certificado = asyncio.run(
        service.agregar_certificado(
            CertificadoIncapacidadCreate(
                incapacidad_id=1,
                folio_imss="IMSS-002",
                fecha_inicio=date(2030, 3, 4),
                fecha_fin=date(2030, 3, 5),
                dias_certificado=2,
                tipo_certificado=TipoCertificado.SUBSECUENTE,
            )
        )
    )

    assert certificado.tipo_certificado == TipoCertificado.SUBSECUENTE
    assert repository.actualizaciones_fecha_fin == [(1, date(2030, 3, 5))]
    assert len(repository.certificados[1]) == 2
    assert len(repository.upserted_incidencias) == 2
    assert len(repository.upserted_registros) == 2


def test_registrar_incapacidad_rechaza_conflictos_con_captura_operativa():
    repository = _FakeIncapacidadRepository()
    repository.incidencias_existentes["2030-03-02"] = {
        "id": 44,
        "origen": "SUPERVISOR",
        "jornada_id": 9,
    }
    service = IncapacidadService(repository=repository)

    with pytest.raises(BusinessRuleError) as raised:
        asyncio.run(service.registrar_incapacidad(_build_datos()))

    assert "02/03/2030" in str(raised.value)
    assert repository.upserted_incidencias == []
    assert repository.upserted_registros == []


def test_registrar_incapacidad_rechaza_si_el_empleado_ya_tiene_una_abierta():
    repository = _FakeIncapacidadRepository()
    repository.seed_incapacidad(
        incapacidad_id=41,
        empleado_id=9,
        estatus=EstatusIncapacidad.VENCIDA.value,
        fecha_inicio="2030-02-01",
        fecha_fin_estimada="2030-02-05",
    )
    repository.seed_certificado(
        incapacidad_id=41,
        certificado_id=91,
        fecha_inicio="2030-02-01",
        fecha_fin="2030-02-05",
        dias_certificado=5,
        folio_imss="IMSS-OPEN",
    )
    service = IncapacidadService(repository=repository)

    with pytest.raises(BusinessRuleError) as raised:
        asyncio.run(service.registrar_incapacidad(_build_datos()))

    mensaje = str(raised.value)
    assert "ya tiene una incapacidad abierta" in mensaje
    assert "01/02/2030" in mensaje
    assert "05/02/2030" in mensaje
    assert repository.upserted_incidencias == []
    assert repository.upserted_registros == []


def test_registrar_incapacidad_rechaza_conflictos_con_registro_consolidado():
    repository = _FakeIncapacidadRepository()
    repository.registros_existentes["2030-03-03"] = {
        "id": 81,
        "jornada_id": None,
        "es_consolidado": True,
    }
    service = IncapacidadService(repository=repository)

    with pytest.raises(BusinessRuleError) as raised:
        asyncio.run(service.registrar_incapacidad(_build_datos()))

    assert "03/03/2030" in str(raised.value)
    assert repository.upserted_incidencias == []
    assert repository.upserted_registros == []
