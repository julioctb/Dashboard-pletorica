"""Core module - Cross-cutting concerns (config, calculations, exceptions, enums)."""

__all__ = ["app"]


def __getattr__(name: str):
    """Expose ``app`` lazily for Reflex app loader compatibility."""
    if name == "app":
        from app.app import app as reflex_app

        return reflex_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
