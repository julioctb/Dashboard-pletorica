"""
Servicio de aplicacion para gestion de Tipos de Servicio.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (ej: clave duplicada)
- DatabaseError: Errores de conexion o infraestructura
- BusinessRuleError: Violaciones de reglas de negocio
"""
import logging
import re
from typing import List, Optional

from app.domain.models import (
    TipoServicio,
    TipoServicioCreate,
    TipoServicioUpdate,
)
from app.domain.enums import Estatus, EstatusContrato, OrigenTipoServicio
from app.domain.repositories import SupabaseTipoServicioRepository
from app.core.exceptions import BusinessRuleError, DuplicateError
from app.core.text_utils import normalizar_mayusculas
from app.core.utils import generar_candidatos_codigo
from app.domain.services.base_service import BaseService

logger = logging.getLogger(__name__)


class TipoServicioService(BaseService):
    """
    Servicio de aplicacion para tipos de servicio.
    Orquesta las operaciones de negocio delegando acceso a datos al repositorio.
    """

    def __init__(self):
        self.repository = SupabaseTipoServicioRepository()

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, tipo_id: int) -> TipoServicio:
        """
        Obtiene un tipo de servicio por su ID.

        Raises:
            NotFoundError: Si el tipo no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(tipo_id)

    async def obtener_por_clave(self, clave: str) -> Optional[TipoServicio]:
        """
        Obtiene un tipo de servicio por su clave.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_clave(clave)

    async def obtener_todas(
        self,
        incluir_inactivas: bool = False,
        limite: Optional[int] = None,
        offset: int = 0
    ) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio con paginacion.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_todas(incluir_inactivas, limite, offset)

    async def obtener_activas(self) -> List[TipoServicio]:
        """
        Obtiene todos los tipos de servicio activos.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.obtener_todas(incluir_inactivas=False)

    async def obtener_portal_empresa(
        self,
        empresa_id: int,
        *,
        incluir_inactivas: bool = False,
    ) -> List[TipoServicio]:
        """Obtiene los tipos creados por una empresa para el portal."""
        return await self.repository.obtener_por_empresa(
            empresa_id,
            incluir_inactivas=incluir_inactivas,
            origen=OrigenTipoServicio.EMPRESA,
        )

    async def obtener_activas_portal_empresa(self, empresa_id: int) -> List[TipoServicio]:
        """Obtiene tipos activos del catálogo de la empresa."""
        return await self.obtener_portal_empresa(
            empresa_id,
            incluir_inactivas=False,
        )

    async def buscar(self, termino: str, limite: int = 10) -> List[TipoServicio]:
        """
        Busca tipos por nombre o clave.

        Raises:
            DatabaseError: Si hay error de BD
        """
        if not termino or len(termino.strip()) < 2:
            return []

        return await self.repository.buscar_por_texto(termino.strip(), limite)

    async def contar(self, incluir_inactivas: bool = False) -> int:
        """
        Cuenta el total de tipos de servicio.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.contar(incluir_inactivas)

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, tipo_create: TipoServicioCreate) -> TipoServicio:
        """
        Crea un nuevo tipo de servicio.

        Raises:
            DuplicateError: Si la clave ya existe
            DatabaseError: Si hay error de BD
        """
        tipo = TipoServicio(**tipo_create.model_dump())

        logger.info(f"Creando tipo de servicio: {tipo.clave} - {tipo.nombre}")

        return await self.repository.crear(tipo)

    async def crear_portal_empresa(
        self,
        empresa_id: int,
        *,
        nombre: str,
        descripcion: Optional[str] = None,
    ) -> TipoServicio:
        """Crea un tipo de servicio dentro del catálogo propio de la empresa."""
        nombre_normalizado = normalizar_mayusculas(nombre)
        if await self.repository.existe_nombre_en_empresa(
            empresa_id,
            nombre_normalizado,
            origen=OrigenTipoServicio.EMPRESA,
        ):
            raise DuplicateError(
                f"El tipo '{nombre_normalizado}' ya existe en esta empresa",
                field="nombre",
                value=nombre_normalizado,
            )

        clave = await self._generar_clave_portal_empresa(nombre_normalizado)
        return await self.crear(
            TipoServicioCreate(
                empresa_id=empresa_id,
                clave=clave,
                nombre=nombre_normalizado,
                descripcion=descripcion,
                origen=OrigenTipoServicio.EMPRESA,
                estatus=Estatus.ACTIVO,
            )
        )

    async def actualizar(self, tipo_id: int, tipo_update: TipoServicioUpdate) -> TipoServicio:
        """
        Actualiza un tipo de servicio existente.

        Raises:
            NotFoundError: Si el tipo no existe
            DuplicateError: Si la nueva clave ya existe
            DatabaseError: Si hay error de BD
        """
        tipo_actual = await self._merge_y_actualizar(tipo_id, tipo_update, self.repository)

        logger.info(f"Actualizando tipo de servicio ID {tipo_id}")

        # Verificar clave duplicada (excluyendo el registro actual)
        if await self.repository.existe_clave(tipo_actual.clave, excluir_id=tipo_actual.id):
            from app.core.exceptions import DuplicateError
            raise DuplicateError(
                f"La clave '{tipo_actual.clave}' ya existe en otro tipo",
                field="clave",
                value=tipo_actual.clave
            )

        return await self.repository.actualizar_entidad(tipo_actual)

    async def actualizar_portal_empresa(
        self,
        tipo_id: int,
        empresa_id: int,
        *,
        nombre: str,
    ) -> TipoServicio:
        """Actualiza un tipo perteneciente al catálogo de una empresa."""
        tipo_actual = await self.obtener_por_id(tipo_id)
        self._validar_tipo_portal_empresa(tipo_actual, empresa_id)

        nombre_normalizado = normalizar_mayusculas(nombre)
        if await self.repository.existe_nombre_en_empresa(
            empresa_id,
            nombre_normalizado,
            origen=OrigenTipoServicio.EMPRESA,
            excluir_id=tipo_actual.id,
        ):
            raise DuplicateError(
                f"El tipo '{nombre_normalizado}' ya existe en esta empresa",
                field="nombre",
                value=nombre_normalizado,
            )

        return await self.actualizar(
            tipo_id,
            TipoServicioUpdate(nombre=nombre_normalizado),
        )

    async def eliminar(self, tipo_id: int) -> bool:
        """
        Elimina (desactiva) un tipo de servicio.

        Raises:
            NotFoundError: Si el tipo no existe
            BusinessRuleError: Si tiene contratos activos
            DatabaseError: Si hay error de BD
        """
        tipo = await self.repository.obtener_por_id(tipo_id)

        await self._validar_puede_eliminar(tipo)

        logger.info(f"Eliminando (desactivando) tipo de servicio: {tipo.clave}")

        return await self.repository.eliminar(tipo_id)

    async def activar(self, tipo_id: int) -> TipoServicio:
        """
        Activa un tipo de servicio que estaba inactivo.

        Raises:
            NotFoundError: Si el tipo no existe
            BusinessRuleError: Si ya esta activo
            DatabaseError: Si hay error de BD
        """
        logger.info(f"Activando tipo de servicio ID {tipo_id}")
        return await self._cambiar_estatus(
            tipo_id, Estatus.ACTIVO.value, self.repository, "El tipo"
        )

    async def activar_portal_empresa(self, tipo_id: int, empresa_id: int) -> TipoServicio:
        """Reactiva un tipo de servicio del catálogo de la empresa."""
        tipo = await self.obtener_por_id(tipo_id)
        self._validar_tipo_portal_empresa(tipo, empresa_id)
        return await self.activar(tipo_id)

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_puede_eliminar(self, tipo: TipoServicio) -> None:
        """
        Valida si un tipo puede ser eliminado.

        Reglas:
        - No debe tener contratos activos asociados
        """
        from app.domain.services.contrato_service import contrato_service

        contratos = await contrato_service.obtener_por_tipo_servicio(tipo.id)
        contratos_activos = [
            contrato
            for contrato in contratos
            if contrato.estatus in (
                EstatusContrato.BORRADOR,
                EstatusContrato.ACTIVO,
                EstatusContrato.SUSPENDIDO,
            )
        ]
        if contratos_activos:
            raise BusinessRuleError(
                f"No se puede eliminar el tipo '{tipo.nombre}' porque tiene "
                f"{len(contratos_activos)} contrato(s) activo(s) o en operación"
            )

    async def existe_clave(self, clave: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verifica si una clave ya existe.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.existe_clave(clave, excluir_id)

    def _validar_tipo_portal_empresa(self, tipo: TipoServicio, empresa_id: int) -> None:
        """Garantiza que el tipo pertenezca al catálogo editable de la empresa."""
        if int(getattr(tipo, "empresa_id", 0) or 0) != int(empresa_id or 0):
            raise BusinessRuleError("El tipo de servicio no pertenece a la empresa activa")
        origen = getattr(tipo, "origen", OrigenTipoServicio.EMPRESA)
        raw_origen = getattr(origen, "value", origen)
        if str(raw_origen or "").upper() != OrigenTipoServicio.EMPRESA.value:
            raise BusinessRuleError("El tipo de servicio es de solo lectura para la empresa")

    async def _generar_clave_portal_empresa(self, nombre: str) -> str:
        """Genera una clave corta única para tipos de servicio del portal."""
        candidatos: list[str] = []
        vistos: set[str] = set()

        def agregar(valor: str) -> None:
            candidato = re.sub(r"[^A-Z]", "", normalizar_mayusculas(valor))[:5]
            if 2 <= len(candidato) <= 5 and candidato not in vistos:
                vistos.add(candidato)
                candidatos.append(candidato)

        for candidato in generar_candidatos_codigo(nombre):
            agregar(candidato)

        nombre_normalizado = re.sub(r"[^A-Z]", "", normalizar_mayusculas(nombre))
        for longitud in range(3, min(len(nombre_normalizado), 5) + 1):
            agregar(nombre_normalizado[:longitud])
        for indice in range(max(len(nombre_normalizado) - 4, 1)):
            agregar(nombre_normalizado[indice: indice + 5])

        agregar("TIPO")

        for candidato in candidatos:
            if not await self.repository.existe_clave(candidato):
                return candidato

        raise BusinessRuleError(
            "No fue posible generar una clave única para el tipo de servicio"
        )


# ==========================================
# SINGLETON
# ==========================================

tipo_servicio_service = TipoServicioService()
