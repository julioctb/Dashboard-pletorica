"""
Servicio de Alta Masiva de Personal.

Orquesta la validacion y procesamiento de archivos de carga masiva.
Fase 1: Validar archivo -> ResultadoValidacion (preview)
Fase 2: Procesar registros validados -> ResultadoProcesamiento (crear/reingresar)
"""
import re
import logging
from datetime import datetime
from typing import Optional

from app.entities.alta_masiva import (
    ResultadoFila,
    RegistroValidado,
    ResultadoValidacion,
    ResultadoProcesamiento,
    DetalleResultado,
)
from app.entities.empleado import EmpleadoCreate, EmpleadoUpdate
from app.core.enums import EstatusEmpleado, GeneroEmpleado
from app.core.text_utils import limpiar_espacios, normalizar_email, normalizar_mayusculas
from app.core.validation.custom_validators import limpiar_telefono
from app.core.validation import (
    CURP_PATTERN,
    CURP_LEN,
    RFC_PERSONA_PATTERN,
    RFC_PERSONA_LEN,
    NSS_PATTERN,
    NSS_LEN,
)
from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    BusinessRuleError,
    DatabaseError,
)
from app.services.alta_masiva_parser import alta_masiva_parser

logger = logging.getLogger(__name__)


# Mapeo de genero desde texto del archivo
GENERO_ALIASES = {
    'masculino': GeneroEmpleado.MASCULINO,
    'femenino': GeneroEmpleado.FEMENINO,
    'm': GeneroEmpleado.MASCULINO,
    'f': GeneroEmpleado.FEMENINO,
    'h': GeneroEmpleado.MASCULINO,  # Hombre
    'hombre': GeneroEmpleado.MASCULINO,
    'mujer': GeneroEmpleado.FEMENINO,
}


class AltaMasivaService:
    """
    Servicio principal de alta masiva.

    Flujo:
    1. validar_archivo() -> Parsea, valida cada fila, detecta reingresos
    2. procesar() -> Crea empleados nuevos y reingresa existentes
    """

    async def validar_archivo(
        self,
        contenido: bytes,
        nombre_archivo: str,
        empresa_id: int
    ) -> ResultadoValidacion:
        """
        Fase 1: Parsea y valida el archivo sin crear nada en BD.

        Args:
            contenido: Bytes del archivo (CSV o Excel)
            nombre_archivo: Nombre original del archivo
            empresa_id: ID de la empresa destino

        Returns:
            ResultadoValidacion con registros clasificados
        """
        resultado = ResultadoValidacion()

        # Parsear archivo
        registros, errores_globales = alta_masiva_parser.parsear(contenido, nombre_archivo)

        if errores_globales:
            # Error global -> todas las filas son error
            for error in errores_globales:
                resultado.errores.append(RegistroValidado(
                    fila=0,
                    resultado=ResultadoFila.ERROR,
                    errores=[error],
                    mensaje=error,
                ))
            return resultado

        resultado.total_filas = len(registros)

        # Validar la empresa destino existe
        try:
            from app.services import empresa_service
            empresa = await empresa_service.obtener_por_id(empresa_id)
        except NotFoundError:
            resultado.errores.append(RegistroValidado(
                fila=0,
                resultado=ResultadoFila.ERROR,
                errores=[f"Empresa con ID {empresa_id} no encontrada"],
                mensaje=f"Empresa con ID {empresa_id} no encontrada",
            ))
            return resultado

        # Validar cada registro
        curps_en_archivo = set()
        for i, registro in enumerate(registros):
            fila = i + 2  # +2 porque fila 1 es header, i empieza en 0
            validado = await self._validar_registro(
                registro, fila, empresa_id, curps_en_archivo
            )

            if validado.resultado == ResultadoFila.VALIDO:
                resultado.validos.append(validado)
            elif validado.resultado == ResultadoFila.REINGRESO:
                resultado.reingresos.append(validado)
            else:
                resultado.errores.append(validado)

            # Trackear CURPs para detectar duplicados dentro del archivo
            if validado.curp:
                curps_en_archivo.add(validado.curp)

        return resultado

    async def procesar(
        self,
        resultado_validacion: ResultadoValidacion,
        empresa_id: int
    ) -> ResultadoProcesamiento:
        """
        Fase 2: Procesa los registros validados (crea y reingresa).

        Args:
            resultado_validacion: Resultado de validar_archivo()
            empresa_id: ID de la empresa destino

        Returns:
            ResultadoProcesamiento con contadores y detalles
        """
        resultado = ResultadoProcesamiento()

        from app.services import empleado_service

        # Procesar altas nuevas
        for registro in resultado_validacion.validos:
            try:
                empleado_create = self._crear_empleado_create(registro.datos, empresa_id)
                empleado = await empleado_service.crear(empleado_create)
                resultado.creados += 1
                resultado.detalles.append(DetalleResultado(
                    fila=registro.fila,
                    curp=registro.curp,
                    resultado=ResultadoFila.VALIDO,
                    clave=empleado.clave,
                    mensaje=f"Creado: {empleado.clave}",
                ))
            except (DuplicateError, BusinessRuleError, DatabaseError) as e:
                resultado.errores += 1
                resultado.detalles.append(DetalleResultado(
                    fila=registro.fila,
                    curp=registro.curp,
                    resultado=ResultadoFila.ERROR,
                    mensaje=f"Error al crear: {str(e)}",
                ))
            except Exception as e:
                resultado.errores += 1
                resultado.detalles.append(DetalleResultado(
                    fila=registro.fila,
                    curp=registro.curp,
                    resultado=ResultadoFila.ERROR,
                    mensaje=f"Error inesperado: {str(e)}",
                ))

        # Procesar reingresos
        for registro in resultado_validacion.reingresos:
            try:
                datos_update = self._crear_empleado_update(registro.datos)
                empleado = await empleado_service.reingresar(
                    empleado_id=registro.empleado_existente_id,
                    nueva_empresa_id=empresa_id,
                    datos_actualizados=datos_update,
                )
                resultado.reingresados += 1
                resultado.detalles.append(DetalleResultado(
                    fila=registro.fila,
                    curp=registro.curp,
                    resultado=ResultadoFila.REINGRESO,
                    clave=empleado.clave,
                    mensaje=f"Reingresado: {empleado.clave}",
                ))
            except (BusinessRuleError, DatabaseError) as e:
                resultado.errores += 1
                resultado.detalles.append(DetalleResultado(
                    fila=registro.fila,
                    curp=registro.curp,
                    resultado=ResultadoFila.ERROR,
                    mensaje=f"Error al reingresar: {str(e)}",
                ))
            except Exception as e:
                resultado.errores += 1
                resultado.detalles.append(DetalleResultado(
                    fila=registro.fila,
                    curp=registro.curp,
                    resultado=ResultadoFila.ERROR,
                    mensaje=f"Error inesperado: {str(e)}",
                ))

        return resultado

    # =========================================================================
    # VALIDACION DE REGISTROS INDIVIDUALES
    # =========================================================================

    async def _validar_registro(
        self,
        registro: dict,
        fila: int,
        empresa_id: int,
        curps_en_archivo: set
    ) -> RegistroValidado:
        """Valida un registro individual y determina si es alta nueva o reingreso."""
        errores = []

        # --- Validar CURP (obligatorio) ---
        curp = normalizar_mayusculas(registro.get('curp'))
        if not curp:
            errores.append("CURP es obligatorio")
        elif len(curp) != CURP_LEN:
            errores.append(f"CURP debe tener {CURP_LEN} caracteres (tiene {len(curp)})")
        elif not re.match(CURP_PATTERN, curp):
            errores.append("CURP con formato invalido")
        elif curp in curps_en_archivo:
            errores.append(f"CURP {curp} duplicado en el archivo")

        # --- Validar nombre (obligatorio) ---
        nombre = limpiar_espacios(registro.get('nombre'))
        if not nombre:
            errores.append("Nombre es obligatorio")
        elif len(nombre) < 2:
            errores.append("Nombre debe tener al menos 2 caracteres")

        # --- Validar apellido paterno (obligatorio) ---
        apellido_paterno = limpiar_espacios(registro.get('apellido_paterno'))
        if not apellido_paterno:
            errores.append("Apellido paterno es obligatorio")
        elif len(apellido_paterno) < 2:
            errores.append("Apellido paterno debe tener al menos 2 caracteres")

        # --- Validar RFC (opcional) ---
        rfc = normalizar_mayusculas(registro.get('rfc'))
        if rfc:
            if len(rfc) != RFC_PERSONA_LEN:
                errores.append(f"RFC debe tener {RFC_PERSONA_LEN} caracteres (tiene {len(rfc)})")
            elif not re.match(RFC_PERSONA_PATTERN, rfc):
                errores.append("RFC con formato invalido")

        # --- Validar NSS (opcional) ---
        nss = limpiar_espacios(registro.get('nss'))
        if nss:
            nss_limpio = re.sub(r'[^0-9]', '', nss)
            if not re.match(NSS_PATTERN, nss_limpio):
                errores.append(f"NSS debe tener {NSS_LEN} digitos numericos")

        # --- Validar fecha nacimiento (opcional) ---
        fecha_nacimiento = (registro.get('fecha_nacimiento') or '').strip()
        if fecha_nacimiento:
            if not self._parsear_fecha(fecha_nacimiento):
                errores.append("Fecha de nacimiento invalida. Use formato DD/MM/AAAA o AAAA-MM-DD")

        # --- Validar genero (opcional) ---
        genero_raw = (registro.get('genero') or '').strip().lower()
        if genero_raw and genero_raw not in GENERO_ALIASES:
            errores.append(f"Genero invalido: '{registro.get('genero')}'. Use: Masculino, Femenino, M, F")

        # --- Validar telefono (opcional) ---
        telefono = limpiar_espacios(registro.get('telefono'))
        if telefono:
            tel_limpio = limpiar_telefono(telefono)
            if len(tel_limpio) != 10:
                errores.append("Telefono debe tener 10 digitos")

        # --- Validar email (opcional) ---
        email = normalizar_email(registro.get('email'))
        if email:
            if '@' not in email or '.' not in email:
                errores.append("Email con formato invalido")

        # Si hay errores de formato, retornar error sin consultar BD
        if errores:
            return RegistroValidado(
                fila=fila,
                resultado=ResultadoFila.ERROR,
                curp=curp,
                datos=registro,
                errores=errores,
                mensaje='; '.join(errores),
            )

        # --- Verificar si el CURP ya existe en BD ---
        from app.services import empleado_service
        empleado_existente = await empleado_service.obtener_por_curp(curp)

        if empleado_existente:
            # Verificar restriccion
            if empleado_existente.is_restricted:
                return RegistroValidado(
                    fila=fila,
                    resultado=ResultadoFila.ERROR,
                    curp=curp,
                    datos=registro,
                    errores=["Empleado con restriccion activa en el sistema"],
                    mensaje="Empleado con restriccion activa en el sistema",
                )

            # Verificar si ya esta activo en la misma empresa
            if (
                empleado_existente.estatus == EstatusEmpleado.ACTIVO
                and empleado_existente.empresa_id == empresa_id
            ):
                return RegistroValidado(
                    fila=fila,
                    resultado=ResultadoFila.ERROR,
                    curp=curp,
                    datos=registro,
                    empleado_existente_id=empleado_existente.id,
                    errores=["Empleado ya esta activo en esta empresa"],
                    mensaje="Empleado ya esta activo en esta empresa",
                )

            # Es reingreso: empleado existe pero en otra empresa o inactivo
            return RegistroValidado(
                fila=fila,
                resultado=ResultadoFila.REINGRESO,
                curp=curp,
                datos=registro,
                empleado_existente_id=empleado_existente.id,
                empresa_anterior_id=empleado_existente.empresa_id,
                mensaje=f"Reingreso: {empleado_existente.clave} ({empleado_existente.nombre_completo()})",
            )

        # Empleado nuevo
        return RegistroValidado(
            fila=fila,
            resultado=ResultadoFila.VALIDO,
            curp=curp,
            datos=registro,
            mensaje="Registro valido para alta",
        )

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _crear_empleado_create(self, datos: dict, empresa_id: int) -> EmpleadoCreate:
        """Crea un EmpleadoCreate a partir de los datos parseados."""
        kwargs = {
            'empresa_id': empresa_id,
            'curp': normalizar_mayusculas(datos.get('curp')),
            'nombre': limpiar_espacios(datos.get('nombre')),
            'apellido_paterno': limpiar_espacios(datos.get('apellido_paterno')),
        }

        # Campos opcionales
        apellido_materno = limpiar_espacios(datos.get('apellido_materno'))
        if apellido_materno:
            kwargs['apellido_materno'] = apellido_materno

        rfc = normalizar_mayusculas(datos.get('rfc'))
        if rfc:
            kwargs['rfc'] = rfc

        nss = limpiar_espacios(datos.get('nss'))
        if nss:
            kwargs['nss'] = re.sub(r'[^0-9]', '', nss)

        fecha_nac = (datos.get('fecha_nacimiento') or '').strip()
        if fecha_nac:
            kwargs['fecha_nacimiento'] = self._parsear_fecha(fecha_nac)

        genero_raw = (datos.get('genero') or '').strip().lower()
        if genero_raw and genero_raw in GENERO_ALIASES:
            kwargs['genero'] = GENERO_ALIASES[genero_raw]

        telefono = limpiar_espacios(datos.get('telefono'))
        if telefono:
            kwargs['telefono'] = limpiar_telefono(telefono)

        email = normalizar_email(datos.get('email'))
        if email:
            kwargs['email'] = email

        direccion = limpiar_espacios(datos.get('direccion'))
        if direccion:
            kwargs['direccion'] = direccion

        contacto_emergencia = limpiar_espacios(datos.get('contacto_emergencia'))
        if contacto_emergencia:
            kwargs['contacto_emergencia'] = contacto_emergencia

        return EmpleadoCreate(**kwargs)

    def _crear_empleado_update(self, datos: dict) -> Optional[EmpleadoUpdate]:
        """Crea un EmpleadoUpdate con los datos proporcionados (para reingresos)."""
        kwargs = {}

        rfc = normalizar_mayusculas(datos.get('rfc'))
        if rfc:
            kwargs['rfc'] = rfc

        nss = limpiar_espacios(datos.get('nss'))
        if nss:
            kwargs['nss'] = re.sub(r'[^0-9]', '', nss)

        telefono = limpiar_espacios(datos.get('telefono'))
        if telefono:
            kwargs['telefono'] = limpiar_telefono(telefono)

        email = normalizar_email(datos.get('email'))
        if email:
            kwargs['email'] = email

        direccion = limpiar_espacios(datos.get('direccion'))
        if direccion:
            kwargs['direccion'] = direccion

        contacto_emergencia = limpiar_espacios(datos.get('contacto_emergencia'))
        if contacto_emergencia:
            kwargs['contacto_emergencia'] = contacto_emergencia

        if kwargs:
            return EmpleadoUpdate(**kwargs)
        return None

    def _parsear_fecha(self, fecha_str: str) -> Optional['date']:
        """
        Parsea una fecha desde string.

        Soporta formatos:
        - DD/MM/AAAA
        - AAAA-MM-DD (ISO)
        - DD-MM-AAAA
        """
        from datetime import date as date_type

        formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']
        for fmt in formatos:
            try:
                return datetime.strptime(fecha_str.strip(), fmt).date()
            except ValueError:
                continue
        return None


# Singleton
alta_masiva_service = AltaMasivaService()
