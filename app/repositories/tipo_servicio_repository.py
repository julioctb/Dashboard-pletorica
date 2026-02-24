"""
Repositorio de Tipos de Servicio - Hereda de BaseRepository.

Metodos heredados de BaseRepository:
- obtener_por_id, obtener_todos, crear, actualizar, actualizar_entidad,
  eliminar, contar, buscar_por_texto, existe, existe_campo

Metodos custom:
- obtener_por_clave, obtener_todas, buscar_por_texto (override),
  existe_clave, eliminar (soft delete)
"""
from typing import List, Optional

from app.entities import TipoServicio
from app.core.enums import Estatus
from app.core.exceptions import DuplicateError
from app.repositories.base_repository import BaseRepository


class SupabaseTipoServicioRepository(BaseRepository[TipoServicio]):
    """Repositorio de tipos de servicio usando Supabase."""

    tabla = 'tipos_servicio'
    entidad_class = TipoServicio
    entidad_nombre = 'Tipo de servicio'

    # =========================================================================
    # QUERIES CUSTOM
    # =========================================================================

    async def obtener_por_clave(self, clave: str) -> Optional[TipoServicio]:
        """Obtiene un tipo de servicio por su clave."""
        result = await self._ejecutar_query(
            "obtener tipo por clave",
            lambda: self._query_por_clave(clave),
        )
        return result

    def _query_por_clave(self, clave: str) -> Optional[TipoServicio]:
        result = self.supabase.table(self.tabla).select('*').eq('clave', clave.upper()).execute()
        if not result.data:
            return None
        return TipoServicio(**result.data[0])

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[TipoServicio]:
        """Obtiene todos los tipos con filtro de estatus."""
        return await self._ejecutar_query(
            "obtener todos los tipos de servicio",
            lambda: self._query_obtener_todas(incluir_inactivas, limite, offset),
            return_list=True
        )

    def _query_obtener_todas(self, incluir_inactivas, limite, offset):
        query = self.supabase.table(self.tabla).select('*')
        query = self._aplicar_filtro_estatus(query, incluir_inactivas)
        query = query.order('nombre', desc=False)
        if limite is None:
            limite = 100
        query = query.range(offset, offset + limite - 1)
        result = query.execute()
        return [TipoServicio(**data) for data in result.data]

    async def buscar_por_texto(self, termino: str, limite: int = 10, offset: int = 0) -> List[TipoServicio]:
        """Busca tipos de servicio por nombre o clave."""
        return await self._ejecutar_query(
            "buscar tipos de servicio",
            lambda: self._query_buscar_tipos(termino, limite, offset),
            return_list=True
        )

    def _query_buscar_tipos(self, termino, limite, offset):
        termino_upper = termino.upper()
        result = self.supabase.table(self.tabla)\
            .select('*')\
            .eq('estatus', Estatus.ACTIVO.value)\
            .or_(f"nombre.ilike.%{termino_upper}%,clave.ilike.%{termino_upper}%")\
            .range(offset, offset + limite - 1)\
            .execute()
        return [TipoServicio(**data) for data in result.data]

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """Cuenta el total de tipos de servicio."""
        filtros = None if incluir_inactivas else {'estatus': Estatus.ACTIVO.value}
        return await super().contar(filtros=filtros)

    # =========================================================================
    # OVERRIDES
    # =========================================================================

    async def crear(self, entidad: TipoServicio) -> TipoServicio:
        """Crea tipo verificando unicidad de clave antes de insertar."""
        if await self.existe_clave(entidad.clave):
            raise DuplicateError(
                f"La clave '{entidad.clave}' ya existe",
                field="clave",
                value=entidad.clave
            )
        return await super().crear(entidad)

    def _insertar(self, entidad: TipoServicio) -> TipoServicio:
        """Override: excluir fecha_actualizacion tambien."""
        datos = entidad.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
        result = self.supabase.table(self.tabla).insert(datos).execute()
        if not result.data:
            return None
        return TipoServicio(**result.data[0])

    def _delete(self, id: int) -> bool:
        """Soft delete: marca como INACTIVO en lugar de borrar."""
        result = self.supabase.table(self.tabla).update(
            {'estatus': 'INACTIVO'}
        ).eq('id', id).execute()
        return bool(result.data)

    # =========================================================================
    # VERIFICACIONES
    # =========================================================================

    async def existe_clave(self, clave: str, excluir_id: Optional[int] = None) -> bool:
        """Verifica si una clave ya existe."""
        return await self.existe_campo('clave', clave.upper(), excluir_id)
