"""
Generador de layout HSBC — TXT delimitado por pipes (|).

Formato: archivo de texto con campos delimitados por '|'.
Cada línea representa un movimiento de pago SPEI saliente.

Campos por línea:
    cuenta_cargo | cuenta_abono | importe | moneda | referencia |
    concepto | nombre_beneficiario

Codificación: UTF-8 con BOM (requerido por HSBC Net).
"""
from datetime import date

from .base import LayoutBancario

_MONEDA = 'MXP'
_SEPARADOR = '|'
_ENCODING = 'utf-8-sig'   # UTF-8 con BOM
_CRLF = '\r\n'

_CABECERA = (
    'CUENTA_CARGO|CUENTA_ABONO|IMPORTE|MONEDA|REFERENCIA|CONCEPTO|NOMBRE_BENEFICIARIO'
)


class LayoutHSBC(LayoutBancario):
    """
    Genera archivo TXT delimitado por pipes para pago masivo en HSBC Net.

    Requisitos HSBC:
    - CLABE destino de 18 dígitos numéricos
    - Importe con 2 decimales, punto como separador decimal
    - Referencia numérica o alfanumérica (máx. 30 chars)
    - Concepto (máx. 40 chars)
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
        cuenta_cargo = config.get('clabe_origen') or config.get('cuenta_origen') or ''
        referencia_base = (config.get('referencia_pago') or 'NOMINA')[:30]
        concepto_base = self.normalizar_texto(
            periodo.get('nombre', 'NOMINA'), 40
        ).strip()

        lineas: list[str] = [_CABECERA]

        for emp in empleados:
            clabe_destino = (emp.get('clabe_destino') or '').strip()
            importe = self.formatear_monto_decimal(
                float(emp.get('total_neto') or 0)
            )
            nombre_bene = self.normalizar_texto(
                emp.get('nombre_empleado', ''), 40
            ).strip()

            # La referencia puede combinar el periodo con la clave del empleado
            clave_emp = (emp.get('clave_empleado') or '')[:10]
            referencia = f"{referencia_base[:20]}{clave_emp}"[:30]

            linea = _SEPARADOR.join([
                cuenta_cargo,
                clabe_destino,
                importe,
                _MONEDA,
                referencia,
                concepto_base,
                nombre_bene,
            ])
            lineas.append(linea)

        contenido_texto = _CRLF.join(lineas) + _CRLF
        contenido = contenido_texto.encode(_ENCODING)

        nombre_periodo = self.normalizar_texto(
            periodo.get('nombre', 'PERIODO'), 20
        ).strip().replace(' ', '_')
        nombre_archivo = f"HSBC_{nombre_periodo}_{fecha_str}.txt"

        return nombre_archivo, contenido
