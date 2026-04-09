"""State para la página principal de plazas (listado de contratos con resumen)."""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from decimal import Decimal

import reflex as rx

from app.core.text_utils import formatear_moneda, normalizar_mayusculas
from app.domain.enums import EstatusPlaza
from app.modules.application import contrato_service, plaza_service
from app.presentation.pages.backoffice.contratos.contrato_presentacion import (
    enriquecer_contrato_presentacion,
)
from app.presentation.pages.portal.state.portal_state import PortalState


_MESES_CORTOS_ES = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic",
}


class PlazasListadoState(PortalState):
    """Listado de contratos con resumen operativo de plazas."""

    _is_loading: bool = False
    _contratos: list[dict] = []
    _totales: dict = {}

    @rx.var
    def is_loading(self) -> bool:
        return self._is_loading

    @rx.var
    def contratos(self) -> list[dict]:
        return self._contratos

    @rx.var
    def total_contratos(self) -> int:
        return len(self._contratos)

    @rx.var
    def total_plazas(self) -> int:
        return sum(int(item.get("total_plazas") or 0) for item in self._contratos)

    @rx.var
    def total_ocupadas(self) -> int:
        return sum(int(item.get("ocupadas") or 0) for item in self._contratos)

    @rx.var
    def total_vacantes(self) -> int:
        return sum(int(item.get("vacantes") or 0) for item in self._contratos)

    @rx.var
    def cobertura_global(self) -> str:
        total = self.total_plazas
        if total <= 0:
            return "0%"
        return f"{int(round((self.total_ocupadas / total) * 100))}%"

    @rx.var
    def costo_mensual_total(self) -> str:
        monto_total = sum(
            Decimal(str(item.get("costo_mensual_raw") or 0))
            for item in self._contratos
        )
        return self._formatear_costo(monto_total)

    @rx.var
    def tiene_contratos(self) -> bool:
        return len(self._contratos) > 0

    async def cargar_contratos(self):
        """Carga contratos con resumen de cobertura de plazas."""
        resultado = await self.on_mount_portal()
        if resultado:
            self._is_loading = False
            yield resultado
            return

        if not self.mostrar_seccion_plazas_portal:
            yield rx.redirect("/portal")
            return

        self._is_loading = True
        yield

        try:
            empresa_id = self._get_empresa_id()
            if empresa_id <= 0:
                self._contratos = []
                self._totales = {}
                return

            contratos_raw = await contrato_service.obtener_por_empresa(
                empresa_id=empresa_id,
                incluir_inactivos=True,
            )
            contratos_presentacion = self._normalizar_contratos_con_personal(contratos_raw)
            contratos_ids = [
                int(item.get("id") or 0)
                for item in contratos_presentacion
                if int(item.get("id") or 0) > 0
            ]

            resumenes_plazas = await asyncio.gather(
                *[
                    plaza_service.obtener_resumen_de_contrato(contrato_id)
                    for contrato_id in contratos_ids
                ],
                return_exceptions=True,
            )

            contratos_listado: list[dict] = []
            for contrato, resumen in zip(contratos_presentacion, resumenes_plazas):
                plazas = [] if isinstance(resumen, Exception) else list(resumen or [])

                total_plazas = len(plazas)
                ocupadas = 0
                categorias: set[int] = set()
                sedes: set[int] = set()
                costo_mensual = Decimal("0")

                for plaza in plazas:
                    estatus = str(
                        getattr(getattr(plaza, "estatus", None), "value", getattr(plaza, "estatus", ""))
                        or ""
                    )
                    if estatus == EstatusPlaza.OCUPADA.value:
                        ocupadas += 1

                    categoria_id = int(getattr(plaza, "categoria_puesto_id", 0) or 0)
                    if categoria_id > 0:
                        categorias.add(categoria_id)

                    sede_id = int(getattr(plaza, "sede_id", 0) or 0)
                    if sede_id > 0:
                        sedes.add(sede_id)

                    costo_mensual += Decimal(str(getattr(plaza, "salario_mensual", 0) or 0))

                vacantes = max(total_plazas - ocupadas, 0)
                cobertura_pct = int(round((ocupadas / total_plazas) * 100)) if total_plazas > 0 else 0
                if cobertura_pct >= 80:
                    cobertura_nivel = "ALTA"
                elif cobertura_pct >= 50:
                    cobertura_nivel = "MEDIA"
                else:
                    cobertura_nivel = "BAJA"

                contratos_listado.append(
                    {
                        "id": int(contrato.get("id") or 0),
                        "codigo": normalizar_mayusculas(str(contrato.get("codigo") or "")),
                        "descripcion": str(contrato.get("descripcion_objeto_display") or ""),
                        "estatus": str(contrato.get("estatus") or ""),
                        "vigencia": self._formatear_vigencia(
                            contrato.get("fecha_inicio"),
                            contrato.get("fecha_fin"),
                        ),
                        "categorias": len(categorias),
                        "sedes": len(sedes),
                        "total_plazas": total_plazas,
                        "ocupadas": ocupadas,
                        "vacantes": vacantes,
                        "cobertura_pct": cobertura_pct,
                        "cobertura_nivel": cobertura_nivel,
                        "costo_mensual_raw": float(costo_mensual),
                        "costo_mensual_fmt": self._formatear_costo(costo_mensual),
                    }
                )

            self._contratos = contratos_listado
            self._totales = {
                "contratos": len(contratos_listado),
                "plazas": sum(int(item.get("total_plazas") or 0) for item in contratos_listado),
                "ocupadas": sum(int(item.get("ocupadas") or 0) for item in contratos_listado),
                "vacantes": sum(int(item.get("vacantes") or 0) for item in contratos_listado),
            }
        except Exception as exc:
            print(f"Error cargando contratos de plazas: {exc}")
            self._contratos = []
            self._totales = {}
        finally:
            self._is_loading = False

    def ir_a_plazas_contrato(self, contrato_id: int):
        """Navega a la vista de plazas de un contrato."""
        contrato_id_int = int(contrato_id or 0)
        if contrato_id_int <= 0:
            return rx.redirect("/portal/plazas")
        return rx.redirect(f"/portal/contratos/{contrato_id_int}/plazas")

    def _get_empresa_id(self) -> int:
        """Obtiene el empresa_id activo desde el contexto del portal."""
        return int(self.id_empresa_actual or 0)

    @staticmethod
    def _normalizar_fecha(value: object) -> date | None:
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()

        texto = str(value or "").strip()
        if not texto:
            return None

        candidatos = [texto]
        if "T" in texto:
            candidatos.append(texto.split("T", maxsplit=1)[0])
        if texto.endswith("Z"):
            candidatos.append(texto.replace("Z", "+00:00"))

        for candidato in candidatos:
            try:
                if len(candidato) <= 10:
                    return date.fromisoformat(candidato)
                return datetime.fromisoformat(candidato).date()
            except ValueError:
                continue

        return None

    @classmethod
    def _formatear_vigencia(cls, fecha_inicio: object, fecha_fin: object) -> str:
        inicio = cls._normalizar_fecha(fecha_inicio)
        fin = cls._normalizar_fecha(fecha_fin)

        if inicio and fin:
            return (
                f"{_MESES_CORTOS_ES.get(inicio.month, '')}"
                f"–{_MESES_CORTOS_ES.get(fin.month, '')} {fin.year}"
            )
        if inicio:
            return f"Desde {_MESES_CORTOS_ES.get(inicio.month, '')} {inicio.year}"
        if fin:
            return f"Hasta {_MESES_CORTOS_ES.get(fin.month, '')} {fin.year}"
        return "Sin vigencia"

    @staticmethod
    def _formatear_costo(monto: Decimal) -> str:
        if monto >= Decimal("1000000"):
            return f"${(monto / Decimal('1000000')):.1f}M"
        return formatear_moneda(str(monto))

    @classmethod
    def _normalizar_contratos_con_personal(cls, contratos: list) -> list[dict]:
        contratos_norm: list[dict] = []
        for contrato in contratos or []:
            contrato_dict = enriquecer_contrato_presentacion(contrato)
            if not bool(contrato_dict.get("tiene_personal")):
                continue
            contratos_norm.append(contrato_dict)

        contratos_norm.sort(
            key=lambda item: (
                cls._normalizar_fecha(item.get("fecha_inicio")) or date.min,
                int(item.get("id") or 0),
            ),
            reverse=True,
        )
        return contratos_norm
