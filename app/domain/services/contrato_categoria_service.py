"""
Servicio de aplicacion para gestion de Contrato-Categoria.

Maneja la asignacion de categorias de puesto a contratos,
incluyendo validaciones de reglas de negocio.

Patron de manejo de errores:
- NotFoundError: Cuando no se encuentra un recurso
- DuplicateError: Cuando se viola unicidad (contrato_id + categoria_puesto_id)
- DatabaseError: Errores de conexion o infraestructura
- BusinessRuleError: Reglas de negocio violadas
"""
import logging
from decimal import Decimal
from string import ascii_uppercase
from typing import List, Optional

from app.domain.models.contrato_categoria import (
    ContratoCategoria,
    ContratoCategoriaCreate,
    ContratoCategoriaUpdate,
    ContratoCategoriaResumen,
    ResumenPersonalContrato,
)
from app.domain.models.categoria_puesto import CategoriaPuestoCreate
from app.domain.enums import TipoSueldo
from app.domain.repositories import SupabaseContratoCategoriaRepository
from app.core.exceptions import NotFoundError, BusinessRuleError
from app.core.text_utils import normalizar_mayusculas

logger = logging.getLogger(__name__)


class ContratoCategoriaService:
    """
    Servicio de aplicacion para ContratoCategoria.
    Orquesta las operaciones de negocio delegando acceso a datos al repositorio.
    """

    def __init__(self):
        self.repository = SupabaseContratoCategoriaRepository()

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, id: int) -> ContratoCategoria:
        """
        Obtiene una asignacion por su ID.

        Raises:
            NotFoundError: Si la asignacion no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(id)

    async def obtener_categorias_de_contrato(
        self,
        contrato_id: int
    ) -> List[ContratoCategoria]:
        """
        Obtiene todas las categorias asignadas a un contrato.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_contrato(contrato_id)

    async def obtener_resumen_de_contrato(
        self,
        contrato_id: int
    ) -> List[ContratoCategoriaResumen]:
        """
        Obtiene resumen con datos de categoria incluidos.

        Returns:
            Lista de ContratoCategoriaResumen ordenada por orden de categoria
        """
        resumen_data = await self.repository.obtener_resumen_por_contrato(contrato_id)

        return [
            ContratoCategoriaResumen(
                id=item['id'],
                contrato_id=item['contrato_id'],
                categoria_puesto_id=item['categoria_puesto_id'],
                cantidad_minima=item['cantidad_minima'],
                cantidad_maxima=item['cantidad_maxima'],
                costo_unitario=Decimal(str(item['costo_unitario'])) if item.get('costo_unitario') else None,
                costo_contractual=(
                    Decimal(str(item['costo_contractual']))
                    if item.get('costo_contractual') is not None
                    else None
                ),
                sueldo_base=(
                    Decimal(str(item['sueldo_base']))
                    if item.get('sueldo_base') is not None
                    else (
                        Decimal(str(item['costo_unitario']))
                        if item.get('costo_unitario') is not None
                        else None
                    )
                ),
                tipo_sueldo=TipoSueldo(str(item.get('tipo_sueldo') or TipoSueldo.BRUTO.value)),
                nombre=item.get('nombre') or item.get('categoria_nombre', ''),
                notas=item.get('notas'),
                categoria_clave=item.get('categoria_clave', ''),
                categoria_nombre=item.get('categoria_nombre', ''),
                costo_minimo=Decimal(str(item['cantidad_minima'])) * Decimal(str(item['costo_unitario'])) if item.get('costo_unitario') else None,
                costo_maximo=Decimal(str(item['cantidad_maxima'])) * Decimal(str(item['costo_unitario'])) if item.get('costo_unitario') else None,
            )
            for item in resumen_data
        ]

    async def obtener_categorias_disponibles(
        self,
        contrato_id: int
    ) -> List[dict]:
        """
        Obtiene las categorias que aun no estan asignadas al contrato.

        Returns:
            Lista de categorias disponibles para asignar
        """
        from app.domain.services import contrato_service, categoria_puesto_service

        contrato = await contrato_service.obtener_por_id(contrato_id)

        if not contrato.tipo_servicio_id:
            return []

        todas_categorias = await categoria_puesto_service.obtener_por_tipo_servicio(
            contrato.tipo_servicio_id,
            incluir_inactivas=False
        )

        asignadas = await self.repository.obtener_por_contrato(contrato_id)
        ids_asignadas = {a.categoria_puesto_id for a in asignadas}

        disponibles = [
            {
                'id': cat.id,
                'clave': cat.clave,
                'nombre': cat.nombre,
                'orden': cat.orden,
            }
            for cat in todas_categorias
            if cat.id not in ids_asignadas
        ]

        return disponibles

    async def calcular_total_personal(self, contrato_id: int) -> ResumenPersonalContrato:
        """
        Calcula los totales de personal y costos para un contrato.

        Returns:
            ResumenPersonalContrato con totales
        """
        totales = await self.repository.obtener_totales_por_contrato(contrato_id)

        return ResumenPersonalContrato(
            contrato_id=contrato_id,
            cantidad_categorias=totales['cantidad_categorias'],
            total_minimo=totales['total_minimo'],
            total_maximo=totales['total_maximo'],
            costo_minimo_total=totales['costo_minimo_total'],
            costo_maximo_total=totales['costo_maximo_total'],
        )

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(
        self,
        contrato_categoria_create: ContratoCategoriaCreate
    ) -> ContratoCategoria:
        """
        Crea una nueva asignacion de categoria a contrato.

        Raises:
            BusinessRuleError: Si no cumple reglas de negocio
            DuplicateError: Si la categoria ya esta asignada
            DatabaseError: Si hay error de BD
        """
        await self._validar_asignacion(
            contrato_categoria_create.contrato_id,
            contrato_categoria_create.categoria_puesto_id
        )

        contrato_categoria = ContratoCategoria(**contrato_categoria_create.model_dump())

        logger.info(
            f"Creando asignacion: contrato={contrato_categoria.contrato_id}, "
            f"categoria={contrato_categoria.categoria_puesto_id}"
        )

        return await self.repository.crear(contrato_categoria)

    async def crear_categoria_portal(
        self,
        contrato_id: int,
        *,
        nombre: str,
        sueldo_base: Decimal,
        tipo_sueldo: TipoSueldo | str = TipoSueldo.BRUTO,
        sueldo_bruto: Decimal,
        costo_contractual: Optional[Decimal] = None,
        min_plazas: int = 0,
        max_plazas: Optional[int] = None,
    ) -> ContratoCategoria:
        """Crea una categoría contractual visible en portal con sueldo ancla."""
        nombre_normalizado = self._normalizar_nombre_categoria_portal(nombre)
        tipo = self._normalizar_tipo_sueldo(tipo_sueldo)
        if not nombre_normalizado:
            raise BusinessRuleError("Captura el nombre de la categoría")
        if sueldo_base <= Decimal("0"):
            raise BusinessRuleError("Captura un sueldo mayor a 0")
        if sueldo_bruto <= Decimal("0"):
            raise BusinessRuleError("No se pudo calcular el sueldo bruto de referencia")

        min_val = max(0, int(min_plazas or 0))
        max_val = 0 if max_plazas in (None, 0) else max(0, int(max_plazas))
        if max_val > 0 and max_val < min_val:
            raise BusinessRuleError(
                "El máximo de plazas no puede ser menor al mínimo"
            )
        if costo_contractual is not None and costo_contractual < Decimal("0"):
            raise BusinessRuleError("El costo contractual no puede ser negativo")

        categoria_puesto_id = await self._resolver_categoria_puesto_portal(
            contrato_id,
            nombre_normalizado,
            sueldo_bruto,
        )

        return await self.crear(
            ContratoCategoriaCreate(
                contrato_id=contrato_id,
                categoria_puesto_id=categoria_puesto_id,
                cantidad_minima=min_val,
                cantidad_maxima=max_val,
                costo_unitario=sueldo_bruto,
                costo_contractual=costo_contractual,
                sueldo_base=sueldo_base,
                tipo_sueldo=tipo,
                nombre=nombre_normalizado,
            )
        )

    async def actualizar(
        self,
        id: int,
        contrato_categoria_update: ContratoCategoriaUpdate
    ) -> ContratoCategoria:
        """
        Actualiza una asignacion existente.

        Raises:
            NotFoundError: Si la asignacion no existe
            DatabaseError: Si hay error de BD
        """
        asignacion_actual = await self.repository.obtener_por_id(id)
        await self._validar_contrato_permite_personal(asignacion_actual.contrato_id)

        datos_actualizados = contrato_categoria_update.model_dump(exclude_unset=True)

        nueva_min = datos_actualizados.get('cantidad_minima', asignacion_actual.cantidad_minima)
        nueva_max = datos_actualizados.get('cantidad_maxima', asignacion_actual.cantidad_maxima)

        if nueva_max > 0 and nueva_max < nueva_min:
            raise BusinessRuleError(
                f"La cantidad maxima ({nueva_max}) debe ser mayor o igual "
                f"a la cantidad minima ({nueva_min})"
            )

        for campo, valor in datos_actualizados.items():
            if campo in {'cantidad_minima', 'cantidad_maxima'}:
                if valor is None:
                    continue
                setattr(asignacion_actual, campo, int(valor))
                continue
            if valor is not None:
                setattr(asignacion_actual, campo, valor)

        logger.info(f"Actualizando asignacion ID {id}")

        return await self.repository.actualizar(asignacion_actual)

    async def actualizar_categoria_portal(
        self,
        id: int,
        *,
        nombre: str,
        sueldo_base: Decimal,
        tipo_sueldo: TipoSueldo | str = TipoSueldo.BRUTO,
        sueldo_bruto: Decimal,
        costo_contractual: Optional[Decimal] = None,
        min_plazas: int = 0,
        max_plazas: Optional[int] = None,
    ) -> ContratoCategoria:
        """Actualiza los datos visibles de una categoría contractual desde portal."""
        nombre_normalizado = self._normalizar_nombre_categoria_portal(nombre)
        tipo = self._normalizar_tipo_sueldo(tipo_sueldo)
        if not nombre_normalizado:
            raise BusinessRuleError("Captura el nombre de la categoría")
        if sueldo_base <= Decimal("0"):
            raise BusinessRuleError("Captura un sueldo mayor a 0")
        if sueldo_bruto <= Decimal("0"):
            raise BusinessRuleError("No se pudo calcular el sueldo bruto de referencia")

        min_val = max(0, int(min_plazas or 0))
        max_val = 0 if max_plazas in (None, 0) else max(0, int(max_plazas))
        if max_val > 0 and max_val < min_val:
            raise BusinessRuleError(
                "El máximo de plazas no puede ser menor al mínimo"
            )
        if costo_contractual is not None and costo_contractual < Decimal("0"):
            raise BusinessRuleError("El costo contractual no puede ser negativo")

        return await self.actualizar(
            id,
            ContratoCategoriaUpdate(
                nombre=nombre_normalizado,
                sueldo_base=sueldo_base,
                tipo_sueldo=tipo,
                costo_unitario=sueldo_bruto,
                costo_contractual=costo_contractual,
                cantidad_minima=min_val,
                cantidad_maxima=max_val,
            ),
        )

    async def eliminar(self, id: int) -> bool:
        """
        Elimina una asignacion (Hard Delete).

        Raises:
            NotFoundError: Si la asignacion no existe
            DatabaseError: Si hay error de BD
        """
        asignacion = await self.repository.obtener_por_id(id)
        await self._validar_contrato_permite_personal(asignacion.contrato_id)

        logger.info(
            f"Eliminando asignacion: contrato={asignacion.contrato_id}, "
            f"categoria={asignacion.categoria_puesto_id}"
        )

        return await self.repository.eliminar(id)

    # ==========================================
    # OPERACIONES EN LOTE
    # ==========================================

    async def asignar_categorias(
        self,
        contrato_id: int,
        categorias: List[dict]
    ) -> List[ContratoCategoria]:
        """
        Asigna multiples categorias a un contrato.

        Raises:
            BusinessRuleError: Si alguna categoria no cumple reglas
            DuplicateError: Si alguna categoria ya esta asignada
        """
        await self._validar_contrato_permite_personal(contrato_id)

        resultados = []

        for cat_data in categorias:
            categoria_puesto_id = cat_data.get('categoria_puesto_id')

            await self._validar_categoria_para_contrato(contrato_id, categoria_puesto_id)

            create_data = ContratoCategoriaCreate(
                contrato_id=contrato_id,
                categoria_puesto_id=categoria_puesto_id,
                cantidad_minima=cat_data.get('cantidad_minima', 0),
                cantidad_maxima=cat_data.get('cantidad_maxima', 0),
                costo_unitario=cat_data.get('costo_unitario'),
                notas=cat_data.get('notas'),
            )

            contrato_categoria = ContratoCategoria(**create_data.model_dump())
            resultado = await self.repository.crear(contrato_categoria)
            resultados.append(resultado)

        logger.info(f"Asignadas {len(resultados)} categorias al contrato {contrato_id}")

        return resultados

    async def eliminar_por_contrato(self, contrato_id: int) -> int:
        """
        Elimina todas las asignaciones de un contrato.

        Returns:
            Cantidad de registros eliminados
        """
        await self._validar_contrato_permite_personal(contrato_id)
        cantidad = await self.repository.eliminar_por_contrato(contrato_id)

        logger.info(f"Eliminadas {cantidad} asignaciones del contrato {contrato_id}")

        return cantidad

    async def reemplazar_categorias(
        self,
        contrato_id: int,
        categorias: List[dict]
    ) -> List[ContratoCategoria]:
        """
        Reemplaza todas las categorias de un contrato.

        Returns:
            Lista de nuevas asignaciones
        """
        await self.eliminar_por_contrato(contrato_id)

        if not categorias:
            return []

        return await self.asignar_categorias(contrato_id, categorias)

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_asignacion(
        self,
        contrato_id: int,
        categoria_puesto_id: int
    ) -> None:
        """Valida que se puede crear la asignacion."""
        await self._validar_contrato_permite_personal(contrato_id)
        await self._validar_categoria_para_contrato(contrato_id, categoria_puesto_id)

    async def _validar_contrato_permite_personal(self, contrato_id: int) -> None:
        """Valida que el contrato existe y permite personal."""
        from app.domain.services import contrato_service

        try:
            contrato = await contrato_service.obtener_por_id(contrato_id)
        except NotFoundError:
            raise BusinessRuleError(f"El contrato con ID {contrato_id} no existe")

        if not contrato.puede_modificarse():
            raise BusinessRuleError(
                f"El contrato '{contrato.codigo}' no permite modificar personal "
                f"en estatus {contrato.estatus}"
            )

        if not contrato.tiene_personal:
            raise BusinessRuleError(
                f"El contrato '{contrato.codigo}' no permite asignacion de personal "
                f"(tiene_personal = False)"
            )

    async def _validar_categoria_para_contrato(
        self,
        contrato_id: int,
        categoria_puesto_id: int
    ) -> None:
        """Valida que la categoria existe, esta activa y pertenece al tipo de servicio del contrato."""
        from app.domain.services import contrato_service, categoria_puesto_service
        from app.domain.enums import Estatus

        contrato = await contrato_service.obtener_por_id(contrato_id)

        try:
            categoria = await categoria_puesto_service.obtener_por_id(categoria_puesto_id)
        except NotFoundError:
            raise BusinessRuleError(f"La categoria de puesto con ID {categoria_puesto_id} no existe")

        if categoria.estatus != Estatus.ACTIVO:
            raise BusinessRuleError(
                f"La categoria '{categoria.nombre}' no esta activa"
            )

        if contrato.tipo_servicio_id and categoria.tipo_servicio_id != contrato.tipo_servicio_id:
            raise BusinessRuleError(
                f"La categoria '{categoria.nombre}' no pertenece al tipo de servicio del contrato"
            )

    async def contar_contratos_con_categoria(self, categoria_puesto_id: int) -> int:
        """Cuenta cuantos contratos usan una categoria especifica."""
        return await self.repository.contar_por_categoria(categoria_puesto_id)

    async def obtener_sugerencias_nombres_empresa(self, empresa_id: int) -> List[str]:
        """Devuelve nombres distintos de categorias ya usados en los contratos
        de la empresa, para alimentar un autocompletado en portal."""
        empresa_id = int(empresa_id or 0)
        if empresa_id <= 0:
            return []
        try:
            return await self.repository.obtener_nombres_por_empresa(empresa_id)
        except Exception as e:
            logger.error(
                f"Error obteniendo sugerencias de categorias para empresa {empresa_id}: {e}"
            )
            return []

    @staticmethod
    def _normalizar_tipo_sueldo(tipo_sueldo: TipoSueldo | str) -> TipoSueldo:
        if isinstance(tipo_sueldo, TipoSueldo):
            return tipo_sueldo
        return TipoSueldo(str(tipo_sueldo or TipoSueldo.BRUTO.value).upper())

    @staticmethod
    def _normalizar_nombre_categoria_portal(nombre: str) -> str:
        return " ".join(str(nombre or "").split())

    @staticmethod
    def _iterar_claves_categoria_portal(nombre: str, existentes: set[str]):
        palabras = [
            "".join(letra for letra in palabra if letra.isalpha())
            for palabra in normalizar_mayusculas(nombre).split()
        ]
        palabras = [palabra for palabra in palabras if palabra]
        letras = "".join(palabras) or "CAT"
        clave_inicial = "".join(palabra[0] for palabra in palabras)[:5]
        if len(clave_inicial) < 2:
            clave_inicial = letras[:5]
        if len(clave_inicial) < 2:
            clave_inicial = "CAT"
        candidatos = [clave_inicial[:5], letras[:5]]
        base = (letras[:4] or "CATX").ljust(4, "X")
        candidatos.extend((base + sufijo)[:5] for sufijo in ascii_uppercase)

        vistos: set[str] = set()
        for candidato in candidatos:
            candidato_norm = normalizar_mayusculas(candidato)[:5]
            if len(candidato_norm) < 2:
                continue
            if candidato_norm in vistos or candidato_norm in existentes:
                continue
            vistos.add(candidato_norm)
            yield candidato_norm

    async def _resolver_categoria_puesto_portal(
        self,
        contrato_id: int,
        nombre: str,
        sueldo_bruto: Decimal,
    ) -> int:
        from app.domain.services import categoria_puesto_service, contrato_service

        contrato = await contrato_service.obtener_por_id(contrato_id)
        tipo_servicio_id = int(getattr(contrato, "tipo_servicio_id", 0) or 0)
        if tipo_servicio_id <= 0:
            raise BusinessRuleError(
                f"El contrato '{contrato.codigo}' no tiene tipo de servicio configurado"
            )

        categorias = await categoria_puesto_service.obtener_por_tipo_servicio(
            tipo_servicio_id,
            incluir_inactivas=False,
        )
        nombre_normalizado = normalizar_mayusculas(nombre)
        for categoria in categorias:
            if normalizar_mayusculas(getattr(categoria, "nombre", "")) == nombre_normalizado:
                return int(categoria.id or 0)

        claves_existentes = {
            normalizar_mayusculas(getattr(categoria, "clave", ""))
            for categoria in categorias
            if str(getattr(categoria, "clave", "") or "").strip()
        }
        try:
            clave = next(
                self._iterar_claves_categoria_portal(nombre, claves_existentes),
            )
        except StopIteration as exc:
            raise BusinessRuleError("No se pudo generar una clave para la categoría") from exc

        categoria = await categoria_puesto_service.crear(
            CategoriaPuestoCreate(
                tipo_servicio_id=tipo_servicio_id,
                clave=clave,
                nombre=nombre,
                descripcion=f"Generada desde el contrato {contrato.codigo}",
                salario_base_mensual=sueldo_bruto,
            )
        )
        return int(categoria.id or 0)


# ==========================================
# SINGLETON
# ==========================================

contrato_categoria_service = ContratoCategoriaService()
