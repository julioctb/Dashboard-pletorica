"""
Servicio de aplicación para gestión de Plazas.

Una Plaza es una instancia individual de un puesto dentro de un ContratoCategoría.
Maneja la creación, asignación de empleados, y cambios de estado.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio agrega validaciones de reglas de negocio (BusinessRuleError)
"""
import logging
from typing import List, Optional
from decimal import Decimal
from datetime import date

from app.entities.plaza import (
    Plaza,
    PlazaCreate,
    PlazaUpdate,
    PlazaResumen,
    ResumenPlazasContrato,
    ResumenPlazasCategoria,
)
from app.repositories.plaza_repository import SupabasePlazaRepository
from app.core.enums import EstatusPlaza
from app.core.exceptions import BusinessRuleError, NotFoundError

logger = logging.getLogger(__name__)


class PlazaService:
    """
    Servicio de aplicación para Plaza.
    Orquesta las operaciones de negocio.
    """

    def __init__(self, repository=None):
        if repository is None:
            repository = SupabasePlazaRepository()
        self.repository = repository

    # ==========================================
    # OPERACIONES DE LECTURA
    # ==========================================

    async def obtener_por_id(self, id: int) -> Plaza:
        """
        Obtiene una plaza por su ID.

        Raises:
            NotFoundError: Si la plaza no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(id)

    async def obtener_por_contrato_categoria(
        self,
        contrato_categoria_id: int,
        incluir_canceladas: bool = False
    ) -> List[Plaza]:
        """
        Obtiene todas las plazas de una ContratoCategoria.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_contrato_categoria(
            contrato_categoria_id,
            incluir_canceladas
        )

    async def obtener_por_contrato(
        self,
        contrato_id: int,
        incluir_canceladas: bool = False
    ) -> List[Plaza]:
        """
        Obtiene todas las plazas de un contrato.

        Raises:
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_contrato(
            contrato_id,
            incluir_canceladas
        )

    async def obtener_vacantes_por_contrato_categoria(
        self,
        contrato_categoria_id: int
    ) -> List[Plaza]:
        """
        Obtiene las plazas vacantes de una ContratoCategoria.
        Útil para el dropdown de asignación de empleados.
        """
        return await self.repository.obtener_vacantes_por_contrato_categoria(
            contrato_categoria_id
        )

    async def obtener_resumen_de_contrato(
        self,
        contrato_id: int
    ) -> List[PlazaResumen]:
        """
        Obtiene resumen de plazas con datos enriquecidos.

        Returns:
            Lista de PlazaResumen ordenada por categoría y número de plaza
        """
        resumen_data = await self.repository.obtener_resumen_por_contrato(contrato_id)

        return [
            PlazaResumen(
                id=item['id'],
                contrato_categoria_id=item['contrato_categoria_id'],
                numero_plaza=item['numero_plaza'],
                codigo=item.get('codigo', ''),
                empleado_id=item.get('empleado_id'),
                fecha_inicio=item['fecha_inicio'],
                fecha_fin=item.get('fecha_fin'),
                salario_mensual=Decimal(str(item['salario_mensual'])),
                estatus=EstatusPlaza(item['estatus']),
                notas=item.get('notas'),
                contrato_id=item.get('contrato_id', 0),
                contrato_codigo=item.get('contrato_codigo', ''),
                categoria_puesto_id=item.get('categoria_puesto_id', 0),
                categoria_clave=item.get('categoria_clave', ''),
                categoria_nombre=item.get('categoria_nombre', ''),
                empleado_nombre=item.get('empleado_nombre', ''),
                empleado_curp=item.get('empleado_curp', ''),
            )
            for item in resumen_data
        ]

    async def obtener_resumen_de_categoria(
        self,
        contrato_categoria_id: int,
        incluir_canceladas: bool = False
    ) -> List[PlazaResumen]:
        """
        Obtiene resumen de plazas de una categoría con datos del empleado.

        Returns:
            Lista de PlazaResumen ordenada por número de plaza
        """
        resumen_data = await self.repository.obtener_resumen_por_contrato_categoria(
            contrato_categoria_id,
            incluir_canceladas
        )

        return [
            PlazaResumen(
                id=item['id'],
                contrato_categoria_id=item['contrato_categoria_id'],
                numero_plaza=item['numero_plaza'],
                codigo=item.get('codigo', ''),
                empleado_id=item.get('empleado_id'),
                fecha_inicio=item['fecha_inicio'],
                fecha_fin=item.get('fecha_fin'),
                salario_mensual=Decimal(str(item['salario_mensual'])),
                estatus=EstatusPlaza(item['estatus']),
                notas=item.get('notas'),
                empleado_nombre=item.get('empleado_nombre', ''),
                empleado_curp=item.get('empleado_curp', ''),
            )
            for item in resumen_data
        ]

    async def calcular_totales_contrato(self, contrato_id: int) -> ResumenPlazasContrato:
        """
        Calcula los totales de plazas para un contrato.

        Returns:
            ResumenPlazasContrato con totales por estatus
        """
        totales = await self.repository.obtener_totales_por_contrato(contrato_id)

        return ResumenPlazasContrato(
            contrato_id=contrato_id,
            total_plazas=totales['total_plazas'],
            plazas_vacantes=totales['plazas_vacantes'],
            plazas_ocupadas=totales['plazas_ocupadas'],
            plazas_suspendidas=totales['plazas_suspendidas'],
            plazas_canceladas=totales['plazas_canceladas'],
            costo_total_mensual=totales['costo_total_mensual'],
        )

    async def obtener_resumen_categorias_con_plazas(self) -> List[dict]:
        """
        Obtiene un resumen de todas las categorías de contrato que tienen plazas.

        Returns:
            Lista de dicts con empresa, contrato, categoría y conteo de plazas
        """
        return await self.repository.obtener_resumen_categorias_con_plazas()

    async def obtener_contratos_con_plazas_pendientes(self) -> List[dict]:
        """
        Obtiene contratos que tienen categorías con plazas pendientes por crear.

        Returns:
            Lista de dicts con datos del contrato
        """
        return await self.repository.obtener_contratos_con_plazas_pendientes()

    async def obtener_empleados_asignados(self) -> List[int]:
        """
        Obtiene los IDs de empleados que ya están asignados a una plaza ocupada.

        Returns:
            Lista de IDs de empleados asignados
        """
        return await self.repository.obtener_empleados_asignados()

    async def calcular_totales_categoria(
        self,
        contrato_categoria_id: int
    ) -> ResumenPlazasCategoria:
        """
        Calcula los totales de plazas para una ContratoCategoria.

        Returns:
            ResumenPlazasCategoria con totales y datos de la categoría
        """
        # Importar dentro del método para evitar imports circulares
        from app.services import contrato_categoria_service

        # Obtener datos de la contrato_categoria
        cc = await contrato_categoria_service.obtener_por_id(contrato_categoria_id)
        resumen_cc = await contrato_categoria_service.obtener_resumen_de_contrato(cc.contrato_id)

        # Buscar la categoría específica en el resumen
        categoria_data = next(
            (r for r in resumen_cc if r.id == contrato_categoria_id),
            None
        )

        # Calcular totales de plazas
        totales = await self.repository.obtener_totales_por_contrato_categoria(
            contrato_categoria_id
        )

        return ResumenPlazasCategoria(
            contrato_categoria_id=contrato_categoria_id,
            categoria_clave=categoria_data.categoria_clave if categoria_data else '',
            categoria_nombre=categoria_data.categoria_nombre if categoria_data else '',
            cantidad_minima=cc.cantidad_minima,
            cantidad_maxima=cc.cantidad_maxima,
            total_plazas=totales['total_plazas'],
            plazas_vacantes=totales['plazas_vacantes'],
            plazas_ocupadas=totales['plazas_ocupadas'],
            plazas_suspendidas=totales['plazas_suspendidas'],
            costo_total_mensual=totales['costo_total_mensual'],
        )

    # ==========================================
    # OPERACIONES DE ESCRITURA
    # ==========================================

    async def crear(self, plaza_create: PlazaCreate) -> Plaza:
        """
        Crea una nueva plaza.

        Validaciones:
        - La ContratoCategoria debe existir
        - El número de plaza no puede exceder cantidad_maxima
        - El código debe ser único si se proporciona

        Raises:
            BusinessRuleError: Si no cumple reglas de negocio
            DuplicateError: Si el número de plaza ya existe
            DatabaseError: Si hay error de BD
        """
        await self._validar_creacion_plaza(plaza_create)

        plaza = Plaza(**plaza_create.model_dump())

        logger.info(
            f"Creando plaza: contrato_categoria={plaza.contrato_categoria_id}, "
            f"numero={plaza.numero_plaza}"
        )

        return await self.repository.crear(plaza)

    async def actualizar(
        self,
        id: int,
        plaza_update: PlazaUpdate
    ) -> Plaza:
        """
        Actualiza una plaza existente.

        No permite cambiar contrato_categoria_id ni numero_plaza.

        Raises:
            NotFoundError: Si la plaza no existe
            BusinessRuleError: Si la operación no es válida
            DatabaseError: Si hay error de BD
        """
        plaza_actual = await self.repository.obtener_por_id(id)

        datos_actualizados = plaza_update.model_dump(exclude_unset=True)

        # Validar cambio de estatus si se incluye
        if 'estatus' in datos_actualizados and datos_actualizados['estatus'] is not None:
            nuevo_estatus = datos_actualizados['estatus']
            self._validar_transicion_estatus(plaza_actual.estatus, nuevo_estatus)

        for campo, valor in datos_actualizados.items():
            if valor is not None:
                setattr(plaza_actual, campo, valor)

        logger.info(f"Actualizando plaza ID {id}")

        return await self.repository.actualizar(plaza_actual)

    async def cancelar(self, id: int) -> Plaza:
        """
        Cancela una plaza (Soft Delete).

        Libera el empleado asociado si existe.

        Raises:
            NotFoundError: Si la plaza no existe
            BusinessRuleError: Si la plaza ya está cancelada
            DatabaseError: Si hay error de BD
        """
        plaza = await self.repository.obtener_por_id(id)

        if not plaza.puede_cancelar():
            raise BusinessRuleError("La plaza ya está cancelada")

        logger.info(
            f"Cancelando plaza: id={id}, contrato_categoria={plaza.contrato_categoria_id}"
        )

        return await self.repository.cancelar(id)

    # ==========================================
    # OPERACIONES DE ESTADO
    # ==========================================

    async def asignar_empleado(
        self,
        plaza_id: int,
        empleado_id: int
    ) -> Plaza:
        """
        Asigna un empleado a una plaza vacante.

        Raises:
            NotFoundError: Si la plaza no existe
            BusinessRuleError: Si la plaza no está vacante
        """
        plaza = await self.repository.obtener_por_id(plaza_id)

        if not plaza.puede_ocupar():
            raise BusinessRuleError(
                f"La plaza no está vacante (estatus actual: {plaza.estatus.descripcion})"
            )

        plaza.empleado_id = empleado_id
        plaza.estatus = EstatusPlaza.OCUPADA

        logger.info(f"Asignando empleado {empleado_id} a plaza {plaza_id}")

        return await self.repository.actualizar(plaza)

    async def liberar_plaza(self, plaza_id: int) -> Plaza:
        """
        Libera una plaza ocupada (la vuelve vacante).

        Raises:
            NotFoundError: Si la plaza no existe
            BusinessRuleError: Si la plaza no está ocupada
        """
        plaza = await self.repository.obtener_por_id(plaza_id)

        if not plaza.esta_ocupada():
            raise BusinessRuleError(
                f"La plaza no está ocupada (estatus actual: {plaza.estatus.descripcion})"
            )

        plaza.empleado_id = None
        plaza.estatus = EstatusPlaza.VACANTE

        logger.info(f"Liberando plaza {plaza_id}")

        return await self.repository.actualizar(plaza)

    async def suspender_plaza(self, plaza_id: int) -> Plaza:
        """
        Suspende una plaza.

        Libera el empleado si está ocupada.

        Raises:
            NotFoundError: Si la plaza no existe
            BusinessRuleError: Si la plaza no puede ser suspendida
        """
        plaza = await self.repository.obtener_por_id(plaza_id)

        if not plaza.puede_suspender():
            raise BusinessRuleError(
                f"No se puede suspender una plaza en estatus {plaza.estatus.descripcion}"
            )

        plaza.empleado_id = None
        plaza.estatus = EstatusPlaza.SUSPENDIDA

        logger.info(f"Suspendiendo plaza {plaza_id}")

        return await self.repository.actualizar(plaza)

    async def reactivar_plaza(self, plaza_id: int) -> Plaza:
        """
        Reactiva una plaza suspendida (la vuelve vacante).

        Raises:
            NotFoundError: Si la plaza no existe
            BusinessRuleError: Si la plaza no puede ser reactivada
        """
        plaza = await self.repository.obtener_por_id(plaza_id)

        if not plaza.puede_reactivar():
            raise BusinessRuleError(
                f"Solo se pueden reactivar plazas suspendidas "
                f"(estatus actual: {plaza.estatus.descripcion})"
            )

        plaza.estatus = EstatusPlaza.VACANTE

        logger.info(f"Reactivando plaza {plaza_id}")

        return await self.repository.actualizar(plaza)

    # ==========================================
    # OPERACIONES EN LOTE
    # ==========================================

    async def crear_plazas_para_categoria(
        self,
        contrato_categoria_id: int,
        cantidad: int,
        salario_mensual: Decimal,
        fecha_inicio: date,
        fecha_fin: Optional[date] = None,
        prefijo_codigo: str = ""
    ) -> List[Plaza]:
        """
        Crea múltiples plazas para una ContratoCategoria.

        Args:
            contrato_categoria_id: ID de la ContratoCategoria
            cantidad: Número de plazas a crear
            salario_mensual: Salario para todas las plazas
            fecha_inicio: Fecha de inicio de las plazas
            fecha_fin: Fecha de fin (opcional)
            prefijo_codigo: Prefijo para generar códigos (ej: "JAR" → JAR-001)

        Returns:
            Lista de plazas creadas

        Raises:
            BusinessRuleError: Si la cantidad excede el máximo permitido
        """
        # Importar dentro del método para evitar imports circulares
        from app.services import contrato_categoria_service

        # Validar que la ContratoCategoria existe
        cc = await contrato_categoria_service.obtener_por_id(contrato_categoria_id)

        # Validar cantidad máxima
        plazas_existentes = await self.repository.contar_por_contrato_categoria(
            contrato_categoria_id
        )

        if plazas_existentes + cantidad > cc.cantidad_maxima:
            raise BusinessRuleError(
                f"No se pueden crear {cantidad} plazas. "
                f"Ya existen {plazas_existentes} y el máximo es {cc.cantidad_maxima}"
            )

        # Obtener siguiente número de plaza
        siguiente_numero = await self.repository.obtener_siguiente_numero_plaza(
            contrato_categoria_id
        )

        plazas_creadas = []

        for i in range(cantidad):
            numero_plaza = siguiente_numero + i
            codigo = f"{prefijo_codigo}-{numero_plaza:03d}" if prefijo_codigo else ""

            plaza_create = PlazaCreate(
                contrato_categoria_id=contrato_categoria_id,
                numero_plaza=numero_plaza,
                codigo=codigo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                salario_mensual=salario_mensual,
                estatus=EstatusPlaza.VACANTE,
            )

            plaza = Plaza(**plaza_create.model_dump())
            plaza_creada = await self.repository.crear(plaza)
            plazas_creadas.append(plaza_creada)

        logger.info(
            f"Creadas {len(plazas_creadas)} plazas para contrato_categoria {contrato_categoria_id}"
        )

        return plazas_creadas

    async def cancelar_plazas_de_categoria(
        self,
        contrato_categoria_id: int
    ) -> int:
        """
        Cancela todas las plazas de una ContratoCategoria.

        Returns:
            Cantidad de plazas canceladas
        """
        plazas = await self.repository.obtener_por_contrato_categoria(
            contrato_categoria_id,
            incluir_canceladas=False
        )

        canceladas = 0
        for plaza in plazas:
            if plaza.puede_cancelar():
                await self.repository.cancelar(plaza.id)
                canceladas += 1

        logger.info(
            f"Canceladas {canceladas} plazas de contrato_categoria {contrato_categoria_id}"
        )

        return canceladas

    # ==========================================
    # VALIDACIONES DE NEGOCIO (privadas)
    # ==========================================

    async def _validar_creacion_plaza(self, plaza_create: PlazaCreate) -> None:
        """
        Valida que se puede crear la plaza.

        Reglas:
        - La ContratoCategoria debe existir
        - El número de plaza no puede exceder cantidad_maxima
        """
        # Importar dentro del método para evitar imports circulares
        from app.services import contrato_categoria_service

        # Validar que la ContratoCategoria existe
        try:
            cc = await contrato_categoria_service.obtener_por_id(
                plaza_create.contrato_categoria_id
            )
        except NotFoundError:
            raise BusinessRuleError(
                f"La ContratoCategoria con ID {plaza_create.contrato_categoria_id} no existe"
            )

        # Validar que no excede el máximo
        plazas_existentes = await self.repository.contar_por_contrato_categoria(
            plaza_create.contrato_categoria_id
        )

        if plazas_existentes >= cc.cantidad_maxima:
            raise BusinessRuleError(
                f"Ya se alcanzó el máximo de plazas ({cc.cantidad_maxima}) "
                f"para esta categoría"
            )

    def _validar_transicion_estatus(
        self,
        estatus_actual: EstatusPlaza,
        nuevo_estatus: EstatusPlaza
    ) -> None:
        """
        Valida que la transición de estatus es válida.

        Transiciones permitidas:
        - VACANTE → OCUPADA, SUSPENDIDA, CANCELADA
        - OCUPADA → VACANTE, SUSPENDIDA, CANCELADA
        - SUSPENDIDA → VACANTE, CANCELADA
        - CANCELADA → (ninguna, es estado final)
        """
        transiciones_validas = {
            EstatusPlaza.VACANTE: {
                EstatusPlaza.OCUPADA,
                EstatusPlaza.SUSPENDIDA,
                EstatusPlaza.CANCELADA
            },
            EstatusPlaza.OCUPADA: {
                EstatusPlaza.VACANTE,
                EstatusPlaza.SUSPENDIDA,
                EstatusPlaza.CANCELADA
            },
            EstatusPlaza.SUSPENDIDA: {
                EstatusPlaza.VACANTE,
                EstatusPlaza.CANCELADA
            },
            EstatusPlaza.CANCELADA: set(),  # No se puede salir de CANCELADA
        }

        permitidas = transiciones_validas.get(estatus_actual, set())

        if nuevo_estatus not in permitidas:
            raise BusinessRuleError(
                f"No se puede cambiar de {estatus_actual.descripcion} "
                f"a {nuevo_estatus.descripcion}"
            )


# ==========================================
# SINGLETON
# ==========================================

plaza_service = PlazaService()
