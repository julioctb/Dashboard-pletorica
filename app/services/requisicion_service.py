"""
Servicio de aplicación para gestión de requisiciones.

Patrón de manejo de errores:
- Las excepciones del repository se propagan (NotFoundError, DuplicateError, DatabaseError)
- El servicio NO captura excepciones, las deja subir al State
- Valida reglas de negocio y lanza BusinessRuleError cuando corresponde
"""
import logging
from datetime import date, datetime
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
    TRANSICIONES_VALIDAS,
)
from app.core.enums import EstadoRequisicion
from app.core.exceptions import BusinessRuleError
from app.core.error_messages import (
    MSG_REQUISICION_SIN_ITEMS,
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
            # Cargar items para contar totales
            items = await self.repository.obtener_items(req.id)
            total_items = len(items)

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
                empresa_nombre=empresa_nombre,
                creado_por=req.creado_por,
                aprobado_por=req.aprobado_por,
                fecha_aprobacion=req.fecha_aprobacion,
                created_at=req.created_at,
            ))

        return resumenes

    async def crear(
        self, data: RequisicionCreate, creado_por: Optional[str] = None
    ) -> Requisicion:
        """
        Crea una nueva requisición con número auto-generado.
        Permite borradores sin items ni partidas.

        Args:
            data: Datos de la requisición a crear
            creado_por: UUID del usuario que crea la requisición

        Raises:
            DuplicateError: Si el número ya existe
            DatabaseError: Si hay error de BD
        """
        # Construir entidad Requisicion (borrador sin número)
        requisicion_data = data.model_dump(exclude={'items'})
        requisicion_data['numero_requisicion'] = None
        requisicion_data['estado'] = EstadoRequisicion.BORRADOR

        # Auditoría: registrar quién crea
        if creado_por:
            requisicion_data['creado_por'] = creado_por

        # Construir items
        items = []
        for item_create in data.items:
            item_dict = item_create.model_dump()
            # Calcular subtotal
            if item_create.precio_unitario_estimado and item_create.cantidad:
                item_dict['subtotal_estimado'] = item_create.cantidad * item_create.precio_unitario_estimado
            items.append(RequisicionItem(**item_dict))

        requisicion = Requisicion(
            **requisicion_data,
            items=items,
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

    async def enviar(
        self, requisicion_id: int, enviado_por: Optional[str] = None
    ) -> Requisicion:
        """
        Envía una requisición (BORRADOR → ENVIADA).
        Valida items y notifica a usuarios autorizadores.

        Args:
            requisicion_id: ID de la requisición
            enviado_por: UUID del usuario que envía (para excluirlo de notificaciones)

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

        resultado = await self.repository.cambiar_estado(
            requisicion_id, EstadoRequisicion.ENVIADA
        )

        # Notificar a usuarios con permiso de autorizar
        await self._notificar_autorizadores(resultado, excluir_usuario_id=enviado_por)

        return resultado

    async def iniciar_revision(self, requisicion_id: int) -> Requisicion:
        """Inicia revisión (ENVIADA → EN_REVISION)."""
        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.EN_REVISION
        )
        return await self.repository.cambiar_estado(
            requisicion_id, EstadoRequisicion.EN_REVISION
        )

    async def aprobar(
        self, requisicion_id: int, aprobado_por: Optional[str] = None
    ) -> Requisicion:
        """
        Aprueba una requisición (EN_REVISION → APROBADA).

        Args:
            requisicion_id: ID de la requisición
            aprobado_por: UUID del usuario que aprueba

        Raises:
            BusinessRuleError: Si el aprobador es el mismo que el creador
            BusinessRuleError: Si no tiene permiso de autorizar requisiciones
        """
        # Validar permiso de autorización
        if aprobado_por:
            await self._validar_permiso(aprobado_por, 'requisiciones', 'autorizar')

        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.APROBADA
        )

        # Validar que el aprobador sea diferente al creador
        if aprobado_por and requisicion.creado_por and aprobado_por == requisicion.creado_por:
            raise BusinessRuleError(
                "El usuario que aprueba no puede ser el mismo que creó la requisición"
            )

        # Generar número oficial al aprobar (si aún no tiene)
        if not requisicion.numero_requisicion:
            numero = await self.generar_numero_requisicion()
            requisicion.numero_requisicion = numero

        # Actualizar campos de aprobación
        requisicion.estado = EstadoRequisicion.APROBADA
        if aprobado_por:
            requisicion.aprobado_por = aprobado_por
        requisicion.fecha_aprobacion = datetime.now()

        resultado = await self.repository.actualizar(requisicion)

        # Notificar al creador que su requisición fue aprobada
        if requisicion.creado_por:
            await self._notificar(
                usuario_id=requisicion.creado_por,
                titulo="Requisición aprobada",
                mensaje=f"Su requisición '{requisicion.objeto_contratacion[:50]}...' ha sido aprobada. Folio: {resultado.numero_requisicion}",
                tipo="requisicion_aprobada",
                entidad_id=requisicion_id,
            )

        return resultado

    async def rechazar(
        self,
        requisicion_id: int,
        comentario: str,
        rechazado_por: str,
    ) -> Requisicion:
        """
        Rechaza una requisición con comentario obligatorio.
        EN_REVISION → BORRADOR, incrementa numero_revision.

        Args:
            requisicion_id: ID de la requisición
            comentario: Comentario obligatorio del rechazo (min 10 chars)
            rechazado_por: UUID del usuario que rechaza

        Raises:
            BusinessRuleError: Si no tiene permiso, estado inválido o comentario muy corto
        """
        # Validar permiso de autorización
        await self._validar_permiso(rechazado_por, 'requisiciones', 'autorizar')

        if not comentario or len(comentario.strip()) < 10:
            raise BusinessRuleError(
                "El comentario de rechazo debe tener al menos 10 caracteres"
            )

        requisicion = await self.repository.obtener_por_id(requisicion_id)
        self._validar_transicion(
            EstadoRequisicion(requisicion.estado), EstadoRequisicion.BORRADOR
        )

        # Actualizar campos de rechazo
        requisicion.estado = EstadoRequisicion.BORRADOR
        requisicion.numero_revision = requisicion.numero_revision + 1
        requisicion.ultimo_comentario_rechazo = comentario.strip()
        requisicion.rechazado_por = rechazado_por
        requisicion.fecha_ultimo_rechazo = datetime.now()

        resultado = await self.repository.actualizar(requisicion)

        # Notificar al creador que su requisición fue rechazada
        if requisicion.creado_por:
            await self._notificar(
                usuario_id=requisicion.creado_por,
                titulo="Requisición rechazada",
                mensaje=f"Su requisición '{requisicion.objeto_contratacion[:50]}...' fue rechazada. Motivo: {comentario[:100]}",
                tipo="requisicion_rechazada",
                entidad_id=requisicion_id,
            )

        return resultado

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
    # VALIDACIÓN DE PERMISOS
    # ==========================================

    async def _validar_permiso(
        self, user_id: str, modulo: str, accion: str
    ) -> None:
        """
        Valida que el usuario tiene permiso para la acción en el módulo.

        Raises:
            BusinessRuleError: Si no tiene permiso
        """
        from app.services.user_service import user_service
        from uuid import UUID
        await user_service.validar_permiso(UUID(user_id), modulo, accion)

    # ==========================================
    # NOTIFICACIONES
    # ==========================================

    async def _notificar(
        self,
        usuario_id: Optional[str],
        titulo: str,
        mensaje: str,
        tipo: str,
        entidad_id: int = None,
    ) -> None:
        """
        Crea una notificacion de forma segura (no lanza excepciones).

        Args:
            usuario_id: UUID del usuario destinatario (None para notificacion admin)
            titulo: Título de la notificación
            mensaje: Mensaje descriptivo
            tipo: Tipo de notificación (requisicion_enviada, requisicion_aprobada, etc.)
            entidad_id: ID de la requisición
        """
        try:
            from app.services.notificacion_service import notificacion_service
            from app.entities.notificacion import NotificacionCreate

            notificacion = NotificacionCreate(
                usuario_id=usuario_id,
                titulo=titulo,
                mensaje=mensaje,
                tipo=tipo,
                entidad_tipo="REQUISICION",
                entidad_id=entidad_id,
            )
            await notificacion_service.crear(notificacion)

        except Exception as e:
            # Las notificaciones no deben bloquear el flujo principal
            logger.error(f"Error creando notificacion de requisicion: {e}")

    async def _notificar_autorizadores(
        self,
        requisicion: Requisicion,
        excluir_usuario_id: Optional[str] = None,
    ) -> None:
        """
        Notifica a todos los usuarios con permiso de autorizar requisiciones.

        Args:
            requisicion: Requisición enviada
            excluir_usuario_id: Usuario a excluir (el que envió)
        """
        try:
            from app.services.user_service import user_service

            usuarios = await user_service.obtener_usuarios_con_permiso(
                modulo='requisiciones',
                accion='autorizar',
            )

            for usuario in usuarios:
                # No notificar al mismo usuario que envió
                if excluir_usuario_id and str(usuario.id) == excluir_usuario_id:
                    continue

                await self._notificar(
                    usuario_id=str(usuario.id),
                    titulo="Requisición pendiente de revisión",
                    mensaje=f"La requisición '{requisicion.objeto_contratacion[:50]}...' está pendiente de revisión.",
                    tipo="requisicion_enviada",
                    entidad_id=requisicion.id,
                )

        except Exception as e:
            logger.error(f"Error notificando autorizadores: {e}")

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
