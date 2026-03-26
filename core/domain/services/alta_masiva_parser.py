"""
Servicio de parseo para Alta Masiva de Personal.

Parsea archivos CSV y Excel, normaliza headers y extrae
los registros como diccionarios listos para validacion.
"""
import csv
import io
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Limites del archivo
MAX_FILAS = 500
MAX_BYTES = 5 * 1024 * 1024  # 5MB

# Columnas requeridas (nombre normalizado -> variaciones aceptadas)
COLUMNAS_REQUERIDAS = {'curp', 'nombre', 'apellido_paterno'}

# Mapeo de variaciones de headers a nombre normalizado
HEADER_ALIASES = {
    # CURP
    'curp': 'curp',
    'c.u.r.p.': 'curp',
    'clave_unica': 'curp',
    'clave unica': 'curp',
    # Nombre
    'nombre': 'nombre',
    'nombres': 'nombre',
    'nombre(s)': 'nombre',
    # Apellido paterno
    'apellido_paterno': 'apellido_paterno',
    'apellido paterno': 'apellido_paterno',
    'paterno': 'apellido_paterno',
    'primer apellido': 'apellido_paterno',
    'ap_paterno': 'apellido_paterno',
    # Apellido materno
    'apellido_materno': 'apellido_materno',
    'apellido materno': 'apellido_materno',
    'materno': 'apellido_materno',
    'segundo apellido': 'apellido_materno',
    'ap_materno': 'apellido_materno',
    # RFC
    'rfc': 'rfc',
    'r.f.c.': 'rfc',
    # NSS
    'nss': 'nss',
    'n.s.s.': 'nss',
    'numero_seguro_social': 'nss',
    'numero seguro social': 'nss',
    'seguro social': 'nss',
    # Fecha nacimiento
    'fecha_nacimiento': 'fecha_nacimiento',
    'fecha nacimiento': 'fecha_nacimiento',
    'fecha de nacimiento': 'fecha_nacimiento',
    'nacimiento': 'fecha_nacimiento',
    'fec_nacimiento': 'fecha_nacimiento',
    # Genero
    'genero': 'genero',
    'sexo': 'genero',
    'género': 'genero',
    # Telefono
    'telefono': 'telefono',
    'teléfono': 'telefono',
    'tel': 'telefono',
    'celular': 'telefono',
    # Email
    'email': 'email',
    'correo': 'email',
    'correo electronico': 'email',
    'correo electrónico': 'email',
    'e-mail': 'email',
    # Direccion
    'direccion': 'direccion',
    'dirección': 'direccion',
    'domicilio': 'direccion',
    # Contacto emergencia
    'contacto_emergencia': 'contacto_emergencia',
    'contacto emergencia': 'contacto_emergencia',
    'contacto de emergencia': 'contacto_emergencia',
    'emergencia': 'contacto_emergencia',
}

# Columnas validas (todas las que el sistema reconoce)
COLUMNAS_VALIDAS = set(HEADER_ALIASES.values())


def _normalizar_header(header: str) -> str:
    """Normaliza un header: minusculas, sin acentos comunes, strip."""
    h = header.strip().lower()
    # Remover acentos comunes en headers
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n',
    }
    for original, reemplazo in reemplazos.items():
        # Solo para busqueda en aliases, no para genero que necesita ñ
        pass
    return h


class AltaMasivaParser:
    """
    Parser de archivos CSV/Excel para alta masiva.

    Soporta:
    - CSV (delimitador: coma o punto y coma, con/sin BOM)
    - Excel (.xlsx, .xls) via openpyxl
    """

    def parsear(self, contenido: bytes, nombre_archivo: str) -> Tuple[List[dict], List[str]]:
        """
        Parsea un archivo y retorna registros como diccionarios.

        Args:
            contenido: Bytes del archivo
            nombre_archivo: Nombre original del archivo (para detectar tipo)

        Returns:
            Tupla (registros, errores_globales)
            - registros: Lista de dicts con claves normalizadas
            - errores_globales: Errores que afectan a todo el archivo

        Raises:
            ValueError: Si el archivo excede los limites
        """
        errores = []

        # Validar tamano
        if len(contenido) > MAX_BYTES:
            mb = len(contenido) / (1024 * 1024)
            return [], [f"Archivo demasiado grande ({mb:.1f}MB). Maximo permitido: 5MB"]

        if len(contenido) == 0:
            return [], ["Archivo vacio"]

        # Detectar tipo y parsear
        nombre_lower = nombre_archivo.lower()
        if nombre_lower.endswith('.csv'):
            registros, errores = self._parsear_csv(contenido)
        elif nombre_lower.endswith(('.xlsx', '.xls')):
            registros, errores = self._parsear_excel(contenido)
        else:
            return [], [f"Formato no soportado: {nombre_archivo}. Use CSV o Excel (.xlsx)"]

        if errores:
            return [], errores

        # Validar cantidad de filas
        if len(registros) > MAX_FILAS:
            return [], [f"Demasiadas filas ({len(registros)}). Maximo permitido: {MAX_FILAS}"]

        if len(registros) == 0:
            return [], ["El archivo no contiene registros (solo headers o vacio)"]

        return registros, []

    def _parsear_csv(self, contenido: bytes) -> Tuple[List[dict], List[str]]:
        """Parsea un archivo CSV."""
        # Detectar encoding (con/sin BOM)
        if contenido[:3] == b'\xef\xbb\xbf':
            texto = contenido[3:].decode('utf-8')
        else:
            try:
                texto = contenido.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    texto = contenido.decode('latin-1')
                except UnicodeDecodeError:
                    return [], ["No se pudo decodificar el archivo. Use codificacion UTF-8"]

        # Detectar delimitador
        primera_linea = texto.split('\n')[0] if '\n' in texto else texto
        delimitador = ';' if ';' in primera_linea else ','

        try:
            reader = csv.DictReader(io.StringIO(texto), delimiter=delimitador)

            if not reader.fieldnames:
                return [], ["No se encontraron headers en el archivo CSV"]

            # Normalizar headers
            headers_normalizados, headers_desconocidos = self._normalizar_headers(
                list(reader.fieldnames)
            )

            # Verificar columnas requeridas
            error_columnas = self._verificar_columnas_requeridas(headers_normalizados)
            if error_columnas:
                return [], [error_columnas]

            # Parsear filas
            registros = []
            for i, row in enumerate(reader):
                registro = {}
                for header_original, valor in row.items():
                    header_norm = _normalizar_header(header_original)
                    nombre_campo = HEADER_ALIASES.get(header_norm)
                    if nombre_campo:
                        registro[nombre_campo] = (valor or '').strip()
                # Solo agregar si tiene algun dato
                if any(v for v in registro.values()):
                    registros.append(registro)

            return registros, []

        except csv.Error as e:
            return [], [f"Error leyendo CSV: {str(e)}"]

    def _parsear_excel(self, contenido: bytes) -> Tuple[List[dict], List[str]]:
        """Parsea un archivo Excel (.xlsx/.xls)."""
        try:
            import openpyxl
        except ImportError:
            return [], ["Libreria openpyxl no instalada. Instale con: pip install openpyxl"]

        try:
            wb = openpyxl.load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
            ws = wb.active

            if ws is None:
                return [], ["El archivo Excel no tiene hojas activas"]

            rows = list(ws.iter_rows(values_only=True))
            if len(rows) < 2:
                return [], ["El archivo Excel no contiene datos (solo headers o vacio)"]

            # Primera fila = headers
            headers_raw = [str(h).strip() if h else '' for h in rows[0]]

            # Normalizar headers
            headers_normalizados, headers_desconocidos = self._normalizar_headers(headers_raw)

            # Verificar columnas requeridas
            error_columnas = self._verificar_columnas_requeridas(headers_normalizados)
            if error_columnas:
                return [], [error_columnas]

            # Parsear filas de datos
            registros = []
            for row in rows[1:]:
                registro = {}
                for idx, valor in enumerate(row):
                    if idx < len(headers_raw):
                        header_norm = _normalizar_header(headers_raw[idx])
                        nombre_campo = HEADER_ALIASES.get(header_norm)
                        if nombre_campo:
                            # Convertir valor a string
                            if valor is None:
                                registro[nombre_campo] = ''
                            else:
                                registro[nombre_campo] = str(valor).strip()
                # Solo agregar si tiene algun dato
                if any(v for v in registro.values()):
                    registros.append(registro)

            wb.close()
            return registros, []

        except Exception as e:
            return [], [f"Error leyendo Excel: {str(e)}"]

    def _normalizar_headers(self, headers: List[str]) -> Tuple[dict, List[str]]:
        """
        Normaliza headers del archivo a nombres de campo del sistema.

        Returns:
            Tupla (mapeo_normalizado, headers_desconocidos)
        """
        mapeo = {}
        desconocidos = []

        for header in headers:
            if not header:
                continue
            header_norm = _normalizar_header(header)
            nombre_campo = HEADER_ALIASES.get(header_norm)
            if nombre_campo:
                mapeo[header] = nombre_campo
            else:
                desconocidos.append(header)

        return mapeo, desconocidos

    def _verificar_columnas_requeridas(self, headers_normalizados: dict) -> str:
        """Verifica que esten presentes todas las columnas requeridas."""
        campos_presentes = set(headers_normalizados.values())
        faltantes = COLUMNAS_REQUERIDAS - campos_presentes
        if faltantes:
            faltantes_str = ', '.join(sorted(faltantes))
            return f"Columnas requeridas faltantes: {faltantes_str}"
        return ""


# Singleton
alta_masiva_parser = AltaMasivaParser()
