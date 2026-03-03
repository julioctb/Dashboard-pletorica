"""
Catálogo maestro de conceptos de nómina alineado a legislación mexicana.

Fuentes legales:
- SAT: Catálogos CFDI Nómina 4.0 (c_TipoPercepcion, c_TipoDeduccion, c_TipoOtroPago)
- LISR: Art. 93 (exenciones), Art. 94 (ingresos gravables), Art. 96 (retención)
- LSS: Art. 27 (integración SBC), Art. 36 (absorción cuota obrera)
- LFT: Art. 76-80 (vacaciones/prima), Art. 87 (aguinaldo)

Uso:
    from app.core.catalogs import CatalogoConceptosNomina

    concepto = CatalogoConceptosNomina.obtener('SUELDO')
    todos = CatalogoConceptosNomina.todos()
    percepciones = CatalogoConceptosNomina.por_tipo(TipoConcepto.PERCEPCION)
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Optional

from app.core.enums import TipoConcepto, TratamientoISR, OrigenCaptura
from app.core.catalogs.nomina.enums import CategoriaConcepto


@dataclass(frozen=True)
class ConceptoNominaDef:
    """
    Definición legal inmutable de un concepto de nómina.

    Cada instancia codifica las reglas fiscales y laborales
    de un concepto según la legislación mexicana vigente.
    """
    # ── Identificación ──────────────────────────────────────────
    clave: str                              # Clave interna única (ej: 'SUELDO')
    nombre: str                             # Nombre legal/oficial
    descripcion: str                        # Descripción funcional

    # ── Clasificación SAT (CFDI Nómina 4.0) ─────────────────────
    tipo: TipoConcepto                      # PERCEPCION / DEDUCCION / OTRO_PAGO
    clave_sat: str                          # c_TipoPercepcion, c_TipoDeduccion o c_TipoOtroPago
    nombre_sat: str                         # Nombre oficial en catálogo SAT

    # ── Tratamiento ISR (LISR Art. 93, 94) ──────────────────────
    tratamiento_isr: TratamientoISR         # GRAVABLE / EXENTO / PARCIALMENTE_EXENTO / NO_APLICA
    limite_exencion_uma: Optional[Decimal] = None   # Múltiplo de UMA para exención
    porcentaje_exento: Optional[Decimal] = None     # Fracción exenta (0.50 = 50%)
    periodo_limite_exencion: Optional[str] = None   # 'diario', 'semanal', 'mensual', 'anual'
    articulo_isr: str = ""                  # Artículo de LISR que fundamenta

    # ── Integración SBC (LSS Art. 27) ──────────────────────────
    integra_sbc: bool = True                # Integra al Salario Base de Cotización
    articulo_lss: str = ""                  # Artículo de LSS que fundamenta

    # ── Operación ──────────────────────────────────────────────
    origen_captura: OrigenCaptura = OrigenCaptura.SISTEMA
    categoria: CategoriaConcepto = CategoriaConcepto.OTROS
    es_obligatorio: bool = False            # Aplica a todos los empleados siempre
    requiere_monto_manual: bool = False     # RRHH/Contabilidad captura el monto
    orden_default: int = 0                  # Orden sugerido en el recibo

    # ── Metadatos legales ──────────────────────────────────────
    fundamentacion_legal: str = ""          # Referencia completa de ley


class CatalogoConceptosNomina:
    """
    Catálogo maestro de conceptos de nómina.

    Define las reglas legales/fiscales de cada concepto (inmutables, versionadas
    en Git). La configuración por empresa vive en BD (tabla conceptos_nomina_empresa).

    Fuente: SAT CFDI Nómina 4.0, LISR, LSS, LFT — vigente 2026.
    """

    ANO: ClassVar[int] = 2026
    FUENTE: ClassVar[str] = "SAT CFDI Nómina 4.0, LISR, LSS, LFT"

    # =========================================================================
    # PERCEPCIONES
    # =========================================================================

    SUELDO: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='SUELDO',
        nombre='Sueldos, Salarios y Asimilados',
        descripcion='Sueldo base proporcional a días trabajados en el período',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='001',
        nombre_sat='Sueldos, Salarios, Rayas y Jornales',
        tratamiento_isr=TratamientoISR.GRAVABLE,
        integra_sbc=True,
        articulo_lss='Art. 27 LSS',
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.SUELDO,
        es_obligatorio=True,
        requiere_monto_manual=False,
        orden_default=1,
        articulo_isr='Art. 94-I LISR',
        fundamentacion_legal='LISR Art. 94-I, LSS Art. 27',
    )

    HORAS_EXTRA_DOBLES: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='HORAS_EXTRA_DOBLES',
        nombre='Horas extra dobles',
        descripcion='Horas extra dobles (primeras 9 semanales)',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='019',
        nombre_sat='Horas extra',
        tratamiento_isr=TratamientoISR.PARCIALMENTE_EXENTO,
        limite_exencion_uma=Decimal('5'),
        porcentaje_exento=Decimal('0.50'),
        periodo_limite_exencion='semanal',
        articulo_isr='Art. 93-I LISR',
        integra_sbc=True,
        articulo_lss='Art. 27 LSS',
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.TIEMPO_EXTRA,
        es_obligatorio=False,
        requiere_monto_manual=False,
        orden_default=2,
        fundamentacion_legal='LISR Art. 93-I (50% exento, tope 5 UMA/sem), LSS Art. 27',
    )

    HORAS_EXTRA_TRIPLES: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='HORAS_EXTRA_TRIPLES',
        nombre='Horas extra triples',
        descripcion='Horas extra triples (excedente de 9 semanales)',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='019',
        nombre_sat='Horas extra',
        tratamiento_isr=TratamientoISR.GRAVABLE,
        articulo_isr='Art. 94 LISR',
        integra_sbc=True,
        articulo_lss='Art. 27 LSS',
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.TIEMPO_EXTRA,
        es_obligatorio=False,
        requiere_monto_manual=False,
        orden_default=3,
        fundamentacion_legal='LISR Art. 94 (100% gravable), LSS Art. 27',
    )

    PRIMA_DOMINICAL: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='PRIMA_DOMINICAL',
        nombre='Prima dominical',
        descripcion='Prima del 25% por trabajar en domingo',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='020',
        nombre_sat='Prima dominical',
        tratamiento_isr=TratamientoISR.PARCIALMENTE_EXENTO,
        limite_exencion_uma=Decimal('1'),
        periodo_limite_exencion='semanal',
        articulo_isr='Art. 93-I LISR',
        integra_sbc=True,
        articulo_lss='Art. 27 LSS',
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.PRESTACIONES,
        es_obligatorio=False,
        requiere_monto_manual=False,
        orden_default=4,
        fundamentacion_legal='LISR Art. 93-I (exento hasta 1 UMA/sem), LSS Art. 27',
    )

    VACACIONES: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='VACACIONES',
        nombre='Vacaciones (pago)',
        descripcion='Pago de días de vacaciones',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='001',
        nombre_sat='Sueldos, Salarios, Rayas y Jornales',
        tratamiento_isr=TratamientoISR.GRAVABLE,
        articulo_isr='Art. 94 LISR',
        integra_sbc=False,
        articulo_lss='Art. 27-IX LSS',
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.PRESTACIONES,
        es_obligatorio=False,
        requiere_monto_manual=False,
        orden_default=5,
        fundamentacion_legal='LISR Art. 94, LSS Art. 27-IX (no integra si LFT min)',
    )

    PRIMA_VACACIONAL: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='PRIMA_VACACIONAL',
        nombre='Prima vacacional',
        descripcion='Prima vacacional (mínimo 25% LFT)',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='021',
        nombre_sat='Prima vacacional',
        tratamiento_isr=TratamientoISR.PARCIALMENTE_EXENTO,
        limite_exencion_uma=Decimal('15'),
        periodo_limite_exencion='anual',
        articulo_isr='Art. 93-XIV LISR',
        integra_sbc=False,
        articulo_lss='Art. 27-IX LSS',
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.PRESTACIONES,
        es_obligatorio=False,
        requiere_monto_manual=False,
        orden_default=6,
        fundamentacion_legal='LISR Art. 93-XIV (exento hasta 15 UMA), LSS Art. 27-IX',
    )

    AGUINALDO: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='AGUINALDO',
        nombre='Aguinaldo',
        descripcion='Aguinaldo anual (mínimo 15 días LFT)',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='002',
        nombre_sat='Gratificación anual (aguinaldo)',
        tratamiento_isr=TratamientoISR.PARCIALMENTE_EXENTO,
        limite_exencion_uma=Decimal('30'),
        periodo_limite_exencion='anual',
        articulo_isr='Art. 93-XIII LISR',
        integra_sbc=False,
        articulo_lss='Art. 27-IX LSS',
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.PRESTACIONES,
        es_obligatorio=False,
        requiere_monto_manual=False,
        orden_default=7,
        fundamentacion_legal='LISR Art. 93-XIII (exento hasta 30 UMA), LSS Art. 27-IX',
    )

    BONO_PRODUCTIVIDAD: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='BONO_PRODUCTIVIDAD',
        nombre='Bono de productividad',
        descripcion='Bono por cumplimiento de metas',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='038',
        nombre_sat='Otros ingresos por salarios',
        tratamiento_isr=TratamientoISR.GRAVABLE,
        articulo_isr='Art. 94 LISR',
        integra_sbc=True,
        articulo_lss='Art. 27 LSS',
        origen_captura=OrigenCaptura.CONTABILIDAD,
        categoria=CategoriaConcepto.BONOS,
        es_obligatorio=False,
        requiere_monto_manual=True,
        orden_default=10,
        fundamentacion_legal='LISR Art. 94 (gravable), LSS Art. 27 (integra)',
    )

    BONO_PUNTUALIDAD: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='BONO_PUNTUALIDAD',
        nombre='Premio de puntualidad',
        descripcion='Premio por puntualidad del trabajador',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='010',
        nombre_sat='Premios por puntualidad',
        tratamiento_isr=TratamientoISR.PARCIALMENTE_EXENTO,
        articulo_isr='Art. 93-I LISR',
        integra_sbc=True,
        articulo_lss='Art. 27-VII LSS',
        origen_captura=OrigenCaptura.CONTABILIDAD,
        categoria=CategoriaConcepto.BONOS,
        es_obligatorio=False,
        requiere_monto_manual=True,
        orden_default=11,
        fundamentacion_legal='LISR Art. 93-I, LSS Art. 27-VII (no integra si <=10% SBC)',
    )

    BONO_ASISTENCIA: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='BONO_ASISTENCIA',
        nombre='Premio de asistencia',
        descripcion='Premio por asistencia del trabajador',
        tipo=TipoConcepto.PERCEPCION,
        clave_sat='009',
        nombre_sat='Premios por asistencia',
        tratamiento_isr=TratamientoISR.PARCIALMENTE_EXENTO,
        articulo_isr='Art. 93-I LISR',
        integra_sbc=True,
        articulo_lss='Art. 27-VII LSS',
        origen_captura=OrigenCaptura.CONTABILIDAD,
        categoria=CategoriaConcepto.BONOS,
        es_obligatorio=False,
        requiere_monto_manual=True,
        orden_default=12,
        fundamentacion_legal='LISR Art. 93-I, LSS Art. 27-VII (no integra si <=10% SBC)',
    )

    # =========================================================================
    # OTRO PAGO
    # =========================================================================

    SUBSIDIO_EMPLEO: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='SUBSIDIO_EMPLEO',
        nombre='Subsidio para el empleo',
        descripcion='Subsidio al empleo (DOF)',
        tipo=TipoConcepto.OTRO_PAGO,
        clave_sat='002',
        nombre_sat='Subsidio para el empleo',
        tratamiento_isr=TratamientoISR.NO_APLICA,
        integra_sbc=False,
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.OTROS,
        es_obligatorio=False,
        requiere_monto_manual=False,
        orden_default=20,
        fundamentacion_legal='DOF Decreto Subsidio Empleo',
    )

    # =========================================================================
    # DEDUCCIONES
    # =========================================================================

    ISR: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='ISR',
        nombre='ISR (Impuesto Sobre la Renta)',
        descripcion='Retención de ISR según tabla Art. 96 LISR',
        tipo=TipoConcepto.DEDUCCION,
        clave_sat='002',
        nombre_sat='ISR',
        tratamiento_isr=TratamientoISR.NO_APLICA,
        integra_sbc=False,
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.IMPUESTOS,
        es_obligatorio=True,
        requiere_monto_manual=False,
        orden_default=30,
        articulo_isr='Art. 96 LISR',
        fundamentacion_legal='LISR Art. 96',
    )

    IMSS_OBRERO: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='IMSS_OBRERO',
        nombre='Cuotas obreras IMSS',
        descripcion='Cuotas del trabajador al IMSS',
        tipo=TipoConcepto.DEDUCCION,
        clave_sat='001',
        nombre_sat='Seguridad social',
        tratamiento_isr=TratamientoISR.NO_APLICA,
        integra_sbc=False,
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.SEGURIDAD_SOCIAL,
        es_obligatorio=True,
        requiere_monto_manual=False,
        orden_default=31,
        articulo_lss='Art. 25, 106, 147 LSS',
        fundamentacion_legal='LSS Art. 25, 106, 147',
    )

    DESCUENTO_INFONAVIT: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='DESCUENTO_INFONAVIT',
        nombre='Amortización INFONAVIT',
        descripcion='Descuento por crédito INFONAVIT',
        tipo=TipoConcepto.DEDUCCION,
        clave_sat='010',
        nombre_sat='Aportaciones para el INFONAVIT',
        tratamiento_isr=TratamientoISR.NO_APLICA,
        integra_sbc=False,
        origen_captura=OrigenCaptura.RRHH,
        categoria=CategoriaConcepto.CREDITOS,
        es_obligatorio=False,
        requiere_monto_manual=True,
        orden_default=32,
        fundamentacion_legal='LINFONAVIT Art. 29',
    )

    DESCUENTO_FONACOT: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='DESCUENTO_FONACOT',
        nombre='Descuento FONACOT',
        descripcion='Descuento por crédito FONACOT',
        tipo=TipoConcepto.DEDUCCION,
        clave_sat='011',
        nombre_sat='Descuento por créditos FONACOT',
        tratamiento_isr=TratamientoISR.NO_APLICA,
        integra_sbc=False,
        origen_captura=OrigenCaptura.RRHH,
        categoria=CategoriaConcepto.CREDITOS,
        es_obligatorio=False,
        requiere_monto_manual=True,
        orden_default=33,
        fundamentacion_legal='LFT Art. 132-XXVI bis',
    )

    PRESTAMO_EMPRESA: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='PRESTAMO_EMPRESA',
        nombre='Préstamos otorgados por empresa',
        descripcion='Descuento por préstamo interno',
        tipo=TipoConcepto.DEDUCCION,
        clave_sat='004',
        nombre_sat='Otros',
        tratamiento_isr=TratamientoISR.NO_APLICA,
        integra_sbc=False,
        origen_captura=OrigenCaptura.RRHH,
        categoria=CategoriaConcepto.CREDITOS,
        es_obligatorio=False,
        requiere_monto_manual=True,
        orden_default=34,
        fundamentacion_legal='Convenio patrón-trabajador',
    )

    PENSION_ALIMENTICIA: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='PENSION_ALIMENTICIA',
        nombre='Pensión alimenticia',
        descripcion='Retención por orden judicial',
        tipo=TipoConcepto.DEDUCCION,
        clave_sat='007',
        nombre_sat='Pensión alimenticia',
        tratamiento_isr=TratamientoISR.NO_APLICA,
        integra_sbc=False,
        origen_captura=OrigenCaptura.RRHH,
        categoria=CategoriaConcepto.CREDITOS,
        es_obligatorio=False,
        requiere_monto_manual=True,
        orden_default=35,
        fundamentacion_legal='Orden judicial',
    )

    DESCUENTO_FALTAS: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='DESCUENTO_FALTAS',
        nombre='Descuento por ausencia',
        descripcion='Descuento proporcional por faltas',
        tipo=TipoConcepto.DEDUCCION,
        clave_sat='006',
        nombre_sat='Ausencias e incapacidades',
        tratamiento_isr=TratamientoISR.NO_APLICA,
        integra_sbc=False,
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.OTROS,
        es_obligatorio=False,
        requiere_monto_manual=False,
        orden_default=36,
        fundamentacion_legal='LFT Art. 82',
    )

    DESCUENTO_INCAPACIDAD: ClassVar[ConceptoNominaDef] = ConceptoNominaDef(
        clave='DESCUENTO_INCAPACIDAD',
        nombre='Descuento por incapacidad',
        descripcion='Descuento por días de incapacidad',
        tipo=TipoConcepto.DEDUCCION,
        clave_sat='006',
        nombre_sat='Ausencias e incapacidades',
        tratamiento_isr=TratamientoISR.NO_APLICA,
        integra_sbc=False,
        origen_captura=OrigenCaptura.SISTEMA,
        categoria=CategoriaConcepto.OTROS,
        es_obligatorio=False,
        requiere_monto_manual=False,
        orden_default=37,
        fundamentacion_legal='LSS Art. 96',
    )

    # =========================================================================
    # REGISTRO INTERNO
    # =========================================================================

    _CONCEPTOS: ClassVar[dict] = {}

    @classmethod
    def _inicializar(cls) -> None:
        """Puebla el dict interno con todos los conceptos ClassVar."""
        if cls._CONCEPTOS:
            return
        for nombre_attr in dir(cls):
            if nombre_attr.startswith('_'):
                continue
            valor = getattr(cls, nombre_attr)
            if isinstance(valor, ConceptoNominaDef):
                cls._CONCEPTOS[valor.clave] = valor

    @classmethod
    def obtener(cls, clave: str) -> ConceptoNominaDef:
        """Obtiene un concepto por clave. Lanza KeyError si no existe."""
        cls._inicializar()
        if clave not in cls._CONCEPTOS:
            raise KeyError(f"Concepto de nómina '{clave}' no existe en el catálogo")
        return cls._CONCEPTOS[clave]

    @classmethod
    def todos(cls) -> list[ConceptoNominaDef]:
        """Retorna todos los conceptos ordenados por orden_default."""
        cls._inicializar()
        return sorted(cls._CONCEPTOS.values(), key=lambda c: c.orden_default)

    @classmethod
    def por_tipo(cls, tipo: TipoConcepto) -> list[ConceptoNominaDef]:
        """Filtra conceptos por tipo (PERCEPCION, DEDUCCION, OTRO_PAGO)."""
        return [c for c in cls.todos() if c.tipo == tipo]

    @classmethod
    def por_categoria(cls, categoria: CategoriaConcepto) -> list[ConceptoNominaDef]:
        """Filtra conceptos por categoría funcional."""
        return [c for c in cls.todos() if c.categoria == categoria]

    @classmethod
    def por_origen(cls, origen: OrigenCaptura) -> list[ConceptoNominaDef]:
        """Filtra conceptos por quién los captura."""
        return [c for c in cls.todos() if c.origen_captura == origen]

    @classmethod
    def percepciones(cls) -> list[ConceptoNominaDef]:
        """Shortcut: todas las percepciones."""
        return cls.por_tipo(TipoConcepto.PERCEPCION)

    @classmethod
    def deducciones(cls) -> list[ConceptoNominaDef]:
        """Shortcut: todas las deducciones."""
        return cls.por_tipo(TipoConcepto.DEDUCCION)

    @classmethod
    def obligatorios(cls) -> list[ConceptoNominaDef]:
        """Conceptos que siempre aplican a todos los empleados."""
        return [c for c in cls.todos() if c.es_obligatorio]

    @classmethod
    def que_integran_sbc(cls) -> list[ConceptoNominaDef]:
        """Conceptos que integran al Salario Base de Cotización."""
        return [c for c in cls.todos() if c.integra_sbc]

    @classmethod
    def claves_validas(cls) -> set[str]:
        """Set de todas las claves válidas (para validación)."""
        cls._inicializar()
        return set(cls._CONCEPTOS.keys())

    @classmethod
    def calcular_exencion(
        cls,
        clave: str,
        monto: Decimal,
        uma_diario: Decimal,
    ) -> tuple[Decimal, Decimal]:
        """
        Calcula la parte gravable y exenta de un concepto.

        Args:
            clave: Clave del concepto
            monto: Monto total del concepto
            uma_diario: Valor diario de la UMA vigente

        Returns:
            Tupla (gravable, exento)

        Ejemplo:
            >>> CatalogoConceptosNomina.calcular_exencion(
            ...     'AGUINALDO', Decimal('6000'), Decimal('113.14'))
            (Decimal('2605.80'), Decimal('3394.20'))
        """
        concepto = cls.obtener(clave)

        if concepto.tratamiento_isr == TratamientoISR.GRAVABLE:
            return (monto, Decimal('0'))

        if concepto.tratamiento_isr == TratamientoISR.EXENTO:
            return (Decimal('0'), monto)

        if concepto.tratamiento_isr == TratamientoISR.NO_APLICA:
            return (Decimal('0'), Decimal('0'))

        # PARCIALMENTE_EXENTO
        # Caso especial: tiene AMBOS porcentaje y límite UMA
        # (ej: horas extra dobles: 50% exento con tope 5 UMA semanales)
        if (concepto.porcentaje_exento is not None
                and concepto.limite_exencion_uma is not None):
            exento_por_porcentaje = monto * concepto.porcentaje_exento
            tope_uma = uma_diario * concepto.limite_exencion_uma
            exento = min(exento_por_porcentaje, tope_uma)
            gravable = monto - exento
            return (gravable, exento)

        # Solo límite UMA (ej: aguinaldo hasta 30 UMA)
        if concepto.limite_exencion_uma is not None:
            limite = uma_diario * concepto.limite_exencion_uma
            exento = min(monto, limite)
            gravable = monto - exento
            return (gravable, exento)

        # Solo porcentaje (sin tope)
        if concepto.porcentaje_exento is not None:
            exento = monto * concepto.porcentaje_exento
            gravable = monto - exento
            return (gravable, exento)

        # Parcialmente exento sin regla definida → tratar como gravable
        return (monto, Decimal('0'))
