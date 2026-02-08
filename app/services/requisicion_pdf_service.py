"""
Servicio para generar PDFs de requisiciones aprobadas.

Genera un documento tipo formulario con:
- Header institucional BUAP
- Datos de la requisición
- Tabla de items (sin precios)
- Partidas presupuestales
- Condiciones y garantías
- Sección de firmas
- Información de aprobación
"""
import logging
from io import BytesIO
from datetime import date

from fpdf import FPDF

from app.core.enums import EstadoRequisicion
from app.core.exceptions import BusinessRuleError
from app.core.text_utils import formatear_fecha_es
from app.services.requisicion_service import requisicion_service

logger = logging.getLogger(__name__)

# Estados mínimos para generar PDF
ESTADOS_PERMITIDOS_PDF = {
    EstadoRequisicion.APROBADA,
    EstadoRequisicion.ADJUDICADA,
    EstadoRequisicion.CONTRATADA,
}


class RequisicionPDF(FPDF):
    """PDF personalizado para requisiciones BUAP."""

    def header(self):
        """Header institucional."""
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 8, "BENEMERITA UNIVERSIDAD AUTONOMA DE PUEBLA", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 6, "SECRETARIA ADMINISTRATIVA", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.cell(0, 5, "Requisicion de Bienes y/o Servicios", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        # Línea separadora
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        """Footer con número de página."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

    def seccion_titulo(self, titulo: str):
        """Título de sección con fondo coloreado."""
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 51, 102)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, f"  {titulo}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def campo_valor(self, campo: str, valor: str, campo_width: int = 45):
        """Campo: Valor en una línea."""
        self.set_font("Helvetica", "B", 8)
        self.cell(campo_width, 5, campo + ":", new_x="END")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, valor or "-", new_x="LMARGIN", new_y="NEXT")

    def campo_valor_doble(self, c1: str, v1: str, c2: str, v2: str):
        """Dos campos en la misma línea."""
        ancho = 95
        self.set_font("Helvetica", "B", 8)
        self.cell(35, 5, c1 + ":", new_x="END")
        self.set_font("Helvetica", "", 8)
        self.cell(ancho - 35, 5, v1 or "-", new_x="END")
        self.set_font("Helvetica", "B", 8)
        self.cell(35, 5, c2 + ":", new_x="END")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 5, v2 or "-", new_x="LMARGIN", new_y="NEXT")


class RequisicionPDFService:
    """Servicio para generar PDFs de requisiciones."""

    async def generar_pdf(self, requisicion_id: int) -> bytes:
        """
        Genera el PDF de una requisición aprobada.

        Args:
            requisicion_id: ID de la requisición

        Returns:
            Bytes del PDF generado

        Raises:
            BusinessRuleError: Si la requisición no está en estado válido para PDF
        """
        requisicion = await requisicion_service.obtener_por_id(requisicion_id)

        estado = EstadoRequisicion(requisicion.estado)
        if estado not in ESTADOS_PERMITIDOS_PDF:
            raise BusinessRuleError(
                f"Solo se puede generar PDF de requisiciones aprobadas o posteriores. "
                f"Estado actual: {estado.value}"
            )

        pdf = RequisicionPDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=20)

        # --- Datos generales ---
        pdf.seccion_titulo("DATOS GENERALES")
        pdf.campo_valor_doble(
            "No. Requisicion", requisicion.numero_requisicion,
            "Fecha Elaboracion", str(requisicion.fecha_elaboracion),
        )
        pdf.campo_valor_doble(
            "Estado", str(requisicion.estado),
            "Tipo Contratacion", str(requisicion.tipo_contratacion),
        )
        pdf.campo_valor("Objeto de contratacion", requisicion.objeto_contratacion)
        pdf.campo_valor("Justificacion", requisicion.justificacion)
        pdf.ln(2)

        # --- Área requirente ---
        pdf.seccion_titulo("AREA REQUIRENTE")
        pdf.campo_valor("Dependencia", requisicion.dependencia_requirente)
        pdf.campo_valor("Domicilio", requisicion.domicilio)
        pdf.campo_valor_doble(
            "Titular", requisicion.titular_nombre,
            "Cargo", requisicion.titular_cargo,
        )
        if requisicion.titular_telefono or requisicion.titular_email:
            pdf.campo_valor_doble(
                "Telefono", requisicion.titular_telefono or "",
                "Email", requisicion.titular_email or "",
            )
        if requisicion.coordinador_nombre:
            pdf.campo_valor_doble(
                "Coordinador", requisicion.coordinador_nombre,
                "Tel.", requisicion.coordinador_telefono or "",
            )
        if requisicion.asesor_nombre:
            pdf.campo_valor_doble(
                "Asesor", requisicion.asesor_nombre,
                "Tel.", requisicion.asesor_telefono or "",
            )
        pdf.ln(2)

        # --- Condiciones de entrega ---
        pdf.seccion_titulo("CONDICIONES DE ENTREGA")
        pdf.campo_valor("Lugar de entrega", requisicion.lugar_entrega)
        if requisicion.inicio_desde_firma and requisicion.fecha_entrega_fin:
            fecha_fin_es = formatear_fecha_es(requisicion.fecha_entrega_fin)
            pdf.campo_valor(
                "Periodo",
                f"A partir de la firma del contrato y hasta el {fecha_fin_es}",
            )
        elif requisicion.fecha_entrega_inicio and requisicion.fecha_entrega_fin:
            fecha_inicio_es = formatear_fecha_es(requisicion.fecha_entrega_inicio)
            fecha_fin_es = formatear_fecha_es(requisicion.fecha_entrega_fin)
            pdf.campo_valor(
                "Periodo",
                f"Del {fecha_inicio_es} al {fecha_fin_es}",
            )
        elif requisicion.fecha_entrega_inicio:
            pdf.campo_valor("Fecha inicio", formatear_fecha_es(requisicion.fecha_entrega_inicio))
        if requisicion.condiciones_entrega:
            pdf.campo_valor("Condiciones", requisicion.condiciones_entrega)
        if requisicion.tipo_garantia:
            pdf.campo_valor_doble(
                "Tipo garantia", requisicion.tipo_garantia,
                "Vigencia", requisicion.garantia_vigencia or "-",
            )
        if requisicion.forma_pago:
            pdf.campo_valor("Forma de pago", requisicion.forma_pago)

        opciones = []
        if requisicion.requiere_anticipo:
            opciones.append("Requiere anticipo")
        if requisicion.requiere_muestras:
            opciones.append("Requiere muestras")
        if requisicion.requiere_visita:
            opciones.append("Requiere visita")
        if opciones:
            pdf.campo_valor("Requisitos", ", ".join(opciones))

        if requisicion.requisitos_proveedor:
            pdf.campo_valor("Requisitos proveedor", requisicion.requisitos_proveedor)
        pdf.ln(2)

        # --- Tabla de items (SIN precios) ---
        if requisicion.items:
            pdf.seccion_titulo("ITEMS SOLICITADOS")
            self._tabla_items(pdf, requisicion.items)
            pdf.ln(2)

        # --- Disponibilidad presupuestal ---
        if any([requisicion.partida_presupuestaria, requisicion.origen_recurso,
                requisicion.oficio_suficiencia]):
            pdf.seccion_titulo("DISPONIBILIDAD PRESUPUESTAL")
            if requisicion.partida_presupuestaria:
                pdf.campo_valor("Partida presupuestaria", requisicion.partida_presupuestaria)
            if requisicion.origen_recurso:
                pdf.campo_valor("Origen del recurso", requisicion.origen_recurso)
            if requisicion.oficio_suficiencia:
                pdf.campo_valor("No. Oficio de Suficiencia", requisicion.oficio_suficiencia)
            pdf.ln(2)

        # --- PDI ---
        if any([requisicion.pdi_eje, requisicion.pdi_objetivo,
                requisicion.pdi_estrategia, requisicion.pdi_meta]):
            pdf.seccion_titulo("PLAN DE DESARROLLO INSTITUCIONAL")
            if requisicion.pdi_eje:
                pdf.campo_valor("Eje", requisicion.pdi_eje)
            if requisicion.pdi_objetivo:
                pdf.campo_valor("Objetivo", requisicion.pdi_objetivo)
            if requisicion.pdi_estrategia:
                pdf.campo_valor("Estrategia", requisicion.pdi_estrategia)
            if requisicion.pdi_meta:
                pdf.campo_valor("Meta", requisicion.pdi_meta)
            pdf.ln(2)

        # --- Observaciones ---
        if requisicion.observaciones:
            pdf.seccion_titulo("OBSERVACIONES")
            pdf.set_font("Helvetica", "", 8)
            pdf.multi_cell(0, 4, requisicion.observaciones)
            pdf.ln(2)

        # --- Firmas ---
        pdf.seccion_titulo("FIRMAS")
        pdf.ln(15)

        # Fila de firmas
        ancho_firma = 60
        x_inicio = 15
        y_firma = pdf.get_y()

        # Firma: Elabora
        pdf.set_xy(x_inicio, y_firma)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(ancho_firma, 4, "_" * 35, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(x_inicio)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(ancho_firma, 4, requisicion.elabora_nombre, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(x_inicio)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(ancho_firma, 4, requisicion.elabora_cargo, align="C", new_x="LMARGIN", new_y="NEXT")

        # Firma: Solicita
        pdf.set_xy(x_inicio + 65, y_firma)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(ancho_firma, 4, "_" * 35, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_xy(x_inicio + 65, y_firma + 4)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(ancho_firma, 4, requisicion.solicita_nombre, align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_xy(x_inicio + 65, y_firma + 8)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(ancho_firma, 4, requisicion.solicita_cargo, align="C", new_x="LMARGIN", new_y="NEXT")

        # Firma: Validación asesor (si existe)
        if requisicion.validacion_asesor:
            pdf.set_xy(x_inicio + 130, y_firma)
            pdf.set_font("Helvetica", "", 7)
            pdf.cell(ancho_firma, 4, "_" * 35, align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_xy(x_inicio + 130, y_firma + 4)
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(ancho_firma, 4, requisicion.validacion_asesor, align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.set_xy(x_inicio + 130, y_firma + 8)
            pdf.set_font("Helvetica", "", 7)
            pdf.cell(ancho_firma, 4, "Vo.Bo. Asesor", align="C", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(8)

        # --- Información de aprobación ---
        if requisicion.fecha_aprobacion:
            pdf.seccion_titulo("INFORMACION DE APROBACION")
            pdf.campo_valor("Fecha de aprobacion", str(requisicion.fecha_aprobacion))
            if requisicion.aprobado_por:
                pdf.campo_valor("Aprobado por (ID)", requisicion.aprobado_por)

        # --- Información de adjudicación ---
        if requisicion.empresa_id and requisicion.fecha_adjudicacion:
            pdf.seccion_titulo("ADJUDICACION")
            pdf.campo_valor("Fecha adjudicacion", str(requisicion.fecha_adjudicacion))
            # Intentar obtener nombre de empresa
            try:
                from app.services.empresa_service import empresa_service
                empresa = await empresa_service.obtener_por_id(requisicion.empresa_id)
                pdf.campo_valor("Empresa adjudicada", empresa.nombre_comercial)
            except Exception:
                pdf.campo_valor("Empresa ID", str(requisicion.empresa_id))

        return pdf.output()

    def _tabla_items(self, pdf: RequisicionPDF, items: list):
        """Renderiza tabla de items sin precios."""
        # Header
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(10, 5, "#", border=1, fill=True, align="C", new_x="END")
        pdf.cell(25, 5, "Unidad", border=1, fill=True, align="C", new_x="END")
        pdf.cell(15, 5, "Cant.", border=1, fill=True, align="C", new_x="END")
        pdf.cell(140, 5, "Descripcion", border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

        # Filas
        pdf.set_font("Helvetica", "", 7)
        for item in items:
            pdf.cell(10, 5, str(item.numero_item), border=1, align="C", new_x="END")
            pdf.cell(25, 5, str(item.unidad_medida)[:15], border=1, align="C", new_x="END")
            pdf.cell(15, 5, str(item.cantidad), border=1, align="C", new_x="END")

            # Descripción puede ser larga
            desc = str(item.descripcion)[:120]
            pdf.cell(140, 5, desc, border=1, new_x="LMARGIN", new_y="NEXT")



# Singleton
requisicion_pdf_service = RequisicionPDFService()
