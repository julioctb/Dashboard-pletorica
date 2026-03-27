"""
Compresores de archivos del sistema.

Provee compresion de imagenes (Pillow → WebP) y PDFs (Ghostscript).
"""

from app.core.compresores.imagen_compressor import ImagenCompressor
from app.core.compresores.pdf_compressor import GhostscriptCompressor

__all__ = ["ImagenCompressor", "GhostscriptCompressor"]
