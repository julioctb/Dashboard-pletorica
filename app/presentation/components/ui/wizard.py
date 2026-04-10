"""Componentes visuales reusables para wizards multi-paso.

Centraliza el `wizard_stepper` para evitar que cada página reimplementa
su propio indicador de pasos. Hoy hay tres usos:

    - `alta_masiva` portal (3 pasos)              — `employee_bulk_upload_kit`
    - `requisiciones` backoffice (8 pasos)        — `requisicion_form`
    - `mis_contratos` extensión portal (3 pasos)  — `mis_contratos`

El primer y segundo llamador tienen su propio `_indicador_pasos` local
(duplicación histórica). Este módulo ofrece una implementación única y
parametrizable; los callers legados pueden migrar cuando se toquen por
otra razón.

Semántica del estado del círculo (igual que `employee_bulk_upload_kit`):
    - `current_step == step_num` → paso actual (bold, highlight)
    - `current_step > step_num`  → paso ya completado (highlight filled)
    - `current_step < step_num`  → paso futuro (outline, muted)
"""
from __future__ import annotations

from typing import Callable, Sequence

import reflex as rx

from app.presentation.theme import Colors, Radius, Spacing, Typography


def wizard_stepper(
    steps: Sequence[tuple[int, str]],
    current_step,
    *,
    on_step_click: Callable | None = None,
    accent_color: str | None = None,
    show_labels: bool = True,
) -> rx.Component:
    """Indicador visual de pasos para un wizard multi-paso.

    Args:
        steps: Secuencia de tuplas `(numero_paso, label)`. Ej:
            `[(1, "Vigencia"), (2, "Categorías"), (4, "Confirmar")]`.
            Los números no necesitan ser consecutivos (se admite saltar
            pasos como en mis_contratos donde 3 está reservado).
        current_step: Var reactivo (o int) con el paso activo.
        on_step_click: Callback opcional invocado con el número de paso
            cuando el usuario hace click en un círculo. Si es `None`, los
            círculos no son clickeables.
        accent_color: Color del círculo activo/completado. Default
            `Colors.PORTAL_PRIMARY`. Para backoffice pasa `Colors.PRIMARY`.
        show_labels: Si `False`, muestra solo los círculos sin texto.
            Útil para versiones compactas en breakpoints pequeños.

    Returns:
        Componente `rx.flex` que renderiza los círculos + conectores.
    """
    if not steps:
        return rx.fragment()

    accent = accent_color or Colors.PORTAL_PRIMARY
    total = len(steps)

    def _circulo(step_num: int) -> rx.Component:
        es_actual = current_step == step_num
        es_completado_o_actual = current_step >= step_num
        background = rx.cond(es_completado_o_actual, accent, Colors.SURFACE)
        color_num = rx.cond(
            es_completado_o_actual, Colors.TEXT_INVERSE, Colors.TEXT_SECONDARY
        )
        circulo = rx.center(
            rx.text(
                str(step_num),
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_BOLD,
                color=color_num,
            ),
            background=background,
            border=f"2px solid {accent}",
            border_radius="50%",
            width="30px",
            height="30px",
            flex_shrink="0",
            cursor="pointer" if on_step_click is not None else "default",
            _hover={"opacity": "0.85"} if on_step_click is not None else {},
        )
        if on_step_click is not None:
            circulo = rx.box(
                circulo,
                on_click=on_step_click(step_num),
                cursor="pointer",
            )
        if not show_labels:
            return circulo

        label_text = rx.text(
            _get_label(step_num, steps),
            font_size=Typography.SIZE_SM,
            color=rx.cond(
                es_completado_o_actual, Colors.TEXT_PRIMARY, Colors.TEXT_MUTED
            ),
            font_weight=rx.cond(
                es_actual, Typography.WEIGHT_SEMIBOLD, Typography.WEIGHT_MEDIUM
            ),
            cursor="pointer" if on_step_click is not None else "default",
            on_click=on_step_click(step_num) if on_step_click is not None else None,
        )
        return rx.hstack(
            circulo,
            label_text,
            align="center",
            spacing="2",
        )

    def _conector() -> rx.Component:
        return rx.box(
            flex="1",
            min_width="24px",
            max_width="80px",
            height="2px",
            background=Colors.BORDER,
            margin_x=Spacing.SM,
        )

    children: list[rx.Component] = []
    for idx, (num, _label) in enumerate(steps):
        children.append(_circulo(num))
        if idx < total - 1:
            children.append(_conector())

    return rx.flex(
        *children,
        width="100%",
        justify="center",
        align="center",
        padding_y=Spacing.MD,
        border_bottom=f"1px solid {Colors.BORDER}",
    )


def _get_label(step_num: int, steps: Sequence[tuple[int, str]]) -> str:
    """Busca el label del paso en la secuencia de steps."""
    for num, label in steps:
        if num == step_num:
            return label
    return ""
