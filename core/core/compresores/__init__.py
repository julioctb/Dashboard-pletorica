"""
Compresores de archivos del sistema.

Provee compresion de imagenes (Pillow → WebP) y PDFs (Ghostscript).
"""

from core.core.compresores.imagen_compressor import ImagenCompressor
from core.core.compresores.pdf_compressor import GhostscriptCompressor

__all__ = ["ImagenCompressor", "GhostscriptCompressor"]
