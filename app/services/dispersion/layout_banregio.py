"""
Generador de layout Banregio — Texto de posiciones fijas.

Formato: archivo TXT con registros de longitud fija (120 chars + CRLF).

Estructura:
    Encabezado (tipo 'H'): fecha, nombre empresa, num_registros
    Detalle    (tipo 'D'): CLABE destino, monto (centavos), nombre, referencia
    Totalizador (tipo 'T'): num_registros, suma de montos

Codificación: Latin-1 (CP1252 compatible con sistemas bancarios mexicanos).
"""
from datetime import date, datetime

from .base import LayoutBancario

# Longitud fija de cada registro (sin CRLF)
_ANCHO_LINEA = 120
_ENCODING = 'latin-1'
_CRLF = b'\r\n'


def _linea(contenido: str) -> bytes:
    """Padding a _ANCHO_LINEA chars y encoda a Latin-1 + CRLF."""
    return (contenido[:_ANCHO_LINEA].ljust(_ANCHO_LINEA)).encode(_ENCODING) + _CRLF


class LayoutBanregio(LayoutBancario):
    """
    Genera archivo TXT de posiciones fijas para pago masivo en Banregio.

    Campos del registro de detalle (120 chars):
    Col  1-1   : Tipo registro  ('D')
    Col  2-19  : CLABE destino  (18 dígitos)
    Col 20-36  : Monto centavos (17 dígitos, relleno ceros a la izquierda)
    Col 37-76  : Nombre bene    (40 chars, relleno espacios a la derecha)
    Col 77-106 : Referencia     (30 chars, relleno espacios a la derecha)
    Col 107-120: Espacios libres (14)
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
        referencia_base = (config.get('referencia_pago') or 'NOMINA')[:30]
        num_registros = len(empleados)
        total_centavos = sum(round(float(emp.get('total_neto') or 0) * 100) for emp in empleados)

        lineas: list[bytes] = []

        # ── Encabezado ────────────────────────────────────────────────────────
        # H + fecha(8) + nombre_empresa(35) + num_registros(7) + total_cents(17) + libres(53)
        nombre_empresa = self.normalizar_texto(
            config.get('referencia_pago') or 'EMPRESA', 35
        )
        encabezado = (
            'H'
            + fecha_str                          # 8 chars
            + nombre_empresa                     # 35 chars
            + str(num_registros).zfill(7)        # 7 chars
            + str(total_centavos).zfill(17)      # 17 chars
        )
        lineas.append(_linea(encabezado))

        # ── Detalles ──────────────────────────────────────────────────────────
        for emp in empleados:
            clabe = (emp.get('clabe_destino') or '').ljust(18)[:18]
            monto_cents = str(round(float(emp.get('total_neto') or 0) * 100)).zfill(17)
            nombre = self.normalizar_texto(emp.get('nombre_empleado', ''), 40)
            referencia = self.normalizar_texto(referencia_base, 30)

            detalle = (
                'D'        # 1
                + clabe    # 18
                + monto_cents  # 17
                + nombre   # 40
                + referencia   # 30
                # 14 libres → ljust en _linea lo rellena
            )
            lineas.append(_linea(detalle))

        # ── Totalizador ───────────────────────────────────────────────────────
        # T + num_registros(7) + total_centavos(17) + libres(95)
        totalizador = (
            'T'
            + str(num_registros).zfill(7)
            + str(total_centavos).zfill(17)
        )
        lineas.append(_linea(totalizador))

        contenido = b''.join(lineas)
        nombre_periodo = self.normalizar_texto(
            periodo.get('nombre', 'PERIODO'), 20
        ).strip().replace(' ', '_')
        nombre_archivo = f"BANREGIO_{nombre_periodo}_{fecha_str}.txt"

        return nombre_archivo, contenido
