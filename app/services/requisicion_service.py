"""
Servicio de aplicación para gestión de requisiciones.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio NO captura excepciones, las deja subir al State
- Valida reglas de negocio y lanza BusinessRuleError cuando corresponde
"""
import logging
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from app.entities.requisicion import (
    ConfiguracionRequisicion,
    LugarEntrega,
    Requisicion,
    RequisicionCreate,
    RequisicionUpdate,
    RequisicionResumen,
    RequisicionAdjudicar,
    RequisicionItem,
    RequisicionItemCreate,
    RequisicionItemUpdate,
    RequisicionPartida,
    RequisicionPartidaCreate,
    RequisicionPartidaUpdate,
    TRANSICIONES_VALIDAS,
)
from app.core.enums import EstadoRequisicion
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.error_messages import (
    MSG_REQUISICION_SIN_ITEMS,
    MSG_REQUISICION_SIN_PARTIDAS,
    MSG_SOLO_ELIMINAR_BORRADOR,
    MSG_ADJUDICAR_SIN_EMPRESA,
    MSG_ADJUDICAR_SIN_FECHA,
    MSG_REQUISICION_NO_EDITABLE,
    msg_transicion_invalida,
)
from app.repositories.requisicion_repository import SupabaseRequisicionRepository

logger = logging.getLogger(__name__)


class RequisicionService:
    """
    Servicio de aplicación para requisiciones.
    Orquesta las operaciones de negocio.
    """

    def __init__(self, repository=None):
        """
        Inicializa el servicio con un repository.

        Args:
            repository: Implementación del repository. Si es None, usa Supabase por defecto.
        """
        if repository is None:
            repository = SupabaseRequisicionRepository()
        self.repository = repository

    # ==========================================
    # OPERACIONES CRUD
    # ==========================================

    async def obtener_por_id(self, requisicion_id: int) -> Requisicion:
        """
        Obtiene una requisición por su ID.

        Raises:
            NotFoundError: Si la requisición no existe
            DatabaseError: Si hay error de BD
        """
        return await self.repository.obtener_por_id(requisicion_id)

    async def obtener_resumen(
        self,
        estado: Optional[str] = None,
        tipo_contratacion: Optional[str] = None,
        incluir_canceladas: bool = False,
        limite: int = 50,
        offset: int = 0,
    ) -> List[RequisicionResumen]:
        """
        Obtiene resumen de requisiciones para listado.

        Raises:
            DatabaseError: Si hay error de BD
        """
        requisiciones = await self.repository.obtener_todos(
            estado=estado,
            tipo_contratacion=tipo_contratacion,
            incluir_canceladas=incluir_canceladas,
            limite=limite,
            offset=offset,
        )

        resumenes = []
        for req in requisiciones:
            # Cargar items y partidas para calcular totales
            items = await self.repository.obtener_items(req.id)
            partidas = await self.repository.obtener_partidas(req.id)

            total_items = len(items)
            presupuesto_total = sum(
                p.presupuesto_autorizado for p in partidas
            ) if partidas else Decimal('0')

            # Obtener nombre de empresa si está adjudicada
            empresa_nombre = None
            if req.empresa_id:
                try:
                    from app.services.empresa_service import empresa_service
                    empresa = await empresa_service.obtener_por_id(req.empresa_id)
                    empresa_nombre = empresa.nombre_comercial
                except Exception:
                    pass  # No bloquear por error al obtener nombre de empresa

            resumenes.append(RequisicionResumen(
                id=req.id,
                numero_requisicion=req.numero_requisicion,
                fecha_elaboracion=req.fecha_elaboracion,
                estado=req.estado,
                tipo_contratacion=req.tipo_contratacion,
                objeto_contratacion=req.objeto_contratacion,
                dependencia_requirente=req.dependencia_requirente,
                total_items=total_items,
                presupuesto_total=presupuesto_total,
                empresa_nombre=empresa_nombre,
                created_at=req.created_at,
            ))

        return resumenes

    async def crear(self, data: RequisicionCreate) -> Requisicion:
        """
        Crea una nueva requisición con número auto-generado.
        Permite borradores sin items ni partidas.

        Raises:
            DuplicateError: Si el número ya existe
            DatabaseError: Si hay error de BD
        """
        # Generar número auto
        numero = await self.generar_numero_requisicion()

        # Construir entidad Requisicion
        requisicion_data = data.model_dump(exclude={'items', 'partidas'})
        requisicion_data['numero_requisicion'] = numero
        requisicion_data['estado'] = EstadoRequisicion.BORRADOR

        # Construir items
        items = []
        for item_create in data.items:
            item_dict = item_create.model_dump()
            # Calcular subtotal
            if item_create.precio_unitario_estimado and item_create.cantidad:
                item_dict['subtotal_estimado'] = item_create.cantidad * item_create.precio_unitario_estimado
            items.append(RequisicionItem(**item_dict))

        # Construir partidas
        partidas = [
            RequisicionPartida(**p.model_dump())
            for p in data.partidas
        ]

        requisicion = Requisicion(
            **requisicion_data,
            items=items,
            partidas=partidas,
        )

        return await self.repository.crear(requisicion)

    async def actualizar(self, requisicion_id: int, data: RequisicionUpdate) -> Requisicion:
        """
        Actualiza una requisición existente.
        Solo permitido en estado BORRADOR.

        Raises:
            BusinessRuleError: Si el estado no permite edición
            NotFoundError: Si la requisición no existe
            DatabaseError: Si hay error de BD
        """
        requisicion = await self.repository.obtener_por_id(requisicion_id)

        if not requisicion.puede_editarse():
            raise BusinessRuleError(MSG_REQUISICION_NO_EDITABLE)

        # Aplicar cambios (solo campos no-None)
        update_data = data.model_dump(exclude_none=True)
        for campo, valor in update_data.items():
            setattr(requisicion, campo, valor)

        return await self.repository.actualizar(requisicion)

    async def eliminar(self, requisicion_id: int) -> bool:
        """
        Elimina una requisición. Solo permitido en estado BORRADOR.

        Raises:
            BusinessRuleError: Si el estado no permite eliminación
            NotFoundError: Si la requisición no existe
            DatabaseError: Si hay error de BD
        """
        requisicion = await self.repository.obtener_por_id(requisicion_id)

        if not requisicion.puede_eliminarse():
            raise BusinessRuleError(MSG_SOLO_ELIMINAR_BORRADOR)

        return await self.repository.eliminar(requisicion_id)

    # ==========================================
    # GESTIÓN DE ITEMS
    # ==========================================

    async def agregar_item(
        self, requisicion_id: int, data: RequisicionItemCreate
    ) -> RequisicionItem:
        """
        Agrega un item a una requisición.

        Raises:
            BusinessRuleError: Si el estado no permite edición
            DatabaseError: Si hay error de BD
        """
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        if not requisicion.puede_editarse():
            raise BusinessRuleError(MSG_REQUISICION_NO_EDITABLE)

        item = RequisicionItem(**data.model_dump())
        return await self.repository.crear_item(requisicion_id, item)

    async def actualizar_item(
        self, item_id: int, data: RequisicionItemUpdate
    ) -> RequisicionItem:
        """Actualiza un item existente."""
        # Obtener item actual para merge
        # El repository.actualizar_item maneja el error si no existe
        update_dict = data.model_dump(exclude_none=True)
        # Necesitamos el item completo para actualizar
        # Por simplicidad, construimos un item parcial
        item = RequisicionItem(id=item_id, **update_dict)
        return await self.repository.actualizar_item(item)

    async def eliminar_item(self, item_id: int) -> bool:
        """Elimina un item."""
        return await self.repository.eliminar_item(item_id)

    async def reemplazar_items(
        self, requisicion_id: int, items: List[RequisicionItemCreate]
    ) -> List[RequisicionItem]:
        """
        Reemplaza todos los items de una requisición.
        Elimina los existentes y crea los nuevos.
        """
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        if not requisicion.puede_editarse():
            raise BusinessRuleError(MSG_REQUISICION_NO_EDITABLE)

        # Eliminar items existentes
        await self.repository.eliminar_items_requisicion(requisicion_id)

        # Crear nuevos items
        nuevos = []
        for item_data in items:
            item = RequisicionItem(**item_data.model_dump())
            nuevo = await self.repository.crear_item(requisicion_id, item)
            nuevos.append(nuevo)

        return nuevos

    # ==========================================
    # GESTIÓN DE PARTIDAS
    # ==========================================

    async def agregar_partida(
        self, requisicion_id: int, data: RequisicionPartidaCreate
    ) -> RequisicionPartida:
        """Agrega una partida a una requisición."""
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        if not requisicion.puede_editarse():
            raise BusinessRuleError(MSG_REQUISICION_NO_EDITABLE)

        partida = RequisicionPartida(**data.model_dump())
        return await self.repository.crear_partida(requisicion_id, partida)

    async def actualizar_partida(
        self, partida_id: int, data: RequisicionPartidaUpdate
    ) -> RequisicionPartida:
        """Actualiza una partida existente."""
        update_dict = data.model_dump(exclude_none=True)
        partida = RequisicionPartida(id=partida_id, **update_dict)
        return await self.repository.actualizar_partida(partida)

    async def eliminar_partida(self, partida_id: int) -> bool:
        """Elimina una partida."""
        return await self.repository.eliminar_partida(partida_id)

    async def reemplazar_partidas(
        self, requisicion_id: int, partidas: List[RequisicionPartidaCreate]
    ) -> List[RequisicionPartida]:
        """
        Reemplaza todas las partidas de una requisición.
        """
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        if not requisicion.puede_editarse():
            raise BusinessRuleError(MSG_REQUISICION_NO_EDITABLE)

        await self.repository.eliminar_partidas_requisicion(requisicion_id)

        nuevas = []
        for partida_data in partidas:
            partida = RequisicionPartida(**partida_data.model_dump())
            nueva = await self.repository.crear_partida(requisicion_id, partida)
            nuevas.append(nueva)

        return nuevas

    # ==========================================
    # TRANSICIONES DE ESTADO
    # ==========================================

    def _validar_transicion(
        self, estado_actual: EstadoRequisicion, estado_nuevo: EstadoRequisicion
    ) -> None:
        """
        Valida que la transición de estado sea válida.

        Raises:
            BusinessRuleError: Si la transición no es válida
        """
        estados_permitidos = TRANSICIONES_VALIDAS.get(estado_actual, [])
        if estado_nuevo not in estados_permitidos:
            raise BusinessRuleError(
                msg_transicion_invalida(estado_actual, estado_nuevo)
            )

    async def enviar(self, requisicion_id: int) -> Requisicion:
        """
        Envía una requisición (BORRADOR → ENVIADA).
        Valida que tenga items y partidas completos.

        Raises:
            BusinessRuleError: Si la transición no es válida o faltan datos
        """
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.ENVIADA
        )

        # Validar que tiene items
        if not requisicion.items:
            raise BusinessRuleError(MSG_REQUISICION_SIN_ITEMS)

        # Validar que tiene partidas
        if not requisicion.partidas:
            raise BusinessRuleError(MSG_REQUISICION_SIN_PARTIDAS)

        return await self.repository.cambiar_estado(
            requisicion_id, EstadoRequisicion.ENVIADA
        )

    async def iniciar_revision(self, requisicion_id: int) -> Requisicion:
        """Inicia revisión (ENVIADA → EN_REVISION)."""
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.EN_REVISION
        )
        return await self.repository.cambiar_estado(
            requisicion_id, EstadoRequisicion.EN_REVISION
        )

    async def aprobar(self, requisicion_id: int) -> Requisicion:
        """Aprueba una requisición (EN_REVISION → APROBADA)."""
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.APROBADA
        )
        return await self.repository.cambiar_estado(
            requisicion_id, EstadoRequisicion.APROBADA
        )

    async def adjudicar(
        self, requisicion_id: int, data: RequisicionAdjudicar
    ) -> Requisicion:
        """
        Adjudica una requisición a un proveedor (APROBADA → ADJUDICADA).

        Raises:
            BusinessRuleError: Si faltan datos de adjudicación
        """
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.ADJUDICADA
        )

        if not data.empresa_id:
            raise BusinessRuleError(MSG_ADJUDICAR_SIN_EMPRESA)
        if not data.fecha_adjudicacion:
            raise BusinessRuleError(MSG_ADJUDICAR_SIN_FECHA)

        # Actualizar empresa y fecha de adjudicación
        requisicion.empresa_id = data.empresa_id
        requisicion.fecha_adjudicacion = data.fecha_adjudicacion
        requisicion.estado = EstadoRequisicion.ADJUDICADA

        return await self.repository.actualizar(requisicion)

    async def marcar_contratada(
        self, requisicion_id: int, contrato_id: int
    ) -> Requisicion:
        """Marca como contratada (ADJUDICADA → CONTRATADA)."""
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.CONTRATADA
        )
        return await self.repository.cambiar_estado(
            requisicion_id, EstadoRequisicion.CONTRATADA
        )

    async def devolver(self, requisicion_id: int) -> Requisicion:
        """Devuelve a BORRADOR para corrección (ENVIADA/EN_REVISION → BORRADOR)."""
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.BORRADOR
        )
        return await self.repository.cambiar_estado(
            requisicion_id, EstadoRequisicion.BORRADOR
        )

    async def cancelar(self, requisicion_id: int, motivo: Optional[str] = None) -> Requisicion:
        """
        Cancela una requisición (desde cualquier estado no-final).

        Args:
            requisicion_id: ID de la requisición
            motivo: Motivo de cancelación (se guarda en observaciones)
        """
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.CANCELADA
        )

        # Guardar motivo en observaciones si se proporcionó
        if motivo:
            requisicion.observaciones = (
                f"{requisicion.observaciones}\n\nCancelada: {motivo}"
                if requisicion.observaciones
                else f"Cancelada: {motivo}"
            )
            requisicion.estado = EstadoRequisicion.CANCELADA
            return await self.repository.actualizar(requisicion)

        return await self.repository.cambiar_estado(
            requisicion_id, EstadoRequisicion.CANCELADA
        )

    # ==========================================
    # CONFIGURACIÓN
    # ==========================================

    async def obtener_valores_default(self) -> Dict[str, str]:
        """
        Obtiene los valores de configuración activos como dict clave:valor.

        Returns:
            Dict con clave -> valor de configuración
        """
        configs = await self.repository.obtener_configuracion()
        return {c.clave: c.valor for c in configs}

    async def obtener_configuracion(
        self, grupo: Optional[str] = None
    ) -> List[ConfiguracionRequisicion]:
        """Obtiene configuraciones, opcionalmente filtradas por grupo."""
        return await self.repository.obtener_configuracion(grupo)

    async def actualizar_configuracion(
        self, config_id: int, valor: str
    ) -> ConfiguracionRequisicion:
        """Actualiza el valor de una configuración."""
        return await self.repository.actualizar_configuracion(config_id, valor)

    # ==========================================
    # UTILIDADES
    # ==========================================

    async def generar_numero_requisicion(self) -> str:
        """
        Genera el siguiente número de requisición.
        Formato: REQ-SA-{AÑO}-{CONSECUTIVO:04d}
        """
        anio = date.today().year
        consecutivo = await self.repository.obtener_siguiente_consecutivo(anio)
        return Requisicion.generar_numero(anio, consecutivo)

    async def calcular_presupuesto_total(self, requisicion_id: int) -> Decimal:
        """Calcula el presupuesto total sumando todas las partidas."""
        partidas = await self.repository.obtener_partidas(requisicion_id)
        return sum(
            p.presupuesto_autorizado for p in partidas
        ) if partidas else Decimal('0')

    async def buscar_con_filtros(
        self,
        texto: Optional[str] = None,
        estado: Optional[str] = None,
        tipo_contratacion: Optional[str] = None,
        incluir_canceladas: bool = False,
        limite: int = 50,
        offset: int = 0,
    ) -> List[Requisicion]:
        """Busca requisiciones con filtros combinados."""
        return await self.repository.buscar_con_filtros(
            texto=texto,
            estado=estado,
            tipo_contratacion=tipo_contratacion,
            incluir_canceladas=incluir_canceladas,
            limite=limite,
            offset=offset,
        )


    # ==========================================
    # LUGARES DE ENTREGA
    # ==========================================

    async def obtener_lugares_entrega(self) -> List[LugarEntrega]:
        """Obtiene todos los lugares de entrega activos."""
        return await self.repository.obtener_lugares_entrega()

    async def crear_lugar_entrega(self, nombre: str) -> LugarEntrega:
        """Crea un nuevo lugar de entrega."""
        return await self.repository.crear_lugar_entrega(nombre.strip())

    async def eliminar_lugar_entrega(self, lugar_id: int) -> bool:
        """Elimina (desactiva) un lugar de entrega."""
        return await self.repository.eliminar_lugar_entrega(lugar_id)


# Singleton
requisicion_service = RequisicionService()
