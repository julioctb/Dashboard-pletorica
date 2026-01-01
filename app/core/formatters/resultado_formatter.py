"""
Formateador de resultados para presentación.

Responsabilidad: Transformar ResultadoCuotas en formatos legibles para:
- Terminal/consola (texto plano con formato)
- UI web (diccionario de strings formateados)
- Reportes PDF (futuro)

Separado del código de cálculo para mantener Single Responsibility Principle.
El formateo es presentación, no lógica de negocio.

Fecha: 2025-12-31 (Fase 3 de refactorización)
"""

from app.entities.costo_patronal import ResultadoCuotas


class ResultadoFormatter:
    """
    Formateador de resultados de costo patronal.

    Convierte ResultadoCuotas en formatos legibles para diferentes
    canales de salida (terminal, web, reportes).
    """

    @staticmethod
    def formatear_terminal(r: ResultadoCuotas) -> str:
        """
        Formatea resultado para impresión en terminal.

        Genera un reporte de texto plano con formato para consola,
        incluyendo emojis, alineación y separadores visuales.

        Args:
            r: ResultadoCuotas a formatear

        Returns:
            String formateado listo para print()

        Ejemplo:
            >>> from app.core.formatters import ResultadoFormatter
            >>> texto = ResultadoFormatter.formatear_terminal(resultado)
            >>> print(texto)
        """
        lines = []

        # ═════════════════════════════════════════════════════════════════════
        # ENCABEZADO
        # ═════════════════════════════════════════════════════════════════════
        lines.append("\n" + "="*65)
        lines.append(f"COSTO PATRONAL: {r.trabajador}")
        lines.append(f"Empresa: {r.empresa}")
        lines.append("="*65)

        # Advertencia para salario mínimo
        if r.es_salario_minimo:
            lines.append("\n   ⚠️  SALARIO MÍNIMO:")
            lines.append("       • Exento de retención ISR (Art. 96 LISR)")
            lines.append("       • Cuota obrera IMSS la paga el patrón (Art. 36 LSS)")

        # ═════════════════════════════════════════════════════════════════════
        # SALARIOS
        # ═════════════════════════════════════════════════════════════════════
        lines.append(f"\n📋 SALARIO")
        lines.append(f"   Salario diario:            ${r.salario_diario:>12,.2f}")
        lines.append(f"   Días cotizados:            {r.dias_cotizados:>12}")
        lines.append(f"   Salario mensual:           ${r.salario_mensual:>12,.2f}")

        # ═════════════════════════════════════════════════════════════════════
        # INTEGRACIÓN
        # ═════════════════════════════════════════════════════════════════════
        lines.append(f"\n📊 INTEGRACIÓN")
        lines.append(f"   Factor de integración:     {r.factor_integracion:>13.4f}")
        lines.append(f"   SBC diario:                ${r.sbc_diario:>12,.2f}")
        lines.append(f"   SBC mensual:               ${r.sbc_mensual:>12,.2f}")

        # ═════════════════════════════════════════════════════════════════════
        # IMSS PATRONAL
        # ═════════════════════════════════════════════════════════════════════
        lines.append(f"\n🏥 IMSS PATRONAL")
        lines.append(f"   Cuota fija (E.M.):         ${r.imss_cuota_fija:>12,.2f}")
        lines.append(f"   Excedente (E.M.):          ${r.imss_excedente_pat:>12,.2f}")
        lines.append(f"   Prest. en dinero (E.M.):   ${r.imss_prest_dinero_pat:>12,.2f}")
        lines.append(f"   Gastos méd. pensionados:   ${r.imss_gastos_med_pens_pat:>12,.2f}")
        lines.append(f"   Invalidez y vida:          ${r.imss_invalidez_vida_pat:>12,.2f}")
        lines.append(f"   Guarderías:                ${r.imss_guarderias:>12,.2f}")
        lines.append(f"   Retiro:                    ${r.imss_retiro:>12,.2f}")
        lines.append(f"   Cesantía y vejez (3.513%): ${r.imss_cesantia_vejez_pat:>12,.2f}")
        lines.append(f"   Riesgo de trabajo:         ${r.imss_riesgo_trabajo:>12,.2f}")
        lines.append(f"   ─────────────────────────────────────────────")
        lines.append(f"   TOTAL IMSS PATRONAL:       ${r.total_imss_patronal:>12,.2f}")

        # ═════════════════════════════════════════════════════════════════════
        # ART. 36 LSS (condicional)
        # ═════════════════════════════════════════════════════════════════════
        if r.imss_obrero_absorbido > 0:
            lines.append(f"\n⚖️  ART. 36 LSS - CUOTA OBRERA (patrón paga)")
            lines.append(f"   IMSS obrero absorbido:     ${r.imss_obrero_absorbido:>12,.2f}")

        # ═════════════════════════════════════════════════════════════════════
        # INFONAVIT
        # ═════════════════════════════════════════════════════════════════════
        lines.append(f"\n🏠 INFONAVIT (5%)")
        lines.append(f"   Aportación patronal:       ${r.infonavit:>12,.2f}")

        # ═════════════════════════════════════════════════════════════════════
        # ISN
        # ═════════════════════════════════════════════════════════════════════
        lines.append(f"\n💰 ISN")
        lines.append(f"   Impuesto sobre nómina:     ${r.isn:>12,.2f}")

        # ═════════════════════════════════════════════════════════════════════
        # PROVISIONES
        # ═════════════════════════════════════════════════════════════════════
        lines.append(f"\n📅 PROVISIONES MENSUALES")
        lines.append(f"   Aguinaldo:                 ${r.provision_aguinaldo:>12,.2f}")
        lines.append(f"   Vacaciones:                ${r.provision_vacaciones:>12,.2f}")
        lines.append(f"   Prima vacacional:          ${r.provision_prima_vac:>12,.2f}")
        lines.append(f"   ─────────────────────────────────────────────")
        lines.append(f"   TOTAL PROVISIONES:         ${r.total_provisiones:>12,.2f}")

        # ═════════════════════════════════════════════════════════════════════
        # DESCUENTOS AL TRABAJADOR
        # ═════════════════════════════════════════════════════════════════════
        lines.append(f"\n👷 DESCUENTOS AL TRABAJADOR")
        if r.es_salario_minimo:
            lines.append(f"   IMSS Obrero:               $        0.00  (Art. 36 LSS)")
            lines.append(f"   ISR:                       $        0.00  (Art. 96 LISR)")
        else:
            lines.append(f"   IMSS Obrero:               ${r.total_imss_obrero:>12,.2f}")
            lines.append(f"   ISR a retener:             ${r.isr_a_retener:>12,.2f}")
        lines.append(f"   ─────────────────────────────────────────────")
        lines.append(f"   TOTAL DESCUENTOS:          ${r.total_descuentos_trabajador:>12,.2f}")

        # ═════════════════════════════════════════════════════════════════════
        # TOTALES FINALES
        # ═════════════════════════════════════════════════════════════════════
        lines.append(f"\n" + "="*65)
        lines.append(f"💵 COSTO TOTAL PATRONAL:      ${r.costo_total:>12,.2f}")
        lines.append(f"📈 FACTOR DE COSTO:           {r.factor_costo:>13.4f}")
        lines.append(f"   (El trabajador cuesta {r.factor_costo:.2%} de su salario nominal)")
        lines.append("="*65)
        lines.append(f"💰 SALARIO NETO TRABAJADOR:   ${r.salario_neto:>12,.2f}")
        lines.append("="*65)

        return "\n".join(lines)

    @staticmethod
    def formatear_para_ui(r: ResultadoCuotas) -> dict[str, str]:
        """
        Formatea resultado para interfaz web (Reflex).

        Convierte todos los valores numéricos a strings formateados
        para mostrar en componentes UI.

        Args:
            r: ResultadoCuotas a formatear

        Returns:
            Diccionario con todos los campos como strings formateados

        Ejemplo:
            >>> from app.core.formatters import ResultadoFormatter
            >>> ui_data = ResultadoFormatter.formatear_para_ui(resultado)
            >>> # En Reflex:
            >>> rx.text(ui_data["costo_total"])  # "$ 12,345.67"
        """
        return {
            # Salarios
            "salario_diario": f"$ {r.salario_diario:,.2f}",
            "salario_mensual": f"$ {r.salario_mensual:,.2f}",
            "factor_integracion": f"{r.factor_integracion:.4f}",
            "sbc_diario": f"$ {r.sbc_diario:,.2f}",
            "sbc_mensual": f"$ {r.sbc_mensual:,.2f}",
            "dias_cotizados": str(r.dias_cotizados),

            # IMSS Patronal
            "imss_cuota_fija": f"$ {r.imss_cuota_fija:,.2f}",
            "imss_excedente_pat": f"$ {r.imss_excedente_pat:,.2f}",
            "imss_prest_dinero_pat": f"$ {r.imss_prest_dinero_pat:,.2f}",
            "imss_gastos_med_pens_pat": f"$ {r.imss_gastos_med_pens_pat:,.2f}",
            "imss_invalidez_vida_pat": f"$ {r.imss_invalidez_vida_pat:,.2f}",
            "imss_guarderias": f"$ {r.imss_guarderias:,.2f}",
            "imss_retiro": f"$ {r.imss_retiro:,.2f}",
            "imss_cesantia_vejez_pat": f"$ {r.imss_cesantia_vejez_pat:,.2f}",
            "imss_riesgo_trabajo": f"$ {r.imss_riesgo_trabajo:,.2f}",

            # IMSS Obrero
            "imss_excedente_obr": f"$ {r.imss_excedente_obr:,.2f}",
            "imss_prest_dinero_obr": f"$ {r.imss_prest_dinero_obr:,.2f}",
            "imss_gastos_med_pens_obr": f"$ {r.imss_gastos_med_pens_obr:,.2f}",
            "imss_invalidez_vida_obr": f"$ {r.imss_invalidez_vida_obr:,.2f}",
            "imss_cesantia_vejez_obr": f"$ {r.imss_cesantia_vejez_obr:,.2f}",

            # Art. 36 LSS
            "imss_obrero_absorbido": f"$ {r.imss_obrero_absorbido:,.2f}",
            "es_salario_minimo": r.es_salario_minimo,

            # Otros
            "infonavit": f"$ {r.infonavit:,.2f}",
            "isn": f"$ {r.isn:,.2f}",

            # Provisiones
            "provision_aguinaldo": f"$ {r.provision_aguinaldo:,.2f}",
            "provision_vacaciones": f"$ {r.provision_vacaciones:,.2f}",
            "provision_prima_vac": f"$ {r.provision_prima_vac:,.2f}",

            # ISR
            "isr_a_retener": f"$ {r.isr_a_retener:,.2f}",

            # Totales (propiedades calculadas)
            "total_imss_patronal": f"$ {r.total_imss_patronal:,.2f}",
            "total_imss_obrero": f"$ {r.total_imss_obrero:,.2f}",
            "total_provisiones": f"$ {r.total_provisiones:,.2f}",
            "total_carga_patronal": f"$ {r.total_carga_patronal:,.2f}",
            "costo_total": f"$ {r.costo_total:,.2f}",
            "factor_costo": f"{r.factor_costo:.4f}",
            "salario_neto": f"$ {r.salario_neto:,.2f}",
        }

    @staticmethod
    def imprimir(r: ResultadoCuotas) -> None:
        """
        Imprime resultado en terminal (wrapper conveniente).

        Args:
            r: ResultadoCuotas a imprimir

        Ejemplo:
            >>> from app.core.formatters import ResultadoFormatter
            >>> ResultadoFormatter.imprimir(resultado)
        """
        print(ResultadoFormatter.formatear_terminal(r))
