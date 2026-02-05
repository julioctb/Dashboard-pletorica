"""
Servicio de aplicacion para gestion de empresas.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: RFC duplicado)
- DatabaseError: Errores de conexion o infraestructura
- Las excepciones se propagan hacia arriba al State
"""
import logging
from typing import List, Optional

from app.entities import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
    TipoEmpresa,
)
from app.repositories import SupabaseEmpresaRepository
from app.core.exceptions import DatabaseError
from app.core.utils import generar_candidatos_codigo

logger = logging.getLogger(__name__)


class EmpresaService:
    """
    Servicio de aplicacion para empresas.
    Orquesta las operaciones de negocio delegando acceso a datos al repositorio.
    """

    def __init__(self):
        self.repository = SupabaseEmpresaRepository()

    # ==========================================
    # OPERACIONES CRUD
    # ==========================================

    async def obtener_por_id(self, empresa_id: int) -> Empresa:
        """
        Obtiene una empresa por su ID.

        Raises:
            NotFoundError: Si la empresa no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(empresa_id)

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[Empresa]:
        """
        Obtiene todas las empresas con paginacion.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todas(incluir_inactivas, limite, offset)

    async def buscar_por_nombre(self, termino: str, limite: int = 10) -> List[Empresa]:
        """
        Busca empresas por nombre comercial o razon social.

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino) < 2:
            return []

        return await self.repository.buscar_por_texto(termino, limite)

    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        tipo_empresa: Optional[str] = None,
        estatus: Optional[str] = None,
        incluir_inactivas: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> List[EmpresaResumen]:
        """
        Busca empresas con filtros combinados.

        Raises:
            DatabaseError: Si hay error de BD
        """
        if texto and len(texto.strip()) < 2:
            texto = None

        empresas = await self.repository.buscar_con_filtros(
            texto=texto,
            tipo_empresa=tipo_empresa,
            estatus=estatus,
            incluir_inactivas=incluir_inactivas,
            limite=limite,
            offset=offset,
        )

        return [EmpresaResumen.from_empresa(empresa) for empresa in empresas]

    async def crear(self, empresa_create: EmpresaCreate) -> Empresa:
        """
        Crea una nueva empresa con codigo corto autogenerado.

        Raises:
            DuplicateError: Si el RFC ya existe
            ValidationError: Si los datos no son validos
            DatabaseError: Si hay error de BD
        """
        codigo_corto = await self._generar_codigo_unico(empresa_create.nombre_comercial)

        datos = empresa_create.model_dump()
        datos['codigo_corto'] = codigo_corto
        empresa = Empresa(**datos)

        if empresa.tipo_empresa == TipoEmpresa.NOMINA:
            if not empresa.email:
                logger.warning("Empresa de nomina creada sin email")

        return await self.repository.crear(empresa)

    async def _generar_codigo_unico(self, nombre_comercial: str) -> str:
        """
        Genera un codigo corto unico para la empresa.

        Raises:
            DatabaseError: Si no se puede generar un codigo unico
        """
        candidatos = generar_candidatos_codigo(nombre_comercial)

        for codigo in candidatos:
            if not await self.repository.existe_codigo_corto(codigo):
                logger.info(f"Codigo '{codigo}' asignado para '{nombre_comercial}'")
                return codigo

        raise DatabaseError(
            f"No se pudo generar codigo unico para '{nombre_comercial}' "
            f"despues de {len(candidatos)} intentos"
        )

    async def actualizar(self, empresa_id: int, empresa_update: EmpresaUpdate) -> Empresa:
        """
        Actualiza una empresa existente.

        Raises:
            NotFoundError: Si la empresa no existe
            ValidationError: Si los datos no son validos
            DatabaseError: Si hay error de BD
        """
        empresa_actual = await self.repository.obtener_por_id(empresa_id)

        datos_actualizados = empresa_actual.model_dump()
        for campo, valor in empresa_update.model_dump(exclude_unset=True).items():
            if valor is not None:
                datos_actualizados[campo] = valor

        empresa_modificada = Empresa(**datos_actualizados)

        return await self.repository.actualizar(empresa_modificada)

    async def cambiar_estatus(self, empresa_id: int, nuevo_estatus) -> bool:
        """
        Cambia el estatus de una empresa.

        Raises:
            NotFoundError: Si la empresa no existe
            DatabaseError: Si hay error de BD
        """
        empresa = await self.repository.obtener_por_id(empresa_id)

        if empresa.estatus == nuevo_estatus:
            logger.warning(f"Empresa {empresa_id} ya tiene estatus {nuevo_estatus.value}")
            return True

        empresa.estatus = nuevo_estatus

        await self.repository.actualizar(empresa)
        return True

    async def eliminar(self, empresa_id: int) -> bool:
        """
        Elimina (inactiva) una empresa.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.eliminar(empresa_id)


# Instancia global del servicio (singleton)
empresa_service = EmpresaService()
