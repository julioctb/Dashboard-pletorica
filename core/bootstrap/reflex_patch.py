"""Compatibility patches applied before building the Reflex core."""

from reflex.compiler import templates as rx_templates

_PATCHED = False


def patch_reflex_context_defaults() -> None:
    """Avoid null-context crashes in Reflex 0.8.x development mode."""
    global _PATCHED
    if _PATCHED:
        return

    original_context_template = rx_templates.context_template

    def _context_template_with_safe_defaults(
        *,
        is_dev_mode,
        default_color_mode,
        initial_state=None,
        state_name=None,
        client_storage=None,
    ):
        generated = original_context_template(
            is_dev_mode=is_dev_mode,
            default_color_mode=default_color_mode,
            initial_state=initial_state,
            state_name=state_name,
            client_storage=client_storage,
        )
        generated = generated.replace(
            "export const ColorModeContext = createContext(null);",
            (
                "export const ColorModeContext = createContext({"
                "rawColorMode: defaultColorMode, "
                'resolvedColorMode: defaultColorMode === "system" ? "light" : defaultColorMode, '
                "toggleColorMode: () => {}, "
                "setColorMode: () => {}"
                "});"
            ),
        )
        generated = generated.replace(
            "export const EventLoopContext = createContext(null);",
            "export const EventLoopContext = createContext([(..._args) => {}, []]);",
        )
        return generated

    rx_templates.context_template = _context_template_with_safe_defaults
    _PATCHED = True
