"""
Servicio de aplicacion para gestion de Categorias de Puesto.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (clave duplicada en el mismo tipo)
- DatabaseError: Errores de conexion o infraestructura
- BusinessRuleError: Violaciones de reglas de negocio
"""
import logging
from decimal import Decimal
from typing import List, Optional

from app.domain.models.categoria_puesto import (
    CategoriaPuesto,
    CategoriaPuestoCreate,
    CategoriaPuestoUpdate,
)
from app.domain.enums import Estatus, OrigenTipoServicio
from app.domain.repositories import (
    SupabaseCategoriaPuestoRepository,
    SupabaseContratoCategoriaRepository,
    SupabasePlazaRepository,
)
from app.core.exceptions import DuplicateError, BusinessRuleError
from app.core.text_utils import (
    generar_candidatos_clave_categoria_puesto,
    normalizar_mayusculas,
)
from app.domain.services.base_service import BaseService

logger = logging.getLogger(__name__)


class CategoriaPuestoService(BaseService):
    """
    Servicio de aplicacion para categorias de puesto.
    Orquesta las operaciones de negocio delegando acceso a datos al repositorio.
    """

    def __init__(self):
        self.repository = SupabaseCategoriaPuestoRepository()
        self.contrato_categoria_repository = SupabaseContratoCategoriaRepository()
        self.plaza_repository = SupabasePlazaRepository()

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, categoria_id: int) -> CategoriaPuesto:
        """
        Obtiene una categoria por su ID.

        Raises:
            NotFoundError: Si la categoria no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(categoria_id)

    async def obtener_por_tipo_servicio(
        self,
        tipo_servicio_id: int,
        incluir_inactivas: bool = False
    ) -> List[CategoriaPuesto]:
        """
        Obtiene todas las categorias de un tipo de servicio.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_tipo_servicio(tipo_servicio_id, incluir_inactivas)

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[CategoriaPuesto]:
        """
        Obtiene todas las categorias con paginacion.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todas(incluir_inactivas, limite, offset)

    async def buscar(
        self,
        termino: str,
        tipo_servicio_id: Optional[int] = None,
        limite: int = 10
    ) -> List[CategoriaPuesto]:
        """
        Busca categorias por nombre o clave.

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino.strip()) < 2:
            return []

        return await self.repository.buscar(termino, tipo_servicio_id, limite)

    async def contar_contratos_por_categorias(self, categoria_ids: list[int]) -> dict[int, int]:
        """Obtiene en lote cuántos contratos usan cada categoría."""
        return await self.contrato_categoria_repository.contar_por_categorias(categoria_ids)

    async def contar_contratos_por_categoria(self, categoria_id: int) -> int:
        """Cuenta contratos donde la categoría está configurada."""
        return await self.contrato_categoria_repository.contar_por_categoria(categoria_id)

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, categoria_create: CategoriaPuestoCreate) -> CategoriaPuesto:
        """
        Crea una nueva categoria de puesto.

        Raises:
            DuplicateError: Si la clave ya existe en el tipo de servicio
            DatabaseError: Si hay error de BD
        """
        categoria = CategoriaPuesto(**categoria_create.model_dump())

        logger.info(
            f"Creando categoria: {categoria.clave} - {categoria.nombre} "
            f"(tipo_servicio_id={categoria.tipo_servicio_id})"
        )

        return await self.repository.crear(categoria)

    async def crear_portal_empresa(
        self,
        empresa_id: int,
        *,
        tipo_servicio_id: int,
        nombre: str,
        clave: str = "",
        salario_base_mensual: Decimal | None = None,
    ) -> CategoriaPuesto:
        """Crea una categoría dentro del catálogo de puestos de la empresa."""
        tipo = await self._obtener_y_validar_tipo_portal_empresa(tipo_servicio_id, empresa_id)
        clave_normalizada = await self._resolver_clave_portal_categoria(
            tipo_servicio_id=tipo_servicio_id,
            tipo_servicio_nombre=tipo.nombre,
            nombre_categoria=nombre,
            clave=clave,
        )

        categoria_create = CategoriaPuestoCreate(
            tipo_servicio_id=tipo_servicio_id,
            clave=clave_normalizada,
            nombre=normalizar_mayusculas(nombre),
            orden=await self._siguiente_orden_tipo_servicio(tipo_servicio_id),
            salario_base_mensual=salario_base_mensual,
            estatus=Estatus.ACTIVO,
        )
        return await self.crear(categoria_create)

    async def actualizar(
        self,
        categoria_id: int,
        categoria_update: CategoriaPuestoUpdate
    ) -> CategoriaPuesto:
        """
        Actualiza una categoria existente.

        Raises:
            NotFoundError: Si la categoria no existe
            DuplicateError: Si la nueva clave ya existe en el tipo de servicio
            DatabaseError: Si hay error de BD
        """
        categoria_actual = await self._merge_y_actualizar(
            categoria_id, categoria_update, self.repository
        )

        logger.info(f"Actualizando categoria ID {categoria_id}")

        # Verificar clave duplicada (excluyendo registro actual)
        if await self.repository.existe_clave_en_tipo(
            categoria_actual.tipo_servicio_id,
            categoria_actual.clave,
            excluir_id=categoria_actual.id
        ):
            raise DuplicateError(
                f"La clave '{categoria_actual.clave}' ya existe en este tipo de servicio",
                field="clave",
                value=categoria_actual.clave
            )

        return await self.repository.actualizar_entidad(categoria_actual)

    async def actualizar_portal_empresa(
        self,
        categoria_id: int,
        empresa_id: int,
        *,
        nombre: str,
        clave: str = "",
        salario_base_mensual: Decimal | None = None,
    ) -> CategoriaPuesto:
        """Actualiza una categoría del catálogo propio de la empresa."""
        categoria_actual = await self.obtener_por_id(categoria_id)
        tipo = await self._obtener_y_validar_tipo_portal_empresa(
            categoria_actual.tipo_servicio_id,
            empresa_id,
        )
        clave_normalizada = await self._resolver_clave_portal_categoria(
            tipo_servicio_id=categoria_actual.tipo_servicio_id,
            tipo_servicio_nombre=tipo.nombre,
            nombre_categoria=nombre,
            clave=clave,
            excluir_id=categoria_actual.id,
        )

        return await self.actualizar(
            categoria_id,
            CategoriaPuestoUpdate(
                nombre=normalizar_mayusculas(nombre),
                clave=clave_normalizada,
                salario_base_mensual=salario_base_mensual,
            ),
        )

    async def eliminar(self, categoria_id: int) -> bool:
        """
        Elimina (desactiva) una categoria.

        Raises:
            NotFoundError: Si la categoria no existe
            BusinessRuleError: Si tiene empleados asociados (futuro)
            DatabaseError: Si hay error de BD
        """
        categoria = await self.repository.obtener_por_id(categoria_id)

        await self._validar_puede_eliminar(categoria)

        logger.info(f"Eliminando (desactivando) categoria: {categoria.clave}")

        return await self.repository.eliminar(categoria_id)

    async def desactivar_portal_empresa(self, categoria_id: int, empresa_id: int) -> bool:
        """Desactiva una categoría del catálogo de empresa con reglas portal."""
        categoria = await self.obtener_por_id(categoria_id)
        await self._obtener_y_validar_tipo_portal_empresa(categoria.tipo_servicio_id, empresa_id)
        await self._validar_puede_desactivar_portal(categoria)
        return await self.repository.eliminar(categoria_id)

    async def puede_desactivar_portal_empresa(self, categoria_id: int, empresa_id: int) -> bool:
        """Indica si una categoría puede desactivarse sin afectar contratos operativos."""
        categoria = await self.obtener_por_id(categoria_id)
        await self._obtener_y_validar_tipo_portal_empresa(categoria.tipo_servicio_id, empresa_id)
        plazas_operativas = await self.plaza_repository.contar_activas_en_contratos_operativos_por_categoria(
            int(categoria.id or 0)
        )
        return plazas_operativas <= 0

    async def activar(self, categoria_id: int) -> CategoriaPuesto:
        """
        Activa una categoria que estaba inactiva.

        Raises:
            NotFoundError: Si la categoria no existe
            BusinessRuleError: Si ya esta activa
            DatabaseError: Si hay error de BD
        """
        logger.info(f"Activando categoria ID {categoria_id}")
        return await self._cambiar_estatus(
            categoria_id, Estatus.ACTIVO, self.repository, "La categoria"
        )

    async def activar_portal_empresa(self, categoria_id: int, empresa_id: int) -> CategoriaPuesto:
        """Reactiva una categoría de la empresa validando ownership."""
        categoria = await self.obtener_por_id(categoria_id)
        await self._obtener_y_validar_tipo_portal_empresa(categoria.tipo_servicio_id, empresa_id)
        return await self.activar(categoria_id)

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_puede_eliminar(self, categoria: CategoriaPuesto) -> None:
        """
        Valida si una categoria puede ser eliminada.
        """
        from app.domain.repositories.plaza_repository import SupabasePlazaRepository

        plazas_asociadas = await SupabasePlazaRepository().contar_por_categoria_puesto(
            categoria.id,
            incluir_canceladas=False,
        )
        if plazas_asociadas > 0:
            raise BusinessRuleError(
                f"No se puede eliminar '{categoria.nombre}' porque está asociada a "
                f"{plazas_asociadas} plaza(s)"
            )

    async def _validar_puede_desactivar_portal(self, categoria: CategoriaPuesto) -> None:
        """Bloquea la desactivación si la categoría tiene plazas activas en contratos operativos."""
        plazas_operativas = await self.plaza_repository.contar_activas_en_contratos_operativos_por_categoria(
            int(categoria.id or 0)
        )
        if plazas_operativas > 0:
            raise BusinessRuleError(
                f"No se puede desactivar '{categoria.nombre}' porque tiene "
                f"{plazas_operativas} plaza(s) en contratos activos"
            )

    async def _obtener_y_validar_tipo_portal_empresa(self, tipo_servicio_id: int, empresa_id: int):
        from app.domain.services.tipo_servicio_service import tipo_servicio_service

        tipo = await tipo_servicio_service.obtener_por_id(tipo_servicio_id)
        if int(getattr(tipo, "empresa_id", 0) or 0) != int(empresa_id or 0):
            raise BusinessRuleError("El tipo de servicio no pertenece a la empresa activa")
        raw_origen = getattr(getattr(tipo, "origen", None), "value", getattr(tipo, "origen", None))
        if str(raw_origen or "").upper() != OrigenTipoServicio.EMPRESA.value:
            raise BusinessRuleError("El tipo de servicio es de solo lectura para la empresa")
        return tipo

    async def _siguiente_orden_tipo_servicio(self, tipo_servicio_id: int) -> int:
        categorias = await self.obtener_por_tipo_servicio(tipo_servicio_id, incluir_inactivas=True)
        if not categorias:
            return 0
        return max(int(getattr(categoria, "orden", 0) or 0) for categoria in categorias) + 1

    async def _resolver_clave_portal_categoria(
        self,
        *,
        tipo_servicio_id: int,
        tipo_servicio_nombre: str,
        nombre_categoria: str,
        clave: str,
        excluir_id: Optional[int] = None,
    ) -> str:
        clave_normalizada = normalizar_mayusculas(clave)
        if clave_normalizada:
            return clave_normalizada

        candidatos = generar_candidatos_clave_categoria_puesto(
            tipo_servicio_nombre,
            nombre_categoria,
        )
        for candidato in candidatos:
            if not await self.repository.existe_clave_en_tipo(
                tipo_servicio_id,
                candidato,
                excluir_id=excluir_id,
            ):
                return candidato

        raise BusinessRuleError(
            "No fue posible generar una clave única para la categoría"
        )

    async def existe_clave_en_tipo(
        self,
        tipo_servicio_id: int,
        clave: str,
        excluir_id: Optional[int] = None
    ) -> bool:
        """
        Verifica si una clave ya existe en el tipo de servicio.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.existe_clave_en_tipo(tipo_servicio_id, clave, excluir_id)


# ==========================================
# SINGLETON
# ==========================================

categoria_puesto_service = CategoriaPuestoService()
