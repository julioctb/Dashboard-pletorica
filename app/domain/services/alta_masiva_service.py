"""
Servicio de Alta Masiva de Personal.

Orquesta la validacion y procesamiento de archivos de carga masiva.
Fase 1: Validar archivo -> ResultadoValidacion (preview)
Fase 2: Procesar registros validados -> ResultadoProcesamiento (crear/reingresar)
"""

import re
import logging
from datetime import date
from typing import Optional

from app.domain.models.alta_masiva import (
    ResultadoFila,
    RegistroValidado,
    ResultadoValidacion,
    ResultadoProcesamiento,
    DetalleResultado,
)
from app.domain.models.empleado import EmpleadoCreate, EmpleadoUpdate
from app.domain.enums import EstatusEmpleado, GeneroEmpleado
from app.core.text_utils import (
    limpiar_espacios,
    normalizar_email,
    normalizar_mayusculas,
)
from app.core.validation import (
    normalizar_clabe_interbancaria,
    normalizar_cuenta_bancaria,
    normalizar_nombre_banco,
    validar_apellido_paterno_empleado,
    validar_clabe_empleado,
    validar_contacto_emergencia_nombre,
    validar_contacto_emergencia_telefono,
    validar_cuenta_bancaria_empleado,
    validar_curp_empleado,
    validar_email_empleado,
    validar_fecha_requerida,
    validar_nombre_empleado,
    validar_nss_empleado,
    validar_rfc_empleado,
    validar_telefono_empleado,
)
from app.core.validation.constants import BANCO_MAX
from app.core.validation.empresa_form_validators import validar_codigo_postal_empresa
from app.core.utils import parse_date_input
from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    BusinessRuleError,
    DatabaseError,
)
from app.domain.services.alta_masiva_parser import alta_masiva_parser

logger = logging.getLogger(__name__)


# Mapeo de genero desde texto del archivo
GENERO_ALIASES = {
    "masculino": GeneroEmpleado.MASCULINO,
    "femenino": GeneroEmpleado.FEMENINO,
    "m": GeneroEmpleado.MASCULINO,
    "f": GeneroEmpleado.FEMENINO,
    "h": GeneroEmpleado.MASCULINO,  # Hombre
    "hombre": GeneroEmpleado.MASCULINO,
    "mujer": GeneroEmpleado.FEMENINO,
}


class AltaMasivaService:
    """
    Servicio principal de alta masiva.

    Flujo:
    1. validar_archivo() -> Parsea, valida cada fila, detecta reingresos
    2. procesar() -> Crea empleados nuevos y reingresa existentes
    """

    async def validar_archivo(
        self, contenido: bytes, nombre_archivo: str, empresa_id: int
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
        registros, errores_globales = alta_masiva_parser.parsear(
            contenido, nombre_archivo
        )

        if errores_globales:
            # Error global -> todas las filas son error
            for error in errores_globales:
                resultado.errores.append(
                    RegistroValidado(
                        fila=0,
                        resultado=ResultadoFila.ERROR,
                        errores=[error],
                        mensaje=error,
                    )
                )
            return resultado

        resultado.total_filas = len(registros)

        # Validar la empresa destino existe
        try:
            from app.domain.services import empresa_service

            empresa = await empresa_service.obtener_por_id(empresa_id)
        except NotFoundError:
            resultado.errores.append(
                RegistroValidado(
                    fila=0,
                    resultado=ResultadoFila.ERROR,
                    errores=[f"Empresa con ID {empresa_id} no encontrada"],
                    mensaje=f"Empresa con ID {empresa_id} no encontrada",
                )
            )
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
        self, resultado_validacion: ResultadoValidacion, empresa_id: int
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

        from app.domain.services import empleado_service

        # Procesar altas nuevas
        for registro in resultado_validacion.validos:
            try:
                empleado_create = self._crear_empleado_create(
                    registro.datos, empresa_id
                )
                empleado = await empleado_service.crear(empleado_create)
                resultado.creados += 1
                resultado.detalles.append(
                    DetalleResultado(
                        fila=registro.fila,
                        curp=registro.curp,
                        resultado=ResultadoFila.VALIDO,
                        clave=empleado.clave,
                        mensaje=f"Creado: {empleado.clave}",
                    )
                )
            except (DuplicateError, BusinessRuleError, DatabaseError) as e:
                resultado.errores += 1
                resultado.detalles.append(
                    DetalleResultado(
                        fila=registro.fila,
                        curp=registro.curp,
                        resultado=ResultadoFila.ERROR,
                        mensaje=f"Error al crear: {str(e)}",
                    )
                )
            except Exception as e:
                resultado.errores += 1
                resultado.detalles.append(
                    DetalleResultado(
                        fila=registro.fila,
                        curp=registro.curp,
                        resultado=ResultadoFila.ERROR,
                        mensaje=f"Error inesperado: {str(e)}",
                    )
                )

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
                resultado.detalles.append(
                    DetalleResultado(
                        fila=registro.fila,
                        curp=registro.curp,
                        resultado=ResultadoFila.REINGRESO,
                        clave=empleado.clave,
                        mensaje=f"Reingresado: {empleado.clave}",
                    )
                )
            except (BusinessRuleError, DatabaseError) as e:
                resultado.errores += 1
                resultado.detalles.append(
                    DetalleResultado(
                        fila=registro.fila,
                        curp=registro.curp,
                        resultado=ResultadoFila.ERROR,
                        mensaje=f"Error al reingresar: {str(e)}",
                    )
                )
            except Exception as e:
                resultado.errores += 1
                resultado.detalles.append(
                    DetalleResultado(
                        fila=registro.fila,
                        curp=registro.curp,
                        resultado=ResultadoFila.ERROR,
                        mensaje=f"Error inesperado: {str(e)}",
                    )
                )

        return resultado

    # =========================================================================
    # VALIDACION DE REGISTROS INDIVIDUALES
    # =========================================================================

    async def _validar_registro(
        self, registro: dict, fila: int, empresa_id: int, curps_en_archivo: set
    ) -> RegistroValidado:
        """Valida un registro individual y determina si es alta nueva o reingreso."""
        errores = []

        # --- Validar CURP (obligatorio) ---
        curp = normalizar_mayusculas(registro.get("curp"))
        error = validar_curp_empleado(curp)
        if error:
            errores.append(error)
        elif curp in curps_en_archivo:
            errores.append(f"CURP {curp} duplicado en el archivo")

        # --- Validar nombre (obligatorio) ---
        nombre = limpiar_espacios(registro.get("nombre"))
        error = validar_nombre_empleado(nombre)
        if error:
            errores.append(error)

        # --- Validar apellido paterno (obligatorio) ---
        apellido_paterno = limpiar_espacios(registro.get("apellido_paterno"))
        error = validar_apellido_paterno_empleado(apellido_paterno)
        if error:
            errores.append(error)

        # --- Validar RFC (opcional) ---
        rfc = normalizar_mayusculas(registro.get("rfc"))
        error = validar_rfc_empleado(rfc)
        if error:
            errores.append(error)

        # --- Validar NSS (opcional) ---
        nss = limpiar_espacios(registro.get("nss"))
        error = validar_nss_empleado(nss)
        if error:
            errores.append(error)

        # --- Validar fecha nacimiento (opcional) ---
        fecha_nacimiento = (registro.get("fecha_nacimiento") or "").strip()
        error = self._validar_fecha_nacimiento_alta_masiva(fecha_nacimiento)
        if error:
            errores.append(error)

        # --- Validar fecha ingreso (opcional) ---
        fecha_ingreso = (registro.get("fecha_ingreso") or "").strip()
        if fecha_ingreso:
            error = validar_fecha_requerida(fecha_ingreso, "fecha de ingreso")
            if error:
                errores.append(error)

        # --- Validar genero (opcional) ---
        genero_raw = (registro.get("genero") or "").strip().lower()
        if genero_raw and genero_raw not in GENERO_ALIASES:
            errores.append(
                f"Genero invalido: '{registro.get('genero')}'. Use: Masculino, Femenino, M, F"
            )

        # --- Validar telefono (opcional) ---
        telefono = limpiar_espacios(registro.get("telefono"))
        error = validar_telefono_empleado(telefono)
        if error:
            errores.append(error)

        # --- Validar email (opcional) ---
        email = normalizar_email(registro.get("email"))
        error = validar_email_empleado(email)
        if error:
            errores.append(error)

        codigo_postal = limpiar_espacios(registro.get("codigo_postal"))
        error = validar_codigo_postal_empresa(codigo_postal)
        if error:
            errores.append(error)

        cuenta_bancaria = normalizar_cuenta_bancaria(registro.get("cuenta_bancaria"))
        error = validar_cuenta_bancaria_empleado(cuenta_bancaria)
        if error:
            errores.append(error)

        banco = normalizar_nombre_banco(registro.get("banco"))
        error = self._validar_banco_alta_masiva(banco)
        if error:
            errores.append(error)

        clabe = normalizar_clabe_interbancaria(registro.get("clabe_interbancaria"))
        error = validar_clabe_empleado(clabe)
        if error:
            errores.append(error)

        contacto_nombre = limpiar_espacios(registro.get("contacto_emergencia_nombre"))
        error = validar_contacto_emergencia_nombre(contacto_nombre)
        if error:
            errores.append(error)

        contacto_telefono = limpiar_espacios(
            registro.get("contacto_emergencia_telefono")
        )
        error = validar_contacto_emergencia_telefono(contacto_telefono)
        if error:
            errores.append(error)

        # Si hay errores de formato, retornar error sin consultar BD
        if errores:
            return RegistroValidado(
                fila=fila,
                resultado=ResultadoFila.ERROR,
                curp=curp,
                datos=registro,
                errores=errores,
                mensaje="; ".join(errores),
            )

        # --- Verificar si el CURP ya existe en BD ---
        from app.domain.services import empleado_service

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
            "empresa_id": empresa_id,
            "curp": normalizar_mayusculas(datos.get("curp")),
            "nombre": limpiar_espacios(datos.get("nombre")),
            "apellido_paterno": limpiar_espacios(datos.get("apellido_paterno")),
        }

        # Campos opcionales
        apellido_materno = limpiar_espacios(datos.get("apellido_materno"))
        if apellido_materno:
            kwargs["apellido_materno"] = apellido_materno

        rfc = normalizar_mayusculas(datos.get("rfc"))
        if rfc:
            kwargs["rfc"] = rfc

        nss = limpiar_espacios(datos.get("nss"))
        if nss:
            kwargs["nss"] = re.sub(r"[^0-9]", "", nss)

        fecha_nac = (datos.get("fecha_nacimiento") or "").strip()
        if fecha_nac:
            kwargs["fecha_nacimiento"] = self._parsear_fecha(fecha_nac)

        fecha_ingreso = (datos.get("fecha_ingreso") or "").strip()
        if fecha_ingreso:
            kwargs["fecha_ingreso"] = self._parsear_fecha(fecha_ingreso)

        genero_raw = (datos.get("genero") or "").strip().lower()
        if genero_raw and genero_raw in GENERO_ALIASES:
            kwargs["genero"] = GENERO_ALIASES[genero_raw]

        telefono = limpiar_espacios(datos.get("telefono"))
        if telefono:
            from app.core.validation.custom_validators import limpiar_telefono

            kwargs["telefono"] = limpiar_telefono(telefono)

        email = normalizar_email(datos.get("email"))
        if email:
            kwargs["email"] = email

        direccion = limpiar_espacios(datos.get("direccion"))
        if direccion:
            kwargs["direccion"] = direccion

        codigo_postal = limpiar_espacios(datos.get("codigo_postal"))
        if codigo_postal:
            kwargs["codigo_postal"] = codigo_postal

        cuenta_bancaria = normalizar_cuenta_bancaria(datos.get("cuenta_bancaria"))
        if cuenta_bancaria:
            kwargs["cuenta_bancaria"] = cuenta_bancaria

        banco = normalizar_nombre_banco(datos.get("banco"))
        if banco:
            kwargs["banco"] = banco

        clabe = normalizar_clabe_interbancaria(datos.get("clabe_interbancaria"))
        if clabe:
            kwargs["clabe_interbancaria"] = clabe

        contacto_emergencia = self._construir_contacto_emergencia(datos)
        if contacto_emergencia:
            kwargs["contacto_emergencia"] = contacto_emergencia

        return EmpleadoCreate(**kwargs)

    def _crear_empleado_update(self, datos: dict) -> Optional[EmpleadoUpdate]:
        """Crea un EmpleadoUpdate con los datos proporcionados (para reingresos)."""
        kwargs = {}

        rfc = normalizar_mayusculas(datos.get("rfc"))
        if rfc:
            kwargs["rfc"] = rfc

        nss = limpiar_espacios(datos.get("nss"))
        if nss:
            kwargs["nss"] = re.sub(r"[^0-9]", "", nss)

        telefono = limpiar_espacios(datos.get("telefono"))
        if telefono:
            from app.core.validation.custom_validators import limpiar_telefono

            kwargs["telefono"] = limpiar_telefono(telefono)

        email = normalizar_email(datos.get("email"))
        if email:
            kwargs["email"] = email

        direccion = limpiar_espacios(datos.get("direccion"))
        if direccion:
            kwargs["direccion"] = direccion

        codigo_postal = limpiar_espacios(datos.get("codigo_postal"))
        if codigo_postal:
            kwargs["codigo_postal"] = codigo_postal

        cuenta_bancaria = normalizar_cuenta_bancaria(datos.get("cuenta_bancaria"))
        if cuenta_bancaria:
            kwargs["cuenta_bancaria"] = cuenta_bancaria

        banco = normalizar_nombre_banco(datos.get("banco"))
        if banco:
            kwargs["banco"] = banco

        clabe = normalizar_clabe_interbancaria(datos.get("clabe_interbancaria"))
        if clabe:
            kwargs["clabe_interbancaria"] = clabe

        contacto_emergencia = self._construir_contacto_emergencia(datos)
        if contacto_emergencia:
            kwargs["contacto_emergencia"] = contacto_emergencia

        if kwargs:
            return EmpleadoUpdate(**kwargs)
        return None

    def _parsear_fecha(self, fecha_str: str) -> Optional[date]:
        """
        Parsea una fecha desde string.

        Soporta formatos:
        - DD/MM/AAAA
        - AAAA-MM-DD (ISO)
        - DD-MM-AAAA
        """
        return parse_date_input(fecha_str)

    @staticmethod
    def _validar_fecha_nacimiento_alta_masiva(fecha: str) -> str:
        """En carga masiva solo valida formato; no bloquea por edad historica."""
        if not fecha:
            return ""
        if parse_date_input(fecha) is None:
            return "Fecha de nacimiento invalida. Use formato DD/MM/AAAA"
        return ""

    @staticmethod
    def _validar_banco_alta_masiva(banco: str) -> str:
        """Permite nombres comerciales reales; solo limita longitud."""
        if banco and len(banco) > BANCO_MAX:
            return f"Banco no puede exceder {BANCO_MAX} caracteres"
        return ""

    def _construir_contacto_emergencia(self, datos: dict) -> str:
        """Construye el contacto separado o conserva el formato legado."""
        partes = [
            limpiar_espacios(datos.get("contacto_emergencia_nombre")),
            limpiar_espacios(datos.get("contacto_emergencia_telefono")),
            limpiar_espacios(datos.get("contacto_emergencia_parentesco")),
        ]
        if any(partes):
            return " / ".join(parte for parte in partes if parte)
        return limpiar_espacios(datos.get("contacto_emergencia"))


# Singleton
alta_masiva_service = AltaMasivaService()
