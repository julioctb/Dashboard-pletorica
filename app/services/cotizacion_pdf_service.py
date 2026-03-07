"""
Servicio de generación de PDF para cotizaciones.

Usa reportlab para generar PDF con el formato de Mantiser:
- Membrete de empresa
- Tabla de determinación de montos min/max por partida
- Desglose de conceptos (si mostrar_desglose=True)
- Espacio de firma del representante legal

Dependencias: reportlab, num2words
"""
import io
import logging
from decimal import Decimal
from typing import Optional

from app.entities.cotizacion import calcular_meses_periodo

logger = logging.getLogger(__name__)


def _monto_a_letra(monto: float) -> str:
    """
    Convierte monto a texto en español para documentos fiscales.

    Ejemplo: 125000.50 → "CIENTO VEINTICINCO MIL PESOS 50/100 M.N."
    """
    try:
        from num2words import num2words
        entero = int(monto)
        centavos = round((monto - entero) * 100)
        texto = num2words(entero, lang='es').upper()
        # Normalizar caracteres especiales
        texto = texto.replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
        return f"{texto} PESOS {centavos:02d}/100 M.N."
    except ImportError:
        return f"${monto:,.2f} M.N."
    except Exception as e:
        logger.warning(f"Error convirtiendo monto a letra: {e}")
        return f"${monto:,.2f} M.N."


class CotizacionPdfService:
    """Generador de PDF para cotizaciones usando reportlab."""

    def __init__(self):
        self.supabase = None  # Lazy init
        self._iva_rate = Decimal('0.16')

    def _get_supabase(self):
        if self.supabase is None:
            from app.database import db_manager
            self.supabase = db_manager.get_client()
        return self.supabase

    async def generar_pdf(
        self,
        cotizacion_id: int,
        partida_ids: Optional[list[int]] = None,
    ) -> bytes:
        """
        Genera PDF de cotización.

        Args:
            cotizacion_id: ID de la cotización.
            partida_ids: Lista de IDs de partidas a incluir. None = todas.

        Returns:
            bytes del PDF generado.

        Raises:
            ImportError: Si reportlab no está instalado.
            Exception: Si hay error al generar el PDF.
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, landscape
            from reportlab.lib.units import cm, mm
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle, Paragraph,
                Spacer, HRFlowable, PageBreak,
            )
        except ImportError:
            raise ImportError(
                "reportlab no está instalado. Ejecuta: poetry add reportlab"
            )

        supabase = self._get_supabase()

        # Cargar cotización
        cot_result = (
            supabase.table('cotizaciones')
            .select('*, empresas(nombre_comercial, codigo)')
            .eq('id', cotizacion_id)
            .single()
            .execute()
        )
        if not cot_result.data:
            raise ValueError(f"Cotización {cotizacion_id} no encontrada")

        cotizacion = cot_result.data
        empresa = cotizacion.pop('empresas', {}) or {}

        # Cargar partidas
        partidas_query = (
            supabase.table('cotizacion_partidas')
            .select('*')
            .eq('cotizacion_id', cotizacion_id)
            .order('numero_partida')
        )
        if partida_ids:
            partidas_query = partidas_query.in_('id', partida_ids)

        partidas_result = partidas_query.execute()
        partidas = partidas_result.data or []

        # Buffer y documento
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        styles = getSampleStyleSheet()
        story = []

        # Estilos personalizados
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Title'],
            fontSize=13,
            spaceAfter=6,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            alignment=TA_CENTER,
        )
        normal_center = ParagraphStyle(
            'NormalCenter',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
        )
        normal_left = ParagraphStyle(
            'NormalLeft',
            parent=styles['Normal'],
            fontSize=9,
            alignment=TA_LEFT,
        )
        bold_left = ParagraphStyle(
            'BoldLeft',
            parent=styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Bold',
            alignment=TA_LEFT,
        )
        small_center = ParagraphStyle(
            'SmallCenter',
            parent=styles['Normal'],
            fontSize=7.5,
            alignment=TA_CENTER,
        )

        nombre_empresa = empresa.get('nombre_comercial', 'EMPRESA')
        mostrar_desglose = cotizacion.get('mostrar_desglose', False)
        from app.services import cotizacion_service

        for i, partida in enumerate(partidas):
            if i > 0:
                story.append(PageBreak())

            partida_id = partida['id']
            num_partida = partida['numero_partida']

            # Membrete
            story.append(Paragraph(nombre_empresa.upper(), title_style))
            story.append(Spacer(1, 3 * mm))

            # Título principal
            story.append(Paragraph(
                f"COTIZACIÓN PARTIDA {num_partida}",
                title_style,
            ))
            story.append(Paragraph(
                f"DETERMINACIÓN DE LOS MONTOS MÍNIMOS Y MÁXIMOS CONFORME A LOS "
                f"PRECIOS UNITARIOS PARA LA PARTIDA {num_partida}",
                subtitle_style,
            ))
            story.append(Spacer(1, 4 * mm))

            # Destinatario
            dest_nombre = cotizacion.get('destinatario_nombre', '')
            dest_cargo = cotizacion.get('destinatario_cargo', '')
            if dest_nombre:
                story.append(Paragraph(f"<b>{dest_nombre.upper()}</b>", normal_left))
            if dest_cargo:
                story.append(Paragraph(dest_cargo.upper(), normal_left))
            story.append(Paragraph("PRESENTE", normal_left))
            story.append(Spacer(1, 4 * mm))

            # Cargar categorías de la partida
            cats_result = (
                supabase.table('cotizacion_partida_categorias')
                .select('*, categorias_puesto(clave, nombre)')
                .eq('partida_id', partida_id)
                .order('id')
                .execute()
            )
            categorias = cats_result.data or []
            matriz_partida = await cotizacion_service.obtener_valores_partida(
                partida_id,
                empresa_id=cotizacion.get('empresa_id'),
            )

            # --- TABLA DESGLOSE (si aplica) ---
            if mostrar_desglose and categorias:
                story += self._build_desglose_table(
                    partida_id, categorias, matriz_partida,
                    num_partida, nombre_empresa,
                    normal_center, bold_left, small_center,
                )
                story.append(Spacer(1, 6 * mm))

            # --- TABLA MONTOS MIN/MAX ---
            story += self._build_montos_table(
                cotizacion, partida, categorias,
                num_partida, nombre_empresa,
                normal_center, bold_left, small_center,
            )

            story.append(Spacer(1, 8 * mm))

            # Espacio de firma
            rep_legal = cotizacion.get('representante_legal', '')
            story += self._build_firma(rep_legal, nombre_empresa, normal_center, bold_left)

        if not story:
            story.append(Paragraph("Sin partidas para generar.", normal_left))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    def _build_montos_table(
        self, cotizacion, partida, categorias,
        num_partida, nombre_empresa,
        normal_center, bold_left, small_center,
    ) -> list:
        """Construye la tabla de determinación de montos min/max."""
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import mm

        fecha_inicio = cotizacion.get('fecha_inicio_periodo', '')
        fecha_fin = cotizacion.get('fecha_fin_periodo', '')

        # Calcular meses
        try:
            from datetime import date
            if isinstance(fecha_inicio, str):
                fi = date.fromisoformat(fecha_inicio)
            else:
                fi = fecha_inicio
            if isinstance(fecha_fin, str):
                ff = date.fromisoformat(fecha_fin)
            else:
                ff = fecha_fin
            meses = calcular_meses_periodo(fi, ff) or 1
        except Exception:
            meses = 1

        story = []

        # Encabezado de tabla
        header_data = [
            [Paragraph(f"<b>NOMBRE DEL PROVEEDOR: {nombre_empresa}</b>", small_center), '', '', '', '', '', ''],
            [Paragraph(f"<b>PARTIDA {num_partida}</b>", small_center), '', '', '', '', '', ''],
            [
                Paragraph("<b>No.</b>", small_center),
                Paragraph("<b>CATEGORÍA</b>", small_center),
                Paragraph("<b>Operarios\nMínimos</b>", small_center),
                Paragraph("<b>Operarios\nMáximos</b>", small_center),
                Paragraph("<b>Precio\nUnitario</b>", small_center),
                Paragraph("<b>Monto Mínimo\nPeríodo</b>", small_center),
                Paragraph("<b>Monto Máximo\nPeríodo</b>", small_center),
            ],
        ]

        # Filas de categorías
        rows = []
        total_min_sum = Decimal('0')
        total_max_sum = Decimal('0')
        total_personal_min = 0
        total_personal_max = 0

        for idx, cat in enumerate(categorias, 1):
            cat_data = cat.get('categorias_puesto', {}) or {}
            cat_nombre = cat_data.get('nombre', f"Categoría {idx}")
            precio_unitario = Decimal(str(cat.get('precio_unitario_final', 0)))
            cant_min = int(cat.get('cantidad_minima', 0))
            cant_max = int(cat.get('cantidad_maxima', 0))

            monto_min = precio_unitario * cant_min * meses
            monto_max = precio_unitario * cant_max * meses

            total_min_sum += monto_min
            total_max_sum += monto_max
            total_personal_min += cant_min
            total_personal_max += cant_max

            rows.append([
                Paragraph(str(idx), small_center),
                Paragraph(cat_nombre, small_center),
                Paragraph(str(cant_min), small_center),
                Paragraph(str(cant_max), small_center),
                Paragraph(f"${float(precio_unitario):,.2f}", small_center),
                Paragraph(f"${float(monto_min):,.2f}", small_center),
                Paragraph(f"${float(monto_max):,.2f}", small_center),
            ])

        # Fila de totales personal
        rows.append([
            Paragraph("", small_center),
            Paragraph("<b>Total de personal por las categorías requeridas</b>", small_center),
            Paragraph(f"<b>{total_personal_min}</b>", small_center),
            Paragraph(f"<b>{total_personal_max}</b>", small_center),
            Paragraph("<b>SUBTOTAL</b>", small_center),
            Paragraph(f"<b>${float(total_min_sum):,.2f}</b>", small_center),
            Paragraph(f"<b>${float(total_max_sum):,.2f}</b>", small_center),
        ])

        # IVA
        iva_min = total_min_sum * self._iva_rate
        iva_max = total_max_sum * self._iva_rate
        rows.append([
            '', '', '', '',
            Paragraph("<b>IVA (16%)</b>", small_center),
            Paragraph(f"<b>${float(iva_min):,.2f}</b>", small_center),
            Paragraph(f"<b>${float(iva_max):,.2f}</b>", small_center),
        ])

        # TOTAL
        total_min = total_min_sum + iva_min
        total_max = total_max_sum + iva_max
        rows.append([
            '', '', '', '',
            Paragraph("<b>TOTAL</b>", small_center),
            Paragraph(f"<b>${float(total_min):,.2f}</b>", small_center),
            Paragraph(f"<b>${float(total_max):,.2f}</b>", small_center),
        ])

        all_data = header_data + rows

        # Span columns para encabezados
        col_widths = [1.2*cm, 6*cm, 2.5*cm, 2.5*cm, 3*cm, 4*cm, 4*cm]
        table = Table(all_data, colWidths=col_widths, repeatRows=3)

        style = TableStyle([
            # Spans de encabezado de proveedor y partida
            ('SPAN', (0, 0), (6, 0)),
            ('SPAN', (0, 1), (6, 1)),
            # Encabezados
            ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 1), colors.white),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
            # Alternating rows
            ('ROWBACKGROUNDS', (0, 3), (-1, len(all_data) - 4), [colors.white, colors.HexColor('#F0F4FF')]),
            # Totales
            ('BACKGROUND', (0, len(all_data) - 3), (-1, len(all_data) - 1), colors.HexColor('#E8F0FE')),
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#AAAAAA')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWHEIGHT', (0, 0), (-1, -1), 18),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ])
        table.setStyle(style)
        story.append(table)

        # Montos en letra
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(
            f"<b>MONTO MÍNIMO CON LETRA:</b> {_monto_a_letra(float(total_min))}",
            bold_left,
        ))
        story.append(Paragraph(
            f"<b>MONTO MÁXIMO CON LETRA:</b> {_monto_a_letra(float(total_max))}",
            bold_left,
        ))

        return story

    def _build_desglose_table(
        self, partida_id, categorias, matriz_partida,
        num_partida, nombre_empresa,
        normal_center, bold_left, small_center,
    ) -> list:
        """Construye tabla de desglose de conceptos (matriz completa)."""
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import mm

        story = []

        # Cargar conceptos
        conceptos_result = (
            self._get_supabase().table('cotizacion_conceptos')
            .select('id, nombre, tipo_concepto, orden')
            .eq('partida_id', partida_id)
            .order('orden')
            .execute()
        )
        conceptos = conceptos_result.data or []
        if not conceptos:
            return story

        # Mapear valor efectivo en pesos por concepto/categoría
        valor_map = {}
        for valor in (matriz_partida or []):
            valor_map.setdefault(valor['concepto_id'], {})[
                valor['partida_categoria_id']
            ] = float(valor.get('valor_calculado') or 0)

        # Encabezados: Concepto | Cat1 | Cat2 ...
        cat_nombres = []
        cat_ids = []
        for cat in categorias:
            cat_data = cat.get('categorias_puesto', {}) or {}
            cat_nombres.append(cat_data.get('nombre', ''))
            cat_ids.append(cat['id'])

        header_row = [Paragraph("<b>Concepto</b>", small_center)] + [
            Paragraph(f"<b>{n}</b>", small_center) for n in cat_nombres
        ]

        rows = [header_row]
        for concepto in conceptos:
            row = [Paragraph(concepto['nombre'], small_center)]
            for cat_id in cat_ids:
                val = valor_map.get(concepto['id'], {}).get(cat_id, 0)
                row.append(Paragraph(f"${val:,.2f}", small_center))
            rows.append(row)

        # Fila total (precio unitario por categoría)
        total_row = [Paragraph("<b>PRECIO UNITARIO</b>", small_center)]
        for cat in categorias:
            precio = float(cat.get('precio_unitario_final', 0))
            total_row.append(Paragraph(f"<b>${precio:,.2f}</b>", small_center))
        rows.append(total_row)

        num_cols = len(cat_nombres) + 1
        col_width_concepto = 6 * cm
        col_width_cat = max(3 * cm, (22 * cm - col_width_concepto) / max(len(cat_nombres), 1))
        col_widths = [col_width_concepto] + [col_width_cat] * len(cat_nombres)

        table = Table(rows, colWidths=col_widths, repeatRows=1)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F0FE')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F8F9FA')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#AAAAAA')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWHEIGHT', (0, 0), (-1, -1), 16),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ])
        table.setStyle(style)

        story.append(Paragraph(
            f"<b>DESGLOSE DE CONCEPTOS — PARTIDA {num_partida}</b>",
            bold_left,
        ))
        story.append(Spacer(1, 2 * mm))
        story.append(table)

        return story

    def _build_firma(self, rep_legal, nombre_empresa, normal_center, bold_left) -> list:
        """Construye el bloque de firma del representante legal."""
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib import colors
        from reportlab.lib.units import mm, cm

        story = []
        story.append(Spacer(1, 8 * mm))

        firma_data = [
            [
                Paragraph("LUGAR Y FECHA: ______________________________", normal_center),
                '',
                Paragraph("A T E N T A M E N T E", normal_center),
            ],
            ['', '', ''],
            ['', '', ''],
            [
                '',
                '',
                Paragraph("_______________________________________", normal_center),
            ],
            [
                '',
                '',
                Paragraph(f"<b>{rep_legal.upper() if rep_legal else nombre_empresa.upper()}</b>", normal_center),
            ],
            [
                '',
                '',
                Paragraph("<b>Representante Legal</b>", normal_center),
            ],
        ]
        firma_table = Table(firma_data, colWidths=[8 * cm, 3 * cm, 12 * cm])
        firma_table.setStyle(TableStyle([
            ('SPAN', (0, 0), (0, 5)),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(firma_table)

        return story


cotizacion_pdf_service = CotizacionPdfService()
