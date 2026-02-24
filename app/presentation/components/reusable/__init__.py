"""Componentes reutilizables de alto nivel."""

from .document_row_primitives import (
    documento_observacion,
    documento_requerido_badge,
    documento_subido_icon,
)
from .employee_form_modal import employee_form_modal
from .employee_list import employee_filters_bar, employee_table
from .employee_form_sections import (
    employee_address_field,
    employee_birth_gender_row,
    employee_curp_field,
    employee_emergency_contact_section,
    employee_email_field,
    employee_name_fields_section,
    employee_notes_field,
    employee_phone_email_row,
    employee_rfc_nss_row,
)
from .onboarding_list import onboarding_filters, onboarding_table

__all__ = [
    "documento_observacion",
    "documento_requerido_badge",
    "documento_subido_icon",
    "employee_form_modal",
    "employee_filters_bar",
    "employee_table",
    "employee_address_field",
    "employee_birth_gender_row",
    "employee_curp_field",
    "employee_emergency_contact_section",
    "employee_email_field",
    "employee_name_fields_section",
    "employee_notes_field",
    "employee_phone_email_row",
    "employee_rfc_nss_row",
    "onboarding_filters",
    "onboarding_table",
]
