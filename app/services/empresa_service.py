"""
Servicio de aplicación para gestión de empresas.
Consolidado y simplificado desde app/services/empresa_service.py

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio NO captura excepciones, las deja subir al State
- Logging de errores solo para debugging, NO para control de flujo
"""
import logging
from typing import List, Optional

from app.entities import (
    Empresa,
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResumen,
    TipoEmpresa,
    EstatusEmpresa,
)
from app.repositories import SupabaseEmpresaRepository
from app.core.exceptions import NotFoundError, DuplicateError, DatabaseError
from app.core.utils import generar_candidatos_codigo

logger = logging.getLogger(__name__)


class EmpresaService:
    """
    Servicio de aplicación para empresas.
    Orquesta las operaciones de negocio.
    """

    def __init__(self, repository=None):
        """
        Inicializa el servicio con un repository.

        Args:
            repository: Implementación del repository. Si es None, usa Supabase por defecto.
        """
        if repository is None:
            repository = SupabaseEmpresaRepository()
        self.repository = repository

    # ==========================================
    # OPERACIONES CRUD
    # ==========================================

    async def obtener_por_id(self, empresa_id: int) -> Empresa:
        """
        Obtiene una empresa por su ID.

        Args:
            empresa_id: ID de la empresa

        Returns:
            Empresa encontrada

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
        Obtiene todas las empresas con paginación.

        Args:
            incluir_inactivas: Si True, incluye empresas inactivas
            limite: Número máximo de resultados (None = 100 por defecto)
            offset: Número de registros a saltar

        Returns:
            Lista de empresas (vacía si no hay resultados)

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todas(incluir_inactivas, limite, offset)

    async def obtener_resumen_empresas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = 50,
        offset: int = 0
    ) -> List[EmpresaResumen]:
        """
        Obtiene un resumen de todas las empresas de forma eficiente con paginación.

        Args:
            incluir_inactivas: Si True, incluye empresas inactivas
            limite: Número máximo de resultados (default 50 para UI responsivo)
            offset: Número de registros a saltar

        Returns:
            Lista de resúmenes de empresas

        Raises:
            DatabaseError: Si hay error de BD
        """
        empresas = await self.repository.obtener_todas(incluir_inactivas, limite, offset)
        # Usar list comprehension con factory method (más eficiente que loop)
        return [EmpresaResumen.from_empresa(empresa) for empresa in empresas]

    async def buscar_por_nombre(self, termino: str, limite: int = 10) -> List[Empresa]:
        """
        Busca empresas por nombre comercial o razón social usando índices de base de datos.

        Args:
            termino: Término de búsqueda (mínimo 2 caracteres)
            limite: Número máximo de resultados

        Returns:
            Lista de empresas que coinciden con el término (vacía si no hay o termino < 2 chars)

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino) < 2:
            return []

        # Delegar búsqueda al repository (usa índices DB, ~100x más rápido)
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
        Busca empresas con filtros combinados aplicados en la base de datos.
        Optimizado para performance con índices y límites.

        Args:
            texto: Término de búsqueda (mínimo 2 caracteres para activar búsqueda)
            tipo_empresa: Filtrar por tipo (NOMINA o MANTENIMIENTO)
            estatus: Filtrar por estatus específico
            incluir_inactivas: Si incluir empresas inactivas
            limite: Número máximo de resultados (default 50 para UI)
            offset: Número de registros a saltar (paginación)

        Returns:
            Lista de resúmenes de empresas que coinciden con los filtros

        Raises:
            DatabaseError: Si hay error de BD
        """
        # Validar texto mínimo si se proporciona
        if texto and len(texto.strip()) < 2:
            texto = None  # Ignorar búsquedas muy cortas

        # Delegar al repository con todos los filtros
        empresas = await self.repository.buscar_con_filtros(
            texto=texto,
            tipo_empresa=tipo_empresa,
            estatus=estatus,
            incluir_inactivas=incluir_inactivas,
            limite=limite,
            offset=offset
        )

        # Convertir a resumen para la UI
        return [EmpresaResumen.from_empresa(empresa) for empresa in empresas]

    async def crear(self, empresa_create: EmpresaCreate) -> Empresa:
        """
        Crea una nueva empresa con código corto autogenerado.

        Args:
            empresa_create: Datos de la empresa a crear

        Returns:
            Empresa creada con ID y codigo_corto asignados

        Raises:
            DuplicateError: Si el RFC ya existe
            ValidationError: Si los datos no son válidos
            DatabaseError: Si hay error de BD
        """
        # Generar código corto único
        codigo_corto = await self._generar_codigo_unico(empresa_create.nombre_comercial)

        # Convertir EmpresaCreate a Empresa con código asignado
        datos = empresa_create.model_dump()
        datos['codigo_corto'] = codigo_corto
        empresa = Empresa(**datos)

        # Validación de reglas de negocio
        if empresa.tipo_empresa == TipoEmpresa.NOMINA:
            if not empresa.email:
                logger.warning("Empresa de nómina creada sin email")

        # Delegar al repository (propaga DuplicateError o DatabaseError)
        return await self.repository.crear(empresa)

    async def _generar_codigo_unico(self, nombre_comercial: str) -> str:
        """
        Genera un código corto único para la empresa.

        Algoritmo:
        1. Nivel 1: Primeras 3 letras de primera palabra significativa
        2. Nivel 2: Iniciales de primeras 3 palabras (estilo RFC)
        3. Fallback: Base + número incremental (XX2, XX3...)

        Args:
            nombre_comercial: Nombre comercial de la empresa

        Returns:
            Código único de 3 caracteres

        Raises:
            DatabaseError: Si no se puede generar un código único
        """
        candidatos = generar_candidatos_codigo(nombre_comercial)

        for codigo in candidatos:
            if not await self.repository.existe_codigo_corto(codigo):
                logger.info(f"Código '{codigo}' asignado para '{nombre_comercial}'")
                return codigo

        # Si llegamos aquí, algo muy raro pasó (>100 colisiones)
        raise DatabaseError(
            f"No se pudo generar código único para '{nombre_comercial}' "
            f"después de {len(candidatos)} intentos"
        )

    async def actualizar(self, empresa_id: int, empresa_update: EmpresaUpdate) -> Empresa:
        """
        Actualiza una empresa existente.

        Args:
            empresa_id: ID de la empresa a actualizar
            empresa_update: Datos a actualizar

        Returns:
            Empresa actualizada

        Raises:
            NotFoundError: Si la empresa no existe
            ValidationError: Si los datos no son válidos
            DatabaseError: Si hay error de BD
        """
        # Obtener empresa actual (propaga NotFoundError)
        empresa_actual = await self.repository.obtener_por_id(empresa_id)

        # Aplicar actualizaciones
        datos_actualizados = empresa_actual.model_dump()
        for campo, valor in empresa_update.model_dump(exclude_unset=True).items():
            if valor is not None:
                datos_actualizados[campo] = valor

        # Crear empresa modificada (puede lanzar ValidationError)
        empresa_modificada = Empresa(**datos_actualizados)

        # Actualizar en BD (propaga NotFoundError o DatabaseError)
        return await self.repository.actualizar(empresa_modificada)

    async def cambiar_estatus(self, empresa_id: int, nuevo_estatus: EstatusEmpresa) -> bool:
        """
        Cambia el estatus de una empresa.

        Args:
            empresa_id: ID de la empresa
            nuevo_estatus: Nuevo estatus a asignar

        Returns:
            True si se cambió exitosamente

        Raises:
            NotFoundError: Si la empresa no existe
            DatabaseError: Si hay error de BD
        """
        # Obtener empresa (propaga NotFoundError)
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

        Args:
            empresa_id: ID de la empresa a eliminar

        Returns:
            True si se eliminó exitosamente

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.eliminar(empresa_id)


# Instancia global del servicio (singleton)
empresa_service = EmpresaService()
