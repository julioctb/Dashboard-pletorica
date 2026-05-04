"""Repositorio de Empresas usando BaseRepository como contrato CRUD canónico."""

from typing import List, Optional

from app.domain.models import (
    Empresa,
    EmpresaResumen,
    EstatusEmpresa,
)
from app.core.exceptions import DuplicateError, DatabaseError
from app.domain.repositories.base_repository import BaseRepository
from app.domain.repositories.shared import (
    apply_eq_filters,
    apply_order,
    apply_pagination,
    build_ilike_or,
)

class SupabaseEmpresaRepository(BaseRepository[Empresa]):
    """Implementación del repositorio de empresas usando Supabase."""

    tabla = "empresas"
    entidad_class = Empresa
    entidad_nombre = "Empresa"

    def __init__(self, db_manager=None):
        super().__init__(db_manager)

    async def obtener_por_id(self, empresa_id: int) -> Empresa:
        return await super().obtener_por_id(empresa_id)

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Empresa]:
        estatus_filtro = None if incluir_inactivas else EstatusEmpresa.ACTIVO.value
        return await self._ejecutar_query(
            "obtener empresas",
            lambda: self._query_todos(
                limite or 100,
                offset,
                "fecha_creacion",
                True,
                {"estatus": estatus_filtro},
            ),
        )

    async def buscar_por_texto(self, termino: str, limite: int = 10) -> List[Empresa]:
        """
        Busca empresas por nombre comercial o razon social.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self._ejecutar_query(
            "buscar empresas",
            lambda: self._query_buscar_por_texto(termino, limite),
        )

    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        tipo_empresa: Optional[str] = None,
        estatus: Optional[str] = None,
        incluir_inactivas: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[Empresa]:
        return await self._ejecutar_query(
            "buscar empresas con filtros",
            lambda: self._query_buscar_con_filtros(
                texto=texto,
                tipo_empresa=tipo_empresa,
                estatus=estatus,
                incluir_inactivas=incluir_inactivas,
                limite=limite,
                offset=offset,
            ),
        )

    async def crear(self, empresa: Empresa) -> Empresa:
        if await self.existe_rfc(empresa.rfc):
            raise DuplicateError(
                f"RFC {empresa.rfc} ya existe",
                field="rfc",
                value=empresa.rfc,
            )
        return await super().crear(empresa)

    async def actualizar(self, empresa: Empresa) -> Empresa:
        return await super().actualizar_entidad(empresa)

    async def eliminar(self, empresa_id: int) -> bool:
        return await super().eliminar(empresa_id)

    async def existe_rfc(self, rfc: str, excluir_id: Optional[int] = None) -> bool:
        return await self.existe_campo("rfc", rfc.upper(), excluir_id)

    async def existe_codigo_corto(self, codigo: str) -> bool:
        return await self.existe_campo("codigo_corto", codigo.upper())

    def _insertar(self, entidad: Empresa) -> Empresa:
        datos = entidad.model_dump(
            mode="json",
            exclude={"id", "fecha_creacion", "fecha_actualizacion"},
        )
        result = self.supabase.table(self.tabla).insert(datos).execute()
        if not result.data:
            raise DatabaseError("No se pudo crear la empresa (sin respuesta de BD)")
        return self.entidad_class(**result.data[0])

    def _delete(self, id: int) -> bool:
        result = self.supabase.table(self.tabla).update({"estatus": "INACTIVO"}).eq(
            "id",
            id,
        ).execute()
        return bool(result.data)

    def _query_buscar_por_texto(self, termino: str, limite: int) -> List[Empresa]:
        or_clause = build_ilike_or(termino, ["nombre_comercial", "razon_social"])
        query = self.supabase.table(self.tabla).select("*").or_(or_clause).limit(limite)
        result = query.execute()
        return [self.entidad_class(**data) for data in result.data]

    def _query_buscar_con_filtros(
        self,
        *,
        texto: Optional[str],
        tipo_empresa: Optional[str],
        estatus: Optional[str],
        incluir_inactivas: bool,
        limite: int,
        offset: int,
    ) -> List[Empresa]:
        query = self.supabase.table(self.tabla).select("*")

        if texto and texto.strip():
            query = query.or_(build_ilike_or(texto, ["nombre_comercial", "razon_social"]))

        estatus_filtro = estatus if estatus else (
            None if incluir_inactivas else EstatusEmpresa.ACTIVO.value
        )
        query = apply_eq_filters(
            query,
            {
                "tipo_empresa": tipo_empresa,
                "estatus": estatus_filtro,
            },
        )
        query = apply_order(query, "fecha_creacion", desc=True)
        query = apply_pagination(query, limite if limite > 0 else None, offset)

        result = query.execute()
        return [self.entidad_class(**data) for data in result.data]
