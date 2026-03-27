"""Bootstrap helpers for composing the Reflex application."""

__all__ = ["create_app"]


def __getattr__(name: str):
    """Expose ``create_app`` lazily to avoid import cycles."""
    if name == "create_app":
        from app.bootstrap.app_factory import create_app

        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
