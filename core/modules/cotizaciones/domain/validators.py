"""Cotizacion-specific validators kept near the feature surface."""

import core.presentation.pages.backoffice.cotizador.cotizador_validators as legacy_validators
from core.presentation.pages.backoffice.cotizador.cotizador_validators import *  # type: ignore[F401,F403]

validators___all__ = list(
    getattr(
        legacy_validators,
        "__all__",
        [name for name in dir(legacy_validators) if not name.startswith("_")],
    )
)

__all__ = validators___all__
