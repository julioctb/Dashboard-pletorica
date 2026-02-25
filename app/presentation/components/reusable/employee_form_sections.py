"""Secciones reutilizables para formularios de empleado."""

from typing import Any

import reflex as rx

from app.presentation.theme import Colors, Typography


def employee_curp_field(
    *,
    value: Any,
    on_change,
    on_blur=None,
    error: Any = None,
    disabled: Any = False,
    placeholder: str = "18 caracteres",
    max_length: int = 18,
    validation_indicator: rx.Component | None = None,
    local_error_condition: Any | None = None,
) -> rx.Component:
    """Campo CURP reutilizable con soporte para indicador externo de validación."""
    error_component = rx.cond(
        (error != "") if local_error_condition is None else local_error_condition,
        rx.text(
            error,
            font_size=Typography.SIZE_XS,
            color=Colors.ERROR,
        ),
        rx.fragment(),
    ) if error is not None else rx.fragment()

    return rx.vstack(
        rx.text(
            "CURP *",
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
        ),
        rx.input(
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            placeholder=placeholder,
            max_length=max_length,
            width="100%",
            disabled=disabled,
        ),
        validation_indicator if validation_indicator is not None else rx.fragment(),
        error_component,
        width="100%",
        spacing="1",
    )


def employee_email_field(
    *,
    value: Any,
    on_change,
    on_blur=None,
    error: Any = None,
    placeholder: str = "correo@ejemplo.com",
    label: str = "Email",
) -> rx.Component:
    """Campo email reutilizable."""
    return _field_stack(
        label=label,
        value=value,
        on_change=on_change,
        on_blur=on_blur,
        error=error,
        placeholder=placeholder,
    )


def employee_phone_email_row(
    *,
    telefono_value: Any,
    telefono_on_change,
    telefono_on_blur=None,
    telefono_error: Any = None,
    email_value: Any = None,
    email_on_change=None,
    email_on_blur=None,
    email_error: Any = None,
    telefono_required: bool = True,
    telefono_placeholder: str = "10 digitos",
    email_placeholder: str = "correo@ejemplo.com",
) -> rx.Component:
    """Fila reutilizable de teléfono + email."""
    telefono_label = "Telefono *" if telefono_required else "Telefono"
    telefono_field = rx.vstack(
        rx.text(
            telefono_label,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
        ),
        rx.input(
            value=telefono_value,
            on_change=telefono_on_change,
            on_blur=telefono_on_blur,
            placeholder=telefono_placeholder,
            max_length=15,
            width="100%",
        ),
        rx.cond(
            telefono_error != "",
            rx.text(
                telefono_error,
                font_size=Typography.SIZE_XS,
                color=Colors.ERROR,
            ),
            rx.fragment(),
        ) if telefono_error is not None else rx.fragment(),
        width="100%",
        spacing="1",
    )

    return rx.hstack(
        telefono_field,
        employee_email_field(
            value=email_value,
            on_change=email_on_change,
            on_blur=email_on_blur,
            error=email_error,
            placeholder=email_placeholder,
        ),
        spacing="3",
        width="100%",
    )


def employee_rfc_nss_row(
    *,
    rfc_value: Any,
    rfc_on_change,
    rfc_on_blur=None,
    rfc_error: Any = None,
    nss_value: Any = None,
    nss_on_change=None,
    nss_on_blur=None,
    nss_error: Any = None,
    rfc_required: bool = False,
    nss_required: bool = False,
    rfc_placeholder: str = "13 caracteres",
    nss_placeholder: str = "11 digitos",
) -> rx.Component:
    """Fila reutilizable RFC + NSS."""
    return rx.hstack(
        _field_stack(
            label="RFC *" if rfc_required else "RFC",
            value=rfc_value,
            on_change=rfc_on_change,
            on_blur=rfc_on_blur,
            error=rfc_error,
            placeholder=rfc_placeholder,
        ),
        rx.vstack(
            rx.text(
                "NSS *" if nss_required else "NSS",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.input(
                value=nss_value,
                on_change=nss_on_change,
                on_blur=nss_on_blur,
                placeholder=nss_placeholder,
                max_length=11,
                width="100%",
            ),
            rx.cond(
                nss_error != "",
                rx.text(
                    nss_error,
                    font_size=Typography.SIZE_XS,
                    color=Colors.ERROR,
                ),
                rx.fragment(),
            ) if nss_error is not None else rx.fragment(),
            width="100%",
            spacing="1",
        ),
        spacing="3",
        width="100%",
    )


def employee_birth_gender_row(
    *,
    fecha_value: Any,
    fecha_on_change,
    fecha_on_blur=None,
    fecha_error: Any = None,
    genero_value: Any = None,
    genero_on_change=None,
    genero_error: Any = None,
    opciones_genero=None,
    fecha_required: bool = False,
    genero_required: bool = False,
    genero_label: str = "Genero",
) -> rx.Component:
    """Fila reutilizable Fecha de nacimiento + Genero."""
    if opciones_genero is None:
        opciones_genero = []

    return rx.hstack(
        rx.vstack(
            rx.text(
                "Fecha de Nacimiento *" if fecha_required else "Fecha de Nacimiento",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.input(
                type="date",
                value=fecha_value,
                on_change=fecha_on_change,
                on_blur=fecha_on_blur,
                width="100%",
            ),
            rx.cond(
                fecha_error != "",
                rx.text(
                    fecha_error,
                    font_size=Typography.SIZE_XS,
                    color=Colors.ERROR,
                ),
                rx.fragment(),
            ) if fecha_error is not None else rx.fragment(),
            width="100%",
            spacing="1",
        ),
        rx.vstack(
            rx.text(
                f"{genero_label} *" if genero_required else genero_label,
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.select.root(
                rx.select.trigger(
                    placeholder="Seleccionar...",
                    width="100%",
                ),
                rx.select.content(
                    rx.foreach(
                        opciones_genero,
                        lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                    ),
                ),
                value=genero_value,
                on_change=genero_on_change,
            ),
            rx.cond(
                genero_error != "",
                rx.text(
                    genero_error,
                    font_size=Typography.SIZE_XS,
                    color=Colors.ERROR,
                ),
                rx.fragment(),
            ) if genero_error is not None else rx.fragment(),
            width="100%",
            spacing="1",
        ),
        spacing="3",
        width="100%",
    )


def employee_address_field(
    *,
    value: Any,
    on_change,
    placeholder: str = "Direccion completa",
    label: str = "Direccion",
    rows: str = "2",
) -> rx.Component:
    """Campo de dirección reutilizable."""
    return rx.vstack(
        rx.text(
            label,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
        ),
        rx.text_area(
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            width="100%",
            rows=rows,
        ),
        width="100%",
        spacing="1",
    )


def employee_notes_field(
    *,
    value: Any,
    on_change,
    placeholder: str = "Observaciones adicionales",
    label: str = "Notas",
    rows: str = "2",
) -> rx.Component:
    """Campo de notas reutilizable."""
    return rx.vstack(
        rx.text(
            label,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
        ),
        rx.text_area(
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            width="100%",
            rows=rows,
        ),
        width="100%",
        spacing="1",
    )


def employee_emergency_contact_section(
    *,
    mode: str = "simple",
    # simple
    simple_value: Any = None,
    simple_on_change=None,
    simple_placeholder: str = "Nombre y teléfono",
    # detailed
    nombre_value: Any = None,
    nombre_on_change=None,
    nombre_on_blur=None,
    nombre_error: Any = None,
    telefono_value: Any = None,
    telefono_on_change=None,
    telefono_on_blur=None,
    telefono_error: Any = None,
    parentesco_value: Any = None,
    parentesco_on_change=None,
    parentesco_error: Any = None,
    opciones_parentesco=None,
    label_weight: str = "bold",
    bordered: bool = False,
) -> rx.Component:
    """Sección reusable de contacto de emergencia (simple o detallada)."""
    if mode == "simple":
        return rx.vstack(
            rx.text(
                "Contacto de Emergencia",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM if label_weight == "medium" else Typography.WEIGHT_BOLD,
            ),
            rx.input(
                value=simple_value,
                on_change=simple_on_change,
                placeholder=simple_placeholder,
                width="100%",
            ),
            width="100%",
            spacing="1",
        )

    if opciones_parentesco is None:
        opciones_parentesco = []
    title = rx.text(
        "Contacto de Emergencia",
        font_size=Typography.SIZE_SM,
        font_weight=Typography.WEIGHT_MEDIUM if label_weight == "medium" else Typography.WEIGHT_BOLD,
    )
    fields = rx.hstack(
        _field_stack(
            label="Nombre",
            value=nombre_value,
            on_change=nombre_on_change,
            on_blur=nombre_on_blur,
            error=nombre_error,
            placeholder="Nombre completo",
        ),
        rx.vstack(
            rx.text(
                "Telefono",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.input(
                value=telefono_value,
                on_change=telefono_on_change,
                on_blur=telefono_on_blur,
                placeholder="10 digitos",
                max_length=15,
                width="100%",
            ),
            rx.cond(
                telefono_error != "",
                rx.text(telefono_error, font_size=Typography.SIZE_XS, color=Colors.ERROR),
                rx.fragment(),
            ) if telefono_error is not None else rx.fragment(),
            width="100%",
            spacing="1",
        ),
        rx.vstack(
            rx.text(
                "Parentesco",
                font_size=Typography.SIZE_SM,
                font_weight=Typography.WEIGHT_MEDIUM,
            ),
            rx.select.root(
                rx.select.trigger(placeholder="Seleccionar...", width="100%"),
                rx.select.content(
                    rx.foreach(
                        opciones_parentesco,
                        lambda opt: rx.select.item(opt["label"], value=opt["value"]),
                    ),
                ),
                value=parentesco_value,
                on_change=parentesco_on_change,
            ),
            rx.cond(
                parentesco_error != "",
                rx.text(parentesco_error, font_size=Typography.SIZE_XS, color=Colors.ERROR),
                rx.fragment(),
            ) if parentesco_error is not None else rx.fragment(),
            width="100%",
            spacing="1",
        ),
        spacing="3",
        width="100%",
    )
    content = rx.vstack(
        title,
        fields,
        width="100%",
        spacing="2",
    )
    if not bordered:
        return content
    return rx.vstack(
        title,
        fields,
        width="100%",
        spacing="2",
        padding="12px",
        border=f"1px solid {Colors.BORDER}",
        border_radius="8px",
    )


def _field_stack(
    *,
    label: str,
    value: Any,
    on_change,
    placeholder: str,
    error: Any = None,
    on_blur=None,
    width: str = "100%",
) -> rx.Component:
    return rx.vstack(
        rx.text(
            label,
            font_size=Typography.SIZE_SM,
            font_weight=Typography.WEIGHT_MEDIUM,
        ),
        rx.input(
            value=value,
            on_change=on_change,
            on_blur=on_blur,
            placeholder=placeholder,
            width="100%",
        ),
        rx.cond(
            (error is not None) & (error != ""),
            rx.text(
                error,
                font_size=Typography.SIZE_XS,
                color=Colors.ERROR,
            ),
            rx.fragment(),
        ) if error is not None else rx.fragment(),
        width=width,
        spacing="1",
    )


def employee_name_fields_section(
    *,
    nombre_value: Any,
    nombre_on_change,
    nombre_on_blur=None,
    nombre_error: Any = None,
    apellido_paterno_value: Any = None,
    apellido_paterno_on_change=None,
    apellido_paterno_on_blur=None,
    apellido_paterno_error: Any = None,
    apellido_materno_value: Any = None,
    apellido_materno_on_change=None,
    apellido_materno_on_blur=None,
    apellido_materno_error: Any = None,
    materno_requerido: bool = False,
    materno_placeholder: str = "Apellido materno",
    materno_mostrar_error: bool = False,
    materno_inline: bool = True,
) -> rx.Component:
    """Sección reutilizable para nombre y apellidos.

    `materno_inline=True` produce 3 columnas.
    `materno_inline=False` produce fila (nombre+paterno) + bloque separado para materno.
    """
    materno_label = "Ap. Materno *" if materno_requerido else "Ap. Materno"

    campo_nombre = _field_stack(
        label="Nombre *",
        value=nombre_value,
        on_change=nombre_on_change,
        on_blur=nombre_on_blur,
        error=nombre_error,
        placeholder="Nombre(s)",
    )
    campo_paterno = _field_stack(
        label="Ap. Paterno *",
        value=apellido_paterno_value,
        on_change=apellido_paterno_on_change,
        on_blur=apellido_paterno_on_blur,
        error=apellido_paterno_error,
        placeholder="Apellido paterno",
    )
    campo_materno = _field_stack(
        label=materno_label,
        value=apellido_materno_value,
        on_change=apellido_materno_on_change,
        on_blur=apellido_materno_on_blur,
        error=apellido_materno_error if materno_mostrar_error else None,
        placeholder=materno_placeholder,
        width="50%" if not materno_inline else "100%",
    )

    if materno_inline:
        return rx.hstack(
            campo_nombre,
            campo_paterno,
            campo_materno,
            spacing="3",
            width="100%",
        )

    return rx.vstack(
        rx.hstack(
            campo_nombre,
            campo_paterno,
            spacing="3",
            width="100%",
        ),
        campo_materno,
        spacing="3",
        width="100%",
    )
