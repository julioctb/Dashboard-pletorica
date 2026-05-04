"""
Clase base abstracta para generadores de layout bancario.

Cada banco tiene su propio formato de archivo de dispersión.
Esta interfaz garantiza consistencia entre implementaciones.
"""
import unicodedata
from abc import ABC, abstractmethod

from app.core.validation import verificar_clabe


class LayoutBancario(ABC):
    """
    Interfaz común para generadores de layout bancario de nómina.

    Cada subclase implementa las especificaciones de formato del banco
    correspondiente: posiciones fijas, CSV, delimitado, etc.
    """

    @abstractmethod
    def generar(
        self,
        empleados: list[dict],
        config: dict,
        periodo: dict,
    ) -> tuple[str, bytes]:
        """
        Genera el archivo de layout para dispersión bancaria.

        Args:
            empleados: Lista de registros nominas_empleado con datos bancarios.
                       Cada dict tiene: nombre_empleado, clabe_destino,
                       total_neto, banco_destino, etc.
            config:    Configuración del banco (configuracion_bancos_empresa).
                       Tiene: nombre_banco, formato, cuenta_origen,
                       clabe_origen, referencia_pago.
            periodo:   Datos del período de nómina.
                       Tiene: nombre, fecha_inicio, fecha_fin, periodicidad.

        Returns:
            Tupla (nombre_archivo, contenido_bytes).
            El nombre incluye banco, período y extensión apropiada.
        """
        ...

    @abstractmethod
    def validar_datos(self, empleados: list[dict]) -> list[str]:
        """
        Valida que los datos bancarios de los empleados estén completos.

        Verifica CLABE de 18 dígitos, montos positivos y nombres presentes.

        Returns:
            Lista de mensajes de error. Vacía si todos los datos son válidos.
        """
        ...

    # =========================================================================
    # UTILIDADES COMPARTIDAS
    # =========================================================================

    @staticmethod
    def normalizar_texto(texto: str, longitud: int = 0) -> str:
        """
        Normaliza texto para compatibilidad con archivos bancarios ASCII.

        Elimina acentos, reemplaza ñ → N, y recorta/rellena a la longitud dada.
        """
        if not texto:
            return ' ' * longitud if longitud else ''
        # Descomponer caracteres Unicode (separa base + combinando)
        nfkd = unicodedata.normalize('NFKD', texto.upper())
        # Mantener solo caracteres ASCII imprimibles
        ascii_text = ''.join(
            c for c in nfkd
            if not unicodedata.combining(c) and ord(c) < 128
        )
        # Reemplazos manuales específicos
        ascii_text = ascii_text.replace('Ñ', 'N').replace('Ü', 'U')
        if longitud:
            return ascii_text[:longitud].ljust(longitud)
        return ascii_text

    @staticmethod
    def formatear_monto_centavos(monto: float, longitud: int) -> str:
        """
        Convierte monto a entero de centavos y lo formatea como cadena.

        Ej: 1234.56 → '000000000123456' (longitud 15)
        """
        centavos = round(monto * 100)
        return str(centavos).zfill(longitud)

    @staticmethod
    def formatear_monto_decimal(monto: float, decimales: int = 2) -> str:
        """
        Formatea monto con decimales fijos.

        Ej: 1234.5 → '1234.50'
        """
        return f"{monto:.{decimales}f}"

    @staticmethod
    def validar_clabe(clabe: str | None) -> bool:
        """Retorna True si la CLABE pasa formato y dígito verificador."""
        return verificar_clabe(clabe)
