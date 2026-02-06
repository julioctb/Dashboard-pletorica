"""
Configuracion para manejo de archivos en el sistema.

Define formatos permitidos, limites de tamano, calidad de compresion,
rutas de storage y limites por entidad.

Uso:
    from app.core.config.archivos_config import ArchivosConfig
"""

from typing import Optional, Set


class ArchivosConfig:
    """Configuracion para manejo de archivos en el sistema."""

    # === FORMATOS PERMITIDOS (MIME types) ===
    FORMATOS_IMAGEN: Set[str] = {"image/jpeg", "image/png", "image/jpg"}
    FORMATOS_DOCUMENTO: Set[str] = {"application/pdf"}
    FORMATOS_PERMITIDOS: Set[str] = FORMATOS_IMAGEN | FORMATOS_DOCUMENTO

    # === EXTENSIONES ===
    EXTENSIONES_IMAGEN: Set[str] = {".jpg", ".jpeg", ".png"}
    EXTENSIONES_DOCUMENTO: Set[str] = {".pdf"}

    # === LIMITES WEB (bytes) ===
    WEB_TAMANIO_MAX_IMAGEN_ORIGINAL: int = 5 * 1024 * 1024       # 5 MB
    WEB_TAMANIO_MAX_IMAGEN_FINAL: int = 2 * 1024 * 1024          # 2 MB despues de conversion
    WEB_TAMANIO_MAX_PDF: int = 10 * 1024 * 1024                  # 10 MB
    WEB_WEBP_CALIDAD: int = 85
    WEB_WEBP_CALIDAD_REDUCIDA: int = 70
    WEB_MAX_DIMENSION: int = 2560  # pixeles

    # === LIMITES CANTIDAD POR ENTIDAD ===
    MAX_ARCHIVOS_POR_ENTIDAD: dict = {
        "REQUISICION": 10,
        "REQUISICION_ITEM": 5,
        "REPORTE": 20,
        "REPORTE_ACTIVIDAD": 10,
        "CONTRATO": 10,
        "EMPLEADO": 5,
        "ENTREGABLE": 20,  # Puede tener múltiples fotos, reportes, etc.
        "PAGO": 2,        # Factura PDF y XML
    }

    # === COMPRESION PDF (Ghostscript) ===
    GS_CALIDAD_INICIAL: str = "/ebook"     # 150 dpi
    GS_CALIDAD_AGRESIVA: str = "/screen"   # 72 dpi

    # === SUPABASE STORAGE ===
    BUCKET_NAME: str = "archivos"

    # === RUTAS POR MODULO ===
    @classmethod
    def get_ruta_storage(
        cls,
        entidad_tipo: str,
        identificador: str,
        nombre_archivo: str,
        sub_identificador: Optional[str] = None,
    ) -> str:
        """
        Genera ruta para archivo en storage.

        Ejemplos:
        - requisiciones/REQ-SA-2025-0001/general/archivo.webp
        - requisiciones/REQ-SA-2025-0001/items/1/foto.webp
        - reportes/2025/01/RPT-0001/fotos/imagen.webp
        - contratos/CON-001/documento.pdf
        - empleados/EMP-001/foto.webp
        """
        rutas = {
            "REQUISICION": f"requisiciones/{identificador}/general/{nombre_archivo}",
            "REQUISICION_ITEM": f"requisiciones/{identificador}/items/{sub_identificador}/{nombre_archivo}",
            "REPORTE": f"reportes/{identificador}/{nombre_archivo}",
            "REPORTE_ACTIVIDAD": f"reportes/{identificador}/actividades/{sub_identificador}/{nombre_archivo}",
            "CONTRATO": f"contratos/{identificador}/{nombre_archivo}",
            "EMPLEADO": f"empleados/{identificador}/{nombre_archivo}",
            "ENTREGABLE": f"entregables/{identificador}/{sub_identificador}/{nombre_archivo}",
            # identificador = contrato_id, sub_identificador = entregable_id/tipo
            "PAGO": f"pagos/{identificador}/{nombre_archivo}",
            # identificador = pago_id
        }
        return rutas.get(entidad_tipo, f"otros/{identificador}/{nombre_archivo}")

    @classmethod
    def get_max_archivos(cls, entidad_tipo: str) -> int:
        """Obtiene el limite de archivos para un tipo de entidad."""
        return cls.MAX_ARCHIVOS_POR_ENTIDAD.get(entidad_tipo, 5)
