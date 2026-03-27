"""Top-level Reflex app composed through the bootstrap layer."""

from app.bootstrap import create_app

app = create_app()

__all__ = ["app"]
