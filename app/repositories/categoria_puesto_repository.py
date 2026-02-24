"""
Repositorio de Categorias de Puesto - Hereda de BaseRepository.

Metodos heredados de BaseRepository:
- obtener_por_id, crear, actualizar_entidad, eliminar, existe, existe_campo

Metodos custom:
- obtener_por_tipo_servicio, obtener_todas, buscar, existe_clave_en_tipo
"""
from typing import List, Optional

from app.entities.categoria_puesto import CategoriaPuesto
from app.core.exceptions import DuplicateError
from app.repositories.base_repository import BaseRepository


class SupabaseCategoriaPuestoRepository(BaseRepository[CategoriaPuesto]):
    """Repositorio de categorias de puesto usando Supabase."""

    tabla = 'categorias_puesto'
    entidad_class = CategoriaPuesto
    entidad_nombre = 'Categoria de puesto'

    # =========================================================================
    # QUERIES CUSTOM
    # =========================================================================

    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivas: bool = False
    ) -> List[CategoriaPuesto]:
        """Obtiene todas las categorias de un tipo de servicio."""
        return await self._ejecutar_query(
            "obtener categorias por tipo",
            lambda: self._query_por_tipo(tipo_servicio_id, incluir_inactivas),
            return_list=True
        )

    def _query_por_tipo(self, tipo_servicio_id, incluir_inactivas):
        query = self.supabase.table(self.tabla).select('*').eq('tipo_servicio_id', tipo_servicio_id)
        query = self._aplicar_filtro_estatus(query, incluir_inactivas)
        query = query.order('orden', desc=False).order('nombre', desc=False)
        result = query.execute()
        return [CategoriaPuesto(**data) for data in result.data]

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[CategoriaPuesto]:
        """Obtiene todas las categorias con paginacion."""
        return await self._ejecutar_query(
            "obtener todas las categorias",
            lambda: self._query_obtener_todas(incluir_inactivas, limite, offset),
            return_list=True
        )

    def _query_obtener_todas(self, incluir_inactivas, limite, offset):
        query = self.supabase.table(self.tabla).select('*')
        query = self._aplicar_filtro_estatus(query, incluir_inactivas)
        query = query.order('tipo_servicio_id', desc=False).order('orden', desc=False)
        if limite is None:
            limite = 100
        query = query.range(offset, offset + limite - 1)
        result = query.execute()
        return [CategoriaPuesto(**data) for data in result.data]

    async def buscar(
        self,
        termino: str,
        tipo_servicio_id: Optional[int] = None,
        limite: int = 10
    ) -> List[CategoriaPuesto]:
        """Busca categorias por nombre o clave."""
        return await self._ejecutar_query(
            "buscar categorias",
            lambda: self._query_buscar(termino, tipo_servicio_id, limite),
            return_list=True
        )

    def _query_buscar(self, termino, tipo_servicio_id, limite):
        termino_upper = termino.strip().upper()
        query = self.supabase.table(self.tabla)\
            .select('*')\
            .eq('estatus', 'ACTIVO')\
            .or_(f"nombre.ilike.%{termino_upper}%,clave.ilike.%{termino_upper}%")
        if tipo_servicio_id:
            query = query.eq('tipo_servicio_id', tipo_servicio_id)
        query = query.limit(limite)
        result = query.execute()
        return [CategoriaPuesto(**data) for data in result.data]

    # =========================================================================
    # OVERRIDES
    # =========================================================================

    async def crear(self, entidad: CategoriaPuesto) -> CategoriaPuesto:
        """Crea categoria verificando unicidad de clave en el tipo de servicio."""
        if await self.existe_clave_en_tipo(entidad.tipo_servicio_id, entidad.clave):
            raise DuplicateError(
                f"La clave '{entidad.clave}' ya existe en este tipo de servicio",
                field="clave",
                value=entidad.clave
            )
        return await super().crear(entidad)

    def _insertar(self, entidad: CategoriaPuesto) -> CategoriaPuesto:
        """Override: excluir fecha_actualizacion tambien."""
        datos = entidad.model_dump(exclude={'id', 'fecha_creacion', 'fecha_actualizacion'})
        result = self.supabase.table(self.tabla).insert(datos).execute()
        if not result.data:
            return None
        return CategoriaPuesto(**result.data[0])

    def _delete(self, id: int) -> bool:
        """Soft delete: marca como INACTIVO en lugar de borrar."""
        result = self.supabase.table(self.tabla).update(
            {'estatus': 'INACTIVO'}
        ).eq('id', id).execute()
        return bool(result.data)

    # =========================================================================
    # VERIFICACIONES
    # =========================================================================

    async def existe_clave_en_tipo(
        self,
        tipo_servicio_id: int,
        clave: str,
        excluir_id: Optional[int] = None
    ) -> bool:
        """Verifica si una clave ya existe en el tipo de servicio."""
        return await self._ejecutar_query(
            "verificar clave en tipo",
            lambda: self._query_existe_clave_en_tipo(tipo_servicio_id, clave, excluir_id),
        )

    def _query_existe_clave_en_tipo(self, tipo_servicio_id, clave, excluir_id):
        query = self.supabase.table(self.tabla)\
            .select('id')\
            .eq('tipo_servicio_id', tipo_servicio_id)\
            .eq('clave', clave.upper())
        if excluir_id:
            query = query.neq('id', excluir_id)
        result = query.execute()
        return len(result.data) > 0
