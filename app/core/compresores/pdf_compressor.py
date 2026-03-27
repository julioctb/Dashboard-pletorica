"""
Compresor de PDFs usando Ghostscript.

Reduce el tamano de PDFs mediante resampling de imagenes internas.
Requiere Ghostscript instalado a nivel de sistema operativo.

Instalacion:
    macOS:  brew install ghostscript
    Ubuntu: sudo apt-get install ghostscript

Niveles de calidad (dPDFSETTINGS):
    /screen   : 72 dpi  - Minima calidad, maxima compresion
    /ebook    : 150 dpi - Baja calidad, buena compresion (RECOMENDADO)
    /printer  : 300 dpi - Alta calidad, compresion moderada
    /prepress : 300 dpi - Maxima calidad, minima compresion

Uso:
    from app.core.compresores import GhostscriptCompressor

    pdf_bytes, metadata = GhostscriptCompressor.comprimir_si_necesario(pdf_bytes)
"""

import os
import subprocess
import tempfile
from typing import Optional, Tuple

from app.core.config.archivos_config import ArchivosConfig


class GhostscriptCompressor:
    """Compresor de PDFs usando Ghostscript."""

    @staticmethod
    def esta_disponible() -> bool:
        """Verifica si Ghostscript esta instalado en el sistema."""
        try:
            result = subprocess.run(
                ["gs", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def obtener_version() -> Optional[str]:
        """Obtiene la version de Ghostscript instalada."""
        try:
            result = subprocess.run(
                ["gs", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    @staticmethod
    def comprimir_pdf(
        pdf_bytes: bytes,
        calidad: str = "/ebook",
    ) -> bytes:
        """
        Comprime un PDF usando Ghostscript.

        Args:
            pdf_bytes: Contenido del PDF original
            calidad: Nivel de compresion (/screen, /ebook, /printer, /prepress)

        Returns:
            PDF comprimido como bytes.

        Raises:
            RuntimeError: Si Ghostscript no esta disponible o falla.
        """
        if not GhostscriptCompressor.esta_disponible():
            raise RuntimeError("Ghostscript no esta instalado en el sistema")

        with tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False
        ) as input_file:
            input_file.write(pdf_bytes)
            input_path = input_file.name

        output_path = input_path.replace(".pdf", "_compressed.pdf")

        try:
            result = subprocess.run(
                [
                    "gs",
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",
                    f"-dPDFSETTINGS={calidad}",
                    "-dNOPAUSE",
                    "-dQUIET",
                    "-dBATCH",
                    "-dColorImageResolution=150",
                    "-dGrayImageResolution=150",
                    "-dMonoImageResolution=150",
                    "-dDownsampleColorImages=true",
                    "-dDownsampleGrayImages=true",
                    "-dDownsampleMonoImages=true",
                    f"-sOutputFile={output_path}",
                    input_path,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Ghostscript error: {result.stderr}")

            with open(output_path, "rb") as f:
                compressed_bytes = f.read()

            return compressed_bytes

        finally:
            for path in [input_path, output_path]:
                if os.path.exists(path):
                    try:
                        os.unlink(path)
                    except OSError:
                        pass

    @staticmethod
    def comprimir_si_necesario(
        pdf_bytes: bytes,
        tamanio_maximo_bytes: int = ArchivosConfig.WEB_TAMANIO_MAX_PDF,
    ) -> Tuple[bytes, dict]:
        """
        Comprime el PDF solo si excede el tamano maximo.
        Intenta primero con calidad /ebook, luego /screen si no basta.

        Returns:
            Tupla (pdf_final, metadata).
        """
        tamanio_original = len(pdf_bytes)

        metadata = {
            "tamanio_original": tamanio_original,
            "tamanio_final": tamanio_original,
            "formato_original": "pdf",
            "formato_final": "pdf",
            "comprimido": False,
            "calidad_usada": None,
            "reduccion_porcentaje": 0,
            "ghostscript_disponible": GhostscriptCompressor.esta_disponible(),
        }

        if tamanio_original <= tamanio_maximo_bytes:
            return pdf_bytes, metadata

        if not GhostscriptCompressor.esta_disponible():
            metadata["error"] = "Ghostscript no disponible"
            return pdf_bytes, metadata

        calidades = [
            ArchivosConfig.GS_CALIDAD_INICIAL,
            ArchivosConfig.GS_CALIDAD_AGRESIVA,
        ]

        compressed = pdf_bytes
        for calidad in calidades:
            try:
                compressed = GhostscriptCompressor.comprimir_pdf(
                    pdf_bytes, calidad
                )

                metadata.update(
                    {
                        "tamanio_final": len(compressed),
                        "comprimido": True,
                        "calidad_usada": calidad,
                        "reduccion_porcentaje": round(
                            (1 - len(compressed) / tamanio_original) * 100, 1
                        ),
                    }
                )

                if len(compressed) <= tamanio_maximo_bytes:
                    return compressed, metadata

            except RuntimeError as e:
                metadata["error"] = str(e)
                return pdf_bytes, metadata

        return compressed, metadata

    @staticmethod
    def validar_pdf(pdf_bytes: bytes) -> bool:
        """Valida que el contenido sea un PDF valido."""
        return pdf_bytes[:4] == b"%PDF"
