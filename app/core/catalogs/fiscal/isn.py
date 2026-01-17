"""
Catálogo de ISN (Impuesto Sobre Nómina) por estado.

El ISN es un impuesto estatal que grava las erogaciones por
remuneraciones al trabajo personal. Las tasas varían por estado.

Fuente: Leyes de Hacienda estatales
Rango: 2.0% - 3.0%
"""

from decimal import Decimal
from typing import ClassVar, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class EstadoISN:
    """Información de ISN por estado."""
    clave: str
    nombre: str
    tasa: Decimal
    notas: str = ""


class CatalogoISN:
    """
    Tasas de ISN (Impuesto Sobre Nómina) por estado 2026.

    Uso:
        from app.core.catalogs import CatalogoISN

        tasa = CatalogoISN.obtener_tasa("puebla")  # Decimal("0.03")
        isn = nomina * CatalogoISN.PUEBLA
    """

    # ═══════════════════════════════════════════════════════════════
    # METADATOS
    # ═══════════════════════════════════════════════════════════════
    ANO: ClassVar[int] = 2026
    TASA_MINIMA: ClassVar[Decimal] = Decimal("0.02")   # 2.0%
    TASA_MAXIMA: ClassVar[Decimal] = Decimal("0.03")   # 3.0%
    TASA_DEFAULT: ClassVar[Decimal] = Decimal("0.03")  # Si no se encuentra

    # ═══════════════════════════════════════════════════════════════
    # TASAS POR ESTADO (acceso directo)
    # ═══════════════════════════════════════════════════════════════

    AGUASCALIENTES: ClassVar[Decimal] = Decimal("0.030")
    BAJA_CALIFORNIA: ClassVar[Decimal] = Decimal("0.0265")
    BAJA_CALIFORNIA_SUR: ClassVar[Decimal] = Decimal("0.025")
    CAMPECHE: ClassVar[Decimal] = Decimal("0.030")
    CHIAPAS: ClassVar[Decimal] = Decimal("0.020")
    CHIHUAHUA: ClassVar[Decimal] = Decimal("0.030")
    CIUDAD_DE_MEXICO: ClassVar[Decimal] = Decimal("0.030")
    COAHUILA: ClassVar[Decimal] = Decimal("0.030")
    COLIMA: ClassVar[Decimal] = Decimal("0.020")
    DURANGO: ClassVar[Decimal] = Decimal("0.020")
    ESTADO_DE_MEXICO: ClassVar[Decimal] = Decimal("0.030")
    GUANAJUATO: ClassVar[Decimal] = Decimal("0.0295")
    GUERRERO: ClassVar[Decimal] = Decimal("0.020")
    HIDALGO: ClassVar[Decimal] = Decimal("0.030")
    JALISCO: ClassVar[Decimal] = Decimal("0.030")
    MICHOACAN: ClassVar[Decimal] = Decimal("0.030")
    MORELOS: ClassVar[Decimal] = Decimal("0.020")
    NAYARIT: ClassVar[Decimal] = Decimal("0.020")
    NUEVO_LEON: ClassVar[Decimal] = Decimal("0.030")
    OAXACA: ClassVar[Decimal] = Decimal("0.030")
    PUEBLA: ClassVar[Decimal] = Decimal("0.030")
    QUERETARO: ClassVar[Decimal] = Decimal("0.030")
    QUINTANA_ROO: ClassVar[Decimal] = Decimal("0.030")
    SAN_LUIS_POTOSI: ClassVar[Decimal] = Decimal("0.030")
    SINALOA: ClassVar[Decimal] = Decimal("0.0265")
    SONORA: ClassVar[Decimal] = Decimal("0.0265")
    TABASCO: ClassVar[Decimal] = Decimal("0.030")
    TAMAULIPAS: ClassVar[Decimal] = Decimal("0.030")
    TLAXCALA: ClassVar[Decimal] = Decimal("0.030")
    VERACRUZ: ClassVar[Decimal] = Decimal("0.030")
    YUCATAN: ClassVar[Decimal] = Decimal("0.030")
    ZACATECAS: ClassVar[Decimal] = Decimal("0.030")

    # ═══════════════════════════════════════════════════════════════
    # DICCIONARIO (para búsqueda por clave)
    # ═══════════════════════════════════════════════════════════════

    TASAS: ClassVar[dict[str, Decimal]] = {
        "aguascalientes": Decimal("0.030"),
        "baja_california": Decimal("0.0265"),
        "baja_california_sur": Decimal("0.025"),
        "campeche": Decimal("0.030"),
        "chiapas": Decimal("0.020"),
        "chihuahua": Decimal("0.030"),
        "ciudad_de_mexico": Decimal("0.030"),
        "cdmx": Decimal("0.030"),  # Alias
        "coahuila": Decimal("0.030"),
        "colima": Decimal("0.020"),
        "durango": Decimal("0.020"),
        "estado_de_mexico": Decimal("0.030"),
        "guanajuato": Decimal("0.0295"),
        "guerrero": Decimal("0.020"),
        "hidalgo": Decimal("0.030"),
        "jalisco": Decimal("0.030"),
        "michoacan": Decimal("0.030"),
        "morelos": Decimal("0.020"),
        "nayarit": Decimal("0.020"),
        "nuevo_leon": Decimal("0.030"),
        "oaxaca": Decimal("0.030"),
        "puebla": Decimal("0.030"),
        "queretaro": Decimal("0.030"),
        "quintana_roo": Decimal("0.030"),
        "san_luis_potosi": Decimal("0.030"),
        "sinaloa": Decimal("0.0265"),
        "sonora": Decimal("0.0265"),
        "tabasco": Decimal("0.030"),
        "tamaulipas": Decimal("0.030"),
        "tlaxcala": Decimal("0.030"),
        "veracruz": Decimal("0.030"),
        "yucatan": Decimal("0.030"),
        "zacatecas": Decimal("0.030"),
    }

    # ═══════════════════════════════════════════════════════════════
    # DATOS ESTRUCTURADOS (para reportes)
    # ═══════════════════════════════════════════════════════════════

    ESTADOS: ClassVar[list[EstadoISN]] = [
        EstadoISN("chiapas", "Chiapas", Decimal("0.020"), "Tasa más baja"),
        EstadoISN("colima", "Colima", Decimal("0.020")),
        EstadoISN("durango", "Durango", Decimal("0.020")),
        EstadoISN("guerrero", "Guerrero", Decimal("0.020")),
        EstadoISN("morelos", "Morelos", Decimal("0.020")),
        EstadoISN("nayarit", "Nayarit", Decimal("0.020")),
        EstadoISN("baja_california_sur", "Baja California Sur", Decimal("0.025")),
        EstadoISN("baja_california", "Baja California", Decimal("0.0265")),
        EstadoISN("sinaloa", "Sinaloa", Decimal("0.0265")),
        EstadoISN("sonora", "Sonora", Decimal("0.0265")),
        EstadoISN("guanajuato", "Guanajuato", Decimal("0.0295")),
        # Estados con 3%
        EstadoISN("aguascalientes", "Aguascalientes", Decimal("0.030")),
        EstadoISN("campeche", "Campeche", Decimal("0.030")),
        EstadoISN("chihuahua", "Chihuahua", Decimal("0.030")),
        EstadoISN("ciudad_de_mexico", "Ciudad de México", Decimal("0.030")),
        EstadoISN("coahuila", "Coahuila", Decimal("0.030")),
        EstadoISN("estado_de_mexico", "Estado de México", Decimal("0.030")),
        EstadoISN("hidalgo", "Hidalgo", Decimal("0.030")),
        EstadoISN("jalisco", "Jalisco", Decimal("0.030")),
        EstadoISN("michoacan", "Michoacán", Decimal("0.030")),
        EstadoISN("nuevo_leon", "Nuevo León", Decimal("0.030")),
        EstadoISN("oaxaca", "Oaxaca", Decimal("0.030")),
        EstadoISN("puebla", "Puebla", Decimal("0.030")),
        EstadoISN("queretaro", "Querétaro", Decimal("0.030")),
        EstadoISN("quintana_roo", "Quintana Roo", Decimal("0.030")),
        EstadoISN("san_luis_potosi", "San Luis Potosí", Decimal("0.030")),
        EstadoISN("tabasco", "Tabasco", Decimal("0.030")),
        EstadoISN("tamaulipas", "Tamaulipas", Decimal("0.030")),
        EstadoISN("tlaxcala", "Tlaxcala", Decimal("0.030")),
        EstadoISN("veracruz", "Veracruz", Decimal("0.030")),
        EstadoISN("yucatan", "Yucatán", Decimal("0.030")),
        EstadoISN("zacatecas", "Zacatecas", Decimal("0.030")),
    ]

    # ═══════════════════════════════════════════════════════════════
    # MÉTODOS
    # ═══════════════════════════════════════════════════════════════

    @classmethod
    def obtener_tasa(cls, estado: str) -> Decimal:
        """
        Obtiene la tasa de ISN para un estado.

        Args:
            estado: Clave del estado (ej: "puebla", "ciudad_de_mexico")

        Returns:
            Tasa de ISN como decimal (ej: 0.03 para 3%)
        """
        clave = estado.lower().replace(" ", "_")
        return cls.TASAS.get(clave, cls.TASA_DEFAULT)

    @classmethod
    def obtener_info(cls, estado: str) -> Optional[EstadoISN]:
        """Obtiene información completa de un estado."""
        clave = estado.lower().replace(" ", "_")
        for info in cls.ESTADOS:
            if info.clave == clave:
                return info
        return None

    @classmethod
    def estados_por_tasa(cls, tasa: Decimal) -> list[str]:
        """Retorna lista de estados con una tasa específica."""
        return [clave for clave, t in cls.TASAS.items() if t == tasa]
