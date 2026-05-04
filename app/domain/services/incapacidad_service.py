"""Servicio de negocio para el módulo de incapacidades."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Iterable, Optional

from app.domain.enums import (
    EstatusIncapacidad,
    OrigenIncapacidad,
    OrigenIncidencia,
    TipoCertificado,
    TipoIncapacidad,
)
from app.core.exceptions import BusinessRuleError, DatabaseError, NotFoundError
from app.domain.models.incapacidad import (
    CertificadoIncapacidad,
    CertificadoIncapacidadCreate,
    Incapacidad,
    IncapacidadCreate,
    IncapacidadResumen,
)
from app.domain.repositories.incapacidad_repository import SupabaseIncapacidadRepository

logger = logging.getLogger(__name__)


class IncapacidadService:
    """Orquesta validación, persistencia y sincronización operativa."""

    def __init__(self, repository=None):
        if repository is None:
            repository = SupabaseIncapacidadRepository()
        self.repository = repository

    async def registrar_incapacidad(self, datos: IncapacidadCreate) -> Incapacidad:
        """Registra una incapacidad y su certificado inicial."""
        self._validar_registro(datos)
        await self._validar_empleado_sin_incapacidad_abierta(datos.empleado_id)

        fecha_fin_cert = self._resolver_fecha_fin_certificado(
            datos.fecha_inicio,
            datos.fecha_fin_estimada,
            datos.dias_certificado,
        )
        dias_certificado = self._resolver_dias_certificado(
            datos.fecha_inicio,
            fecha_fin_cert,
            datos.dias_certificado,
        )
        contexto = await self._resolver_contexto_operativo(
            empleado_id=datos.empleado_id,
            plaza_id=datos.plaza_id,
            contrato_id=datos.contrato_id,
        )

        incapacidad_payload = {
            "empleado_id": datos.empleado_id,
            "plaza_id": contexto["plaza_id"],
            "empresa_id": datos.empresa_id,
            "origen": self._enum_value(datos.origen),
            "tipo": self._enum_value(datos.tipo),
            "fecha_inicio": datos.fecha_inicio.isoformat(),
            "fecha_fin_estimada": fecha_fin_cert.isoformat(),
            "estatus": EstatusIncapacidad.ACTIVA.value,
            "porcentaje_pago": str(self._normalizar_porcentaje(datos)),
            "requiere_cobertura": bool(datos.requiere_cobertura),
            "notas": datos.notas,
            "registrado_por": str(datos.registrado_por) if datos.registrado_por else None,
        }
        incapacidad_row = await self.repository.crear_incapacidad(incapacidad_payload)
        incapacidad_id = int(incapacidad_row.get("id") or 0)
        if incapacidad_id <= 0:
            raise DatabaseError("No se pudo crear la incapacidad")

        certificado = CertificadoIncapacidadCreate(
            incapacidad_id=incapacidad_id,
            folio_imss=datos.folio_imss,
            fecha_inicio=datos.fecha_inicio,
            fecha_fin=fecha_fin_cert,
            dias_certificado=dias_certificado,
            tipo_certificado=TipoCertificado.INICIAL,
            archivo_id=datos.archivo_id,
        )
        certificado_row = await self.repository.crear_certificado(
            certificado.model_dump(mode="json", exclude_none=True)
        )
        if not certificado_row:
            raise DatabaseError("No se pudo crear el certificado inicial")

        await self._sincronizar_rango_operativo(
            empleado_id=datos.empleado_id,
            empresa_id=datos.empresa_id,
            contrato_id=contexto["contrato_id"],
            fecha_inicio=datos.fecha_inicio,
            fecha_fin=fecha_fin_cert,
            tipo=datos.tipo,
            origen=datos.origen,
            registrado_por=datos.registrado_por,
            archivo_id=datos.archivo_id,
            sede_real_id=contexto.get("sede_id"),
            folio_imss=datos.folio_imss,
        )

        incapacidad = await self.obtener_por_id(incapacidad_id)
        if incapacidad is None:
            raise DatabaseError("No se pudo reconstruir la incapacidad recién creada")
        return incapacidad

    async def agregar_certificado(
        self,
        datos: CertificadoIncapacidadCreate,
    ) -> CertificadoIncapacidad:
        """Agrega un certificado subsecuente y extiende la incapacidad."""
        incapacidad = await self.obtener_por_id(datos.incapacidad_id)
        if incapacidad is None:
            raise NotFoundError(f"Incapacidad {datos.incapacidad_id} no encontrada")
        if incapacidad.estatus == EstatusIncapacidad.CERRADA:
            raise BusinessRuleError("No se pueden agregar certificados a una incapacidad cerrada")

        fecha_fin = self._resolver_fecha_fin_certificado(
            datos.fecha_inicio,
            datos.fecha_fin,
            datos.dias_certificado,
        )
        dias_certificado = self._resolver_dias_certificado(
            datos.fecha_inicio,
            fecha_fin,
            datos.dias_certificado,
        )
        self._validar_certificado_subsecuente(incapacidad, datos, fecha_fin)

        tipo_certificado = TipoCertificado.SUBSECUENTE
        certificado_payload = CertificadoIncapacidadCreate(
            incapacidad_id=datos.incapacidad_id,
            folio_imss=datos.folio_imss,
            fecha_inicio=datos.fecha_inicio,
            fecha_fin=fecha_fin,
            dias_certificado=dias_certificado,
            tipo_certificado=tipo_certificado,
            archivo_id=datos.archivo_id,
        )
        certificado_row = await self.repository.crear_certificado(
            certificado_payload.model_dump(mode="json", exclude_none=True)
        )
        if not certificado_row:
            raise DatabaseError("No se pudo crear el certificado subsecuente")

        await self.repository.actualizar_fecha_fin_estimada(
            incapacidad.id,
            fecha_fin,
        )
        contexto = await self._resolver_contexto_operativo(
            empleado_id=incapacidad.empleado_id,
            plaza_id=incapacidad.plaza_id,
            contrato_id=None,
        )
        await self._sincronizar_rango_operativo(
            empleado_id=incapacidad.empleado_id,
            empresa_id=incapacidad.empresa_id,
            contrato_id=contexto["contrato_id"],
            fecha_inicio=datos.fecha_inicio,
            fecha_fin=fecha_fin,
            tipo=incapacidad.tipo,
            origen=incapacidad.origen,
            registrado_por=incapacidad.registrado_por,
            archivo_id=datos.archivo_id,
            sede_real_id=contexto.get("sede_id"),
            folio_imss=datos.folio_imss,
        )
        return CertificadoIncapacidad(**certificado_row)

    async def cerrar_incapacidad(
        self,
        incapacidad_id: int,
        fecha_reincorporacion: date,
    ) -> None:
        """Cierra una incapacidad al reincorporarse el empleado."""
        incapacidad = await self.obtener_por_id(incapacidad_id)
        if incapacidad is None:
            raise NotFoundError(f"Incapacidad {incapacidad_id} no encontrada")
        if fecha_reincorporacion < incapacidad.fecha_inicio:
            raise BusinessRuleError(
                "La fecha de reincorporación no puede ser anterior al inicio de la incapacidad"
            )

        await self.repository.actualizar_estatus(
            incapacidad_id,
            EstatusIncapacidad.CERRADA.value,
            fecha_fin_real=fecha_reincorporacion,
        )

    async def obtener_por_id(self, incapacidad_id: int) -> Optional[Incapacidad]:
        """Obtiene una incapacidad completa por ID."""
        row = await self.repository.obtener_por_id(incapacidad_id)
        if not row:
            return None
        return self._mapear_incapacidad(row)

    async def listar_por_empleado(self, empleado_id: int) -> list[IncapacidadResumen]:
        """Lista incapacidades de un empleado."""
        rows = await self.repository.listar_por_empleado(empleado_id)
        return [self._mapear_resumen(row) for row in rows]

    async def listar_por_empresa(self, empresa_id: int) -> list[IncapacidadResumen]:
        """Lista el historial completo de incapacidades de una empresa."""
        rows = await self.repository.listar_por_empresa(empresa_id)
        return [self._mapear_resumen(row) for row in rows]

    async def listar_activas_empresa(self, empresa_id: int) -> list[IncapacidadResumen]:
        """Lista incapacidades activas o vencidas de la empresa."""
        rows = await self.repository.listar_activas_por_empresa(empresa_id)
        return [self._mapear_resumen(row) for row in rows]

    async def obtener_conteos(self, empresa_id: int) -> dict:
        """Obtiene conteos dinámicos para tarjetas o dashboards."""
        rows = await self.repository.listar_por_empresa(empresa_id)
        resumenes = [self._mapear_resumen(row) for row in rows]
        return {
            "activas": sum(1 for item in resumenes if item.estatus == EstatusIncapacidad.ACTIVA),
            "vencidas": sum(1 for item in resumenes if item.estatus == EstatusIncapacidad.VENCIDA),
            "total": len(resumenes),
        }

    async def obtener_incapacidad_activa_plaza(
        self,
        plaza_id: int,
    ) -> Optional[IncapacidadResumen]:
        """Obtiene la incapacidad activa/vencida de una plaza."""
        row = await self.repository.obtener_activa_por_plaza(plaza_id)
        if not row:
            return None
        return self._mapear_resumen(row)

    async def obtener_contexto_operativo_empleado(
        self,
        empleado_id: int,
        *,
        plaza_id: Optional[int] = None,
        contrato_id: Optional[int] = None,
    ) -> dict:
        """Resuelve contexto laboral utilizable para registrar incapacidades."""
        return await self._resolver_contexto_operativo(
            empleado_id=empleado_id,
            plaza_id=plaza_id,
            contrato_id=contrato_id,
        )

    def _validar_registro(self, datos: IncapacidadCreate) -> None:
        origen = self._coerce_origen(datos.origen)
        tipo = self._coerce_tipo(datos.tipo)

        if origen == OrigenIncapacidad.FORMAL:
            if tipo == TipoIncapacidad.ACUERDO:
                raise BusinessRuleError(
                    "Las incapacidades formales solo aceptan tipos IMSS"
                )
            if TipoIncapacidad.requiere_folio(tipo) and not str(datos.folio_imss or "").strip():
                raise BusinessRuleError("El folio IMSS es obligatorio para incapacidades formales")
        elif tipo != TipoIncapacidad.ACUERDO:
            raise BusinessRuleError("Las incapacidades por acuerdo deben usar el tipo 'Por acuerdo'")

        fecha_fin = self._resolver_fecha_fin_certificado(
            datos.fecha_inicio,
            datos.fecha_fin_estimada,
            datos.dias_certificado,
        )
        if fecha_fin < datos.fecha_inicio:
            raise BusinessRuleError("La fecha final no puede ser anterior a la fecha de inicio")

        if datos.dias_certificado is not None and int(datos.dias_certificado) <= 0:
            raise BusinessRuleError("Los días del certificado deben ser mayores a 0")

        porcentaje = self._normalizar_porcentaje(datos)
        if porcentaje < Decimal("0") or porcentaje > Decimal("100"):
            raise BusinessRuleError("El porcentaje de pago debe estar entre 0 y 100")

    def _validar_certificado_subsecuente(
        self,
        incapacidad: Incapacidad,
        datos: CertificadoIncapacidadCreate,
        fecha_fin: date,
    ) -> None:
        if fecha_fin < datos.fecha_inicio:
            raise BusinessRuleError("La fecha final del certificado no puede ser anterior al inicio")

        ultimo = incapacidad.ultimo_certificado
        if ultimo and datos.fecha_inicio < ultimo.fecha_inicio:
            raise BusinessRuleError(
                "La fecha de inicio del certificado no puede ser anterior al historial ya registrado"
            )

        if incapacidad.es_formal and not str(datos.folio_imss or "").strip():
            raise BusinessRuleError("Los certificados de incapacidades formales requieren folio IMSS")

    async def _validar_empleado_sin_incapacidad_abierta(self, empleado_id: int) -> None:
        abierta = await self.repository.obtener_abierta_por_empleado(empleado_id)
        if not abierta:
            return

        incapacidad = self._mapear_incapacidad(abierta)
        fecha_inicio = incapacidad.fecha_inicio.strftime("%d/%m/%Y")
        fecha_fin = (
            incapacidad.fecha_fin_estimada.strftime("%d/%m/%Y")
            if incapacidad.fecha_fin_estimada is not None
            else "sin fecha de término"
        )
        tipo = self._coerce_tipo(incapacidad.tipo)
        raise BusinessRuleError(
            "El empleado ya tiene una incapacidad abierta "
            f"({tipo.descripcion.lower()}, {fecha_inicio} a {fecha_fin}). "
            "Cierre o renueve la incapacidad existente antes de registrar otra."
        )

    async def _resolver_contexto_operativo(
        self,
        *,
        empleado_id: int,
        plaza_id: Optional[int],
        contrato_id: Optional[int],
    ) -> dict:
        contexto = {}
        plaza_id_int = int(plaza_id or 0)
        contrato_id_int = int(contrato_id or 0)

        if plaza_id_int > 0:
            contexto = await self.repository.obtener_contexto_plaza(plaza_id_int) or {}

        if not contexto:
            contexto = await self.repository.obtener_contexto_laboral_empleado(empleado_id) or {}

        plaza_resuelta = plaza_id_int or int(contexto.get("plaza_id") or contexto.get("id") or 0)
        contrato_resuelto = contrato_id_int or int(contexto.get("contrato_id") or 0)
        sede_resuelta = int(contexto.get("sede_id") or 0) or None
        categoria_nombre = str(contexto.get("categoria_nombre") or "").strip() or None
        sede_nombre = str(contexto.get("sede_nombre") or "").strip() or None

        if contrato_resuelto <= 0:
            raise BusinessRuleError(
                "No se pudo resolver la plaza o contrato activo del empleado para sincronizar asistencias y nómina"
            )

        return {
            "plaza_id": plaza_resuelta or None,
            "contrato_id": contrato_resuelto,
            "sede_id": sede_resuelta,
            "categoria_nombre": categoria_nombre,
            "sede_nombre": sede_nombre,
        }

    async def _sincronizar_rango_operativo(
        self,
        *,
        empleado_id: int,
        empresa_id: int,
        contrato_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        tipo: TipoIncapacidad | str,
        origen: OrigenIncapacidad | str,
        registrado_por,
        archivo_id: Optional[int],
        sede_real_id: Optional[int],
        folio_imss: Optional[str],
    ) -> None:
        tipo_incapacidad = self._coerce_tipo(tipo)
        origen_incapacidad = self._coerce_origen(origen)
        conflictos = await self._validar_conflictos_rango(
            empleado_id=empleado_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        if conflictos:
            raise BusinessRuleError(
                "No se pudo registrar la incapacidad porque ya existen capturas operativas o registros consolidados en: "
                + ", ".join(fecha.strftime("%d/%m/%Y") for fecha in conflictos)
            )

        motivo = self._construir_motivo_operativo(
            origen=origen_incapacidad,
            tipo=tipo_incapacidad,
            folio_imss=folio_imss,
        )
        for fecha in self._iterar_fechas(fecha_inicio, fecha_fin):
            incidencia = await self.repository.upsert_incidencia_asistencia(
                {
                    "empleado_id": empleado_id,
                    "empresa_id": empresa_id,
                    "fecha": fecha.isoformat(),
                    "tipo_incidencia": tipo_incapacidad.tipo_incidencia_asistencia.value,
                    "minutos_retardo": 0,
                    "horas_extra": 0,
                    "motivo": motivo,
                    "documento_soporte_id": archivo_id,
                    "origen": OrigenIncidencia.RH.value,
                    "registrado_por": str(registrado_por) if registrado_por else None,
                    "sede_real_id": sede_real_id,
                    "jornada_id": None,
                }
            )
            incidencia_id = int(incidencia.get("id") or 0) or None
            await self.repository.upsert_registro_asistencia(
                {
                    "empleado_id": empleado_id,
                    "empresa_id": empresa_id,
                    "contrato_id": contrato_id,
                    "jornada_id": None,
                    "incidencia_id": incidencia_id,
                    "fecha": fecha.isoformat(),
                    "tipo_registro": tipo_incapacidad.tipo_registro_asistencia.value,
                    "hora_entrada": None,
                    "hora_salida": None,
                    "horas_trabajadas": None,
                    "horas_extra": 0,
                    "minutos_retardo": 0,
                    "sede_real_id": sede_real_id,
                    "es_consolidado": False,
                }
            )

    async def _validar_conflictos_rango(
        self,
        *,
        empleado_id: int,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> list[date]:
        conflictos: list[date] = []
        for fecha in self._iterar_fechas(fecha_inicio, fecha_fin):
            incidencia = await self.repository.obtener_incidencia_asistencia(empleado_id, fecha)
            if incidencia and (
                str(incidencia.get("origen") or "").upper() != OrigenIncidencia.RH.value
                or incidencia.get("jornada_id") is not None
            ):
                conflictos.append(fecha)
                continue

            registro = await self.repository.obtener_registro_asistencia(empleado_id, fecha)
            if registro and (
                registro.get("jornada_id") is not None
                or bool(registro.get("es_consolidado"))
            ):
                conflictos.append(fecha)
        return conflictos

    def _mapear_incapacidad(self, data: dict) -> Incapacidad:
        certificados = self._mapear_certificados(data.get("certificados_incapacidad") or [], data.get("id"))
        empleado = data.get("empleados") or {}
        plaza = data.get("plazas") or {}
        categoria = (plaza.get("categorias_puesto") or {}).get("nombre")
        sede = (plaza.get("sedes") or {}).get("nombre")
        fecha_fin_resuelta = self._resolver_fecha_fin_resumen(
            data.get("fecha_fin_estimada"),
            certificados,
        )

        return Incapacidad(
            id=int(data.get("id") or 0),
            empleado_id=int(data.get("empleado_id") or 0),
            plaza_id=int(data.get("plaza_id") or 0) or None,
            empresa_id=int(data.get("empresa_id") or 0),
            origen=self._coerce_origen(data.get("origen")),
            tipo=self._coerce_tipo(data.get("tipo")),
            fecha_inicio=self._coerce_date(data.get("fecha_inicio")),
            fecha_fin_estimada=fecha_fin_resuelta,
            fecha_fin_real=self._coerce_date(data.get("fecha_fin_real")),
            estatus=self._resolver_estatus_vigente(data.get("estatus"), fecha_fin_resuelta),
            porcentaje_pago=Decimal(str(data.get("porcentaje_pago") or "100")),
            requiere_cobertura=bool(data.get("requiere_cobertura")),
            notas=data.get("notas"),
            registrado_por=data.get("registrado_por"),
            fecha_creacion=data.get("fecha_creacion"),
            fecha_actualizacion=data.get("fecha_actualizacion"),
            certificados=certificados,
            empleado_nombre=self._construir_nombre_empleado(empleado),
            plaza_categoria=str(categoria or "") or None,
            plaza_sede=str(sede or "") or None,
        )

    def _mapear_resumen(self, data: dict) -> IncapacidadResumen:
        certificados = self._mapear_certificados(data.get("certificados_incapacidad") or [], data.get("id"))
        empleado = data.get("empleados") or {}
        plaza = data.get("plazas") or {}
        fecha_fin_resuelta = self._resolver_fecha_fin_resumen(
            data.get("fecha_fin_estimada"),
            certificados,
        )
        return IncapacidadResumen(
            id=int(data.get("id") or 0),
            empleado_id=int(data.get("empleado_id") or 0),
            empleado_uuid=empleado.get("uuid"),
            empleado_clave=str(empleado.get("clave") or ""),
            empleado_nombre=self._construir_nombre_empleado(data.get("empleados") or {}),
            tipo=self._coerce_tipo(data.get("tipo")),
            origen=self._coerce_origen(data.get("origen")),
            fecha_inicio=self._coerce_date(data.get("fecha_inicio")),
            fecha_fin_estimada=fecha_fin_resuelta,
            estatus=self._resolver_estatus_vigente(data.get("estatus"), fecha_fin_resuelta),
            dias_certificados=sum(cert.dias_certificado for cert in certificados),
            total_certificados=len(certificados),
            requiere_cobertura=bool(data.get("requiere_cobertura")),
            plaza_id=int(data.get("plaza_id") or 0) or None,
            contrato_id=int(plaza.get("contrato_id") or 0) or None,
            ultimo_folio_imss=self._resolver_ultimo_folio(certificados),
            plaza_categoria=(plaza.get("categorias_puesto") or {}).get("nombre"),
            plaza_sede=(plaza.get("sedes") or {}).get("nombre"),
        )

    def _mapear_certificados(
        self,
        certificados: list[dict],
        incapacidad_id: object,
    ) -> list[CertificadoIncapacidad]:
        incapacidad_id_int = int(incapacidad_id or 0)
        items = [
            CertificadoIncapacidad(
                id=int(item.get("id") or 0) or None,
                incapacidad_id=incapacidad_id_int,
                folio_imss=item.get("folio_imss"),
                fecha_inicio=self._coerce_date(item.get("fecha_inicio")),
                fecha_fin=self._coerce_date(item.get("fecha_fin")),
                dias_certificado=int(item.get("dias_certificado") or 0),
                tipo_certificado=self._coerce_tipo_certificado(item.get("tipo_certificado")),
                archivo_id=int(item.get("archivo_id") or 0) or None,
                fecha_creacion=item.get("fecha_creacion"),
                fecha_actualizacion=item.get("fecha_actualizacion"),
            )
            for item in certificados
        ]
        items.sort(key=lambda cert: (cert.fecha_fin, cert.fecha_inicio))
        return items

    def _resolver_estatus_vigente(
        self,
        estatus: object,
        fecha_fin: Optional[date],
    ) -> EstatusIncapacidad:
        try:
            actual = (
                estatus
                if isinstance(estatus, EstatusIncapacidad)
                else EstatusIncapacidad(str(estatus or "").upper())
            )
        except ValueError:
            actual = EstatusIncapacidad.ACTIVA

        if actual == EstatusIncapacidad.CERRADA:
            return actual
        if fecha_fin is not None and fecha_fin < date.today():
            return EstatusIncapacidad.VENCIDA
        return actual if actual != EstatusIncapacidad.VENCIDA else EstatusIncapacidad.VENCIDA

    def _resolver_fecha_fin_resumen(
        self,
        fecha_fin_estimada: object,
        certificados: list[CertificadoIncapacidad],
    ) -> Optional[date]:
        if certificados:
            return max(cert.fecha_fin for cert in certificados)
        return self._coerce_date(fecha_fin_estimada)

    def _resolver_fecha_fin_certificado(
        self,
        fecha_inicio: date,
        fecha_fin: Optional[date],
        dias_certificado: Optional[int],
    ) -> date:
        if fecha_fin is not None:
            return fecha_fin
        if dias_certificado is not None and int(dias_certificado) > 0:
            return fecha_inicio + timedelta(days=int(dias_certificado) - 1)
        return fecha_inicio

    def _resolver_dias_certificado(
        self,
        fecha_inicio: date,
        fecha_fin: date,
        dias_certificado: Optional[int],
    ) -> int:
        if dias_certificado is not None and int(dias_certificado) > 0:
            return int(dias_certificado)
        return (fecha_fin - fecha_inicio).days + 1

    def _normalizar_porcentaje(self, datos: IncapacidadCreate) -> Decimal:
        origen = self._coerce_origen(datos.origen)
        if origen == OrigenIncapacidad.FORMAL:
            return Decimal("100.00")
        return Decimal(str(datos.porcentaje_pago or "100"))

    def _construir_motivo_operativo(
        self,
        *,
        origen: OrigenIncapacidad,
        tipo: TipoIncapacidad,
        folio_imss: Optional[str],
    ) -> str:
        if origen == OrigenIncapacidad.POR_ACUERDO:
            return "Incapacidad por acuerdo registrada por RH"
        if folio_imss:
            return f"Incapacidad {tipo.descripcion.lower()} (folio IMSS: {folio_imss})"
        return f"Incapacidad {tipo.descripcion.lower()} registrada por RH"

    def _construir_nombre_empleado(self, empleado: dict) -> str:
        return " ".join(
            part
            for part in [
                str(empleado.get("nombre") or "").strip(),
                str(empleado.get("apellido_paterno") or "").strip(),
                str(empleado.get("apellido_materno") or "").strip(),
            ]
            if part
        ).strip()

    def _iterar_fechas(self, fecha_inicio: date, fecha_fin: date) -> Iterable[date]:
        total_dias = (fecha_fin - fecha_inicio).days
        for offset in range(max(total_dias, 0) + 1):
            yield fecha_inicio + timedelta(days=offset)

    def _coerce_date(self, value: object) -> Optional[date]:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))

    def _coerce_tipo(self, value: TipoIncapacidad | str) -> TipoIncapacidad:
        if isinstance(value, TipoIncapacidad):
            return value
        raw = getattr(value, "value", value)
        return TipoIncapacidad(str(raw or "").upper())

    def _coerce_origen(self, value: OrigenIncapacidad | str) -> OrigenIncapacidad:
        if isinstance(value, OrigenIncapacidad):
            return value
        raw = getattr(value, "value", value)
        return OrigenIncapacidad(str(raw or "").upper())

    def _coerce_tipo_certificado(self, value: TipoCertificado | str | None) -> TipoCertificado:
        if isinstance(value, TipoCertificado):
            return value
        raw = getattr(value, "value", value)
        if raw in (None, ""):
            return TipoCertificado.INICIAL
        return TipoCertificado(str(raw).upper())

    @staticmethod
    def _enum_value(value) -> str:
        return getattr(value, "value", value)

    @staticmethod
    def _resolver_ultimo_folio(certificados: list[CertificadoIncapacidad]) -> Optional[str]:
        for certificado in sorted(
            certificados,
            key=lambda cert: (cert.fecha_fin, cert.fecha_inicio),
            reverse=True,
        ):
            folio = str(certificado.folio_imss or "").strip()
            if folio:
                return folio
        return None


incapacidad_service = IncapacidadService()
