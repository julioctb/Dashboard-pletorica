"""
Compresor de imagenes a formato WebP usando Pillow.

Convierte JPG/PNG a WebP con redimensionado opcional y ajuste
automatico de calidad si el resultado excede el limite.

Uso:
    from app.core.compresores import ImagenCompressor

    webp_bytes, metadata = ImagenCompressor.comprimir_imagen(
        imagen_bytes, ".jpg"
    )
"""

from io import BytesIO
from typing import Tuple

from PIL import Image

from app.core.config.archivos_config import ArchivosConfig


class ImagenCompressor:
    """Compresor de imagenes a formato WebP usando Pillow."""

    @staticmethod
    def convertir_a_webp(
        imagen_bytes: bytes,
        calidad: int = ArchivosConfig.WEB_WEBP_CALIDAD,
        max_dimension: int = ArchivosConfig.WEB_MAX_DIMENSION,
    ) -> bytes:
        """
        Convierte una imagen a formato WebP con redimensionado opcional.

        Args:
            imagen_bytes: Contenido de la imagen original (JPG/PNG)
            calidad: Calidad de compresion (1-100)
            max_dimension: Dimension maxima (ancho o alto)

        Returns:
            Imagen en formato WebP como bytes.
        """
        img = Image.open(BytesIO(imagen_bytes))

        # Redimensionar si excede la dimension maxima
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convertir a RGB si tiene canal alpha (PNG con transparencia)
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            background.paste(
                img, mask=img.split()[-1] if img.mode == "RGBA" else None
            )
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        output = BytesIO()
        img.save(output, format="WEBP", quality=calidad, method=6)
        return output.getvalue()

    @staticmethod
    def comprimir_imagen(
        imagen_bytes: bytes,
        formato_original: str,
    ) -> Tuple[bytes, dict]:
        """
        Comprime una imagen a WebP, ajustando calidad si excede el limite.

        Args:
            imagen_bytes: Contenido de la imagen original
            formato_original: Extension original (.jpg, .png)

        Returns:
            Tupla (imagen_comprimida, metadata).
        """
        tamanio_original = len(imagen_bytes)

        metadata = {
            "tamanio_original": tamanio_original,
            "tamanio_final": tamanio_original,
            "formato_original": formato_original.lower().lstrip("."),
            "formato_final": "webp",
            "comprimido": True,
            "calidad_usada": ArchivosConfig.WEB_WEBP_CALIDAD,
            "reduccion_porcentaje": 0,
        }

        # Primer intento con calidad alta
        webp_bytes = ImagenCompressor.convertir_a_webp(
            imagen_bytes, ArchivosConfig.WEB_WEBP_CALIDAD
        )

        # Si excede el limite, reducir calidad
        if len(webp_bytes) > ArchivosConfig.WEB_TAMANIO_MAX_IMAGEN_FINAL:
            webp_bytes = ImagenCompressor.convertir_a_webp(
                imagen_bytes, ArchivosConfig.WEB_WEBP_CALIDAD_REDUCIDA
            )
            metadata["calidad_usada"] = ArchivosConfig.WEB_WEBP_CALIDAD_REDUCIDA

        metadata["tamanio_final"] = len(webp_bytes)
        metadata["reduccion_porcentaje"] = round(
            (1 - len(webp_bytes) / tamanio_original) * 100, 1
        )

        return webp_bytes, metadata

    @staticmethod
    def validar_imagen(imagen_bytes: bytes) -> bool:
        """Valida que el contenido sea una imagen valida."""
        try:
            img = Image.open(BytesIO(imagen_bytes))
            img.verify()
            return True
        except Exception:
            return False

    @staticmethod
    def obtener_dimensiones(imagen_bytes: bytes) -> Tuple[int, int]:
        """Obtiene las dimensiones de una imagen (width, height)."""
        img = Image.open(BytesIO(imagen_bytes))
        return img.size
