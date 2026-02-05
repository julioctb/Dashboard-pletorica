#!/usr/bin/env python3
"""
Script para generar el reporte de código redundante en PDF.
"""
from fpdf import FPDF

class PDFReporte(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, 'Reporte de Codigo Redundante', align='C', new_x='LMARGIN', new_y='NEXT')
        self.set_font('Helvetica', '', 10)
        self.cell(0, 6, 'Dashboard Pletorica - Analisis de Codigo', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')

def crear_reporte():
    pdf = PDFReporte()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Resumen ejecutivo
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, 'RESUMEN EJECUTIVO', fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Se identificaron aproximadamente 386 lineas de codigo redundante o duplicado en el proyecto. Este reporte detalla cada categoria con ejemplos y recomendaciones.')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 6, 'Estadisticas:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(0, 5, '- Lineas duplicadas identificadas: ~386', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(15)
    pdf.cell(0, 5, '- Archivos afectados: 8+', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(15)
    pdf.cell(0, 5, '- Categorias de duplicacion: 6', new_x='LMARGIN', new_y='NEXT')

    # Categoria 1
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, '1. MANEJO DE ERRORES REPETIDO (~80 lineas)', fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Problema:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'El bloque try/except se repite en cada metodo CRUD de TipoServicioState, mientras que EmpresasState tiene un metodo centralizado _manejar_error().')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Archivos afectados:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(0, 5, '- tipo_servicio_state.py: lineas 218-227, 285-295, 309-312', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Codigo duplicado (repetido 4 veces):', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Courier', '', 8)
    pdf.set_fill_color(245, 245, 245)
    codigo1 = '''  except DuplicateError as e:
      self.error_clave = f"La clave ya existe"
  except NotFoundError as e:
      self.mostrar_mensaje(str(e), "error")
  except DatabaseError as e:
      self.mostrar_mensaje(f"Error de BD: {str(e)}", "error")
  except Exception as e:
      self.mostrar_mensaje(f"Error: {str(e)}", "error")'''
    for linea in codigo1.split('\n'):
        pdf.cell(0, 4, linea[:90], fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Solucion recomendada:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Implementar _manejar_error() en TipoServicioState o mejor, en BaseState para uso compartido.')

    # Categoria 2
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, '2. SETTERS EXPLICITOS REPETIDOS (~60 lineas)', fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Problema:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Cada State tiene setters explicitos casi identicos para campos de formulario.')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Archivos afectados:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(0, 5, '- empresas_state.py: lineas 83-134 (15 setters)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(15)
    pdf.cell(0, 5, '- tipo_servicio_state.py: lineas 57-78 (8 setters)', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Patron repetido:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Courier', '', 8)
    pdf.set_fill_color(245, 245, 245)
    codigo2 = '''  def set_form_nombre(self, value: str):
      self.form_nombre = value

  def set_form_clave(self, value: str):
      self.form_clave = value.upper() if value else ""'''
    for linea in codigo2.split('\n'):
        pdf.cell(0, 4, linea[:90], fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Solucion recomendada:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Usar un decorador o metaclase que genere setters automaticamente, o un helper generico en BaseState.')

    # Categoria 3
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, '3. VALIDACION DE CAMPOS REPETIDA (~50 lineas)', fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Problema:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Metodos de validacion en tiempo real son casi identicos entre modulos.')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Archivos afectados:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(0, 5, '- empresas_state.py: lineas 332-364 (6 validadores)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(15)
    pdf.cell(0, 5, '- tipo_servicio_state.py: lineas 83-99 (3 validadores)', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Patron repetido:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Courier', '', 8)
    pdf.set_fill_color(245, 245, 245)
    codigo3 = '''  def validar_nombre_campo(self):
      self.error_nombre = validar_nombre(self.form_nombre)

  def validar_clave_campo(self):
      self.error_clave = validar_clave(self.form_clave)'''
    for linea in codigo3.split('\n'):
        pdf.cell(0, 4, linea[:90], fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Solucion recomendada:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Crear un mixin o helper generico para validacion en tiempo real.')

    # Categoria 4
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, '4. OPERACIONES DE MODAL DUPLICADAS (~40 lineas)', fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Problema:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'abrir_modal_crear, cerrar_modal, limpiar_formulario siguen patrones casi identicos.')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Archivos afectados:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(0, 5, '- empresas_state.py: lineas 256-298', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(15)
    pdf.cell(0, 5, '- tipo_servicio_state.py: lineas 166-198', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Patron repetido:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Courier', '', 8)
    pdf.set_fill_color(245, 245, 245)
    codigo4 = '''  def abrir_modal_crear(self):
      self.limpiar_formulario()
      self.modo_modal = "crear"
      self.mostrar_modal = True

  def cerrar_modal(self):
      self.mostrar_modal = False
      self.limpiar_formulario()'''
    for linea in codigo4.split('\n'):
        pdf.cell(0, 4, linea[:90], fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Solucion recomendada:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Crear ModalMixin en BaseState con logica generica de modales.')

    # Categoria 5
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, '5. CARGA DE DATOS CON TRY/EXCEPT (~30 lineas)', fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Problema:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'cargar_empresas y cargar_tipos tienen estructura identica.')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Patron repetido:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Courier', '', 8)
    pdf.set_fill_color(245, 245, 245)
    codigo5 = '''  async def cargar_datos(self):
      self.loading = True
      try:
          self.datos = await servicio.obtener_todas(...)
      except DatabaseError as e:
          self.mostrar_mensaje(f"Error: {e}", "error")
          self.datos = []
      finally:
          self.loading = False'''
    for linea in codigo5.split('\n'):
        pdf.cell(0, 4, linea[:90], fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Solucion recomendada:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Crear decorador @with_loading que maneje el patron loading/try/except/finally.')

    # Categoria 6
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, '6. PROPIEDADES CALCULADAS SIMILARES (~26 lineas)', fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Problema:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'tiene_errores_formulario es casi identico entre modulos.')
    pdf.ln(1)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Patron repetido:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Courier', '', 8)
    pdf.set_fill_color(245, 245, 245)
    codigo6 = '''  @rx.var
  def tiene_errores_formulario(self) -> bool:
      return bool(
          self.error_campo1 or
          self.error_campo2 or
          self.error_campo3
      )'''
    for linea in codigo6.split('\n'):
        pdf.cell(0, 4, linea[:90], fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(2)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Solucion recomendada:', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, 'Definir lista de campos de error y verificar dinamicamente en BaseState.')

    # Plan de accion
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, 'PLAN DE ACCION RECOMENDADO', fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Fase 1 - Alta prioridad (reduce ~130 lineas):', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(0, 5, '[ ] Implementar _manejar_error() en BaseState', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(15)
    pdf.cell(0, 5, '[ ] Crear ModalMixin con logica generica', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(15)
    pdf.cell(0, 5, '[ ] Crear decorador @with_loading', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(3)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Fase 2 - Media prioridad (reduce ~110 lineas):', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(0, 5, '[ ] Crear ValidacionMixin generico', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(15)
    pdf.cell(0, 5, '[ ] Crear helper para setters con transformacion', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(3)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Fase 3 - Mejoras opcionales (reduce ~46 lineas):', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(15)
    pdf.cell(0, 5, '[ ] Refactorizar propiedades calculadas', new_x='LMARGIN', new_y='NEXT')
    pdf.set_x(15)
    pdf.cell(0, 5, '[ ] Unificar estructura de filtros', new_x='LMARGIN', new_y='NEXT')

    # Tabla de archivos
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, 'ARCHIVOS AFECTADOS', fill=True, new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)
    pdf.set_font('Helvetica', '', 9)

    archivos = [
        ('empresas_state.py', '#1, #2, #3, #4, #5, #6'),
        ('tipo_servicio_state.py', '#1, #2, #3, #4, #5, #6'),
        ('base_state.py', 'Destino de refactorizacion'),
        ('empresas_validators.py', '#3'),
        ('tipo_servicio_validators.py', '#3'),
    ]

    for archivo, categorias in archivos:
        pdf.cell(80, 6, archivo, border=1)
        pdf.cell(0, 6, categorias, border=1, new_x='LMARGIN', new_y='NEXT')

    # Nota final
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.cell(0, 5, 'Generado por Claude Code - Dashboard Pletorica', align='C')

    # Guardar
    pdf.output('/Users/julioctb/Desktop/Dashboard-pletorica/REPORTE_CODIGO_REDUNDANTE.pdf')
    print("PDF generado: REPORTE_CODIGO_REDUNDANTE.pdf")

if __name__ == "__main__":
    crear_reporte()
