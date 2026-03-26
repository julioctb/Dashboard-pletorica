"""Top-level Reflex app composed through the bootstrap layer."""

from core.bootstrap import create_app

app = create_app()

__all__ = ["app"]
