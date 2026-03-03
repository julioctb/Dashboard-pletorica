"""
Generador de layout Fondeadora — CSV estándar.

Fondeadora es una plataforma fintech mexicana que acepta pagos SPEI masivos
mediante un CSV con headers fijos.

Campos:
    clabe_destino, monto, concepto, referencia, nombre_beneficiario

Codificación: UTF-8 sin BOM.
"""
import csv
import io
from datetime import date

from .base import LayoutBancario

_HEADERS = [
    'clabe_destino',
    'monto',
    'concepto',
    'referencia',
    'nombre_beneficiario',
]


class LayoutFondeadora(LayoutBancario):
    """
    Genera archivo CSV para pago masivo en Fondeadora.

    Requisitos Fondeadora:
    - CLABE de 18 dígitos numéricos
    - Monto con 2 decimales (punto decimal)
    - Concepto (máx. 40 chars)
    - Referencia alfanumérica (máx. 30 chars)
    - Nombre beneficiario (máx. 40 chars)
    """

    def validar_datos(self, empleados: list[dict]) -> list[str]:
        errores = []
        for emp in empleados:
            nombre = emp.get('nombre_empleado', '')
            clabe = emp.get('clabe_destino', '')
            monto = float(emp.get('total_neto') or 0)

            if not self.validar_clabe(clabe):
                errores.append(
                    f"{nombre}: CLABE inválida o ausente ({clabe!r})"
                )
            if monto <= 0:
                errores.append(
                    f"{nombre}: monto neto inválido ({monto})"
                )
        return errores

    def generar(
        self,
        empleados: list[dict],
        config: dict,
        periodo: dict,
    ) -> tuple[str, bytes]:
        hoy = date.today()
        fecha_str = hoy.strftime('%Y%m%d')
        referencia_base = (config.get('referencia_pago') or 'NOMINA')[:20]
        concepto = self.normalizar_texto(
            periodo.get('nombre', 'NOMINA'), 40
        ).strip()

        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator='\r\n')
        writer.writerow(_HEADERS)

        for emp in empleados:
            clabe_destino = (emp.get('clabe_destino') or '').strip()
            monto = self.formatear_monto_decimal(
                float(emp.get('total_neto') or 0)
            )
            clave_emp = (emp.get('clave_empleado') or '')[:10]
            referencia = f"{referencia_base}{clave_emp}"[:30]
            nombre_bene = self.normalizar_texto(
                emp.get('nombre_empleado', ''), 40
            ).strip()

            writer.writerow([
                clabe_destino,
                monto,
                concepto,
                referencia,
                nombre_bene,
            ])

        contenido = buffer.getvalue().encode('utf-8')

        nombre_periodo = self.normalizar_texto(
            periodo.get('nombre', 'PERIODO'), 20
        ).strip().replace(' ', '_')
        nombre_archivo = f"FONDEADORA_{nombre_periodo}_{fecha_str}.csv"

        return nombre_archivo, contenido
