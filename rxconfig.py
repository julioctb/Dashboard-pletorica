import os

# Evita fallback implícito a Uvicorn en Reflex 0.8.x y elimina warning de runtime.
os.environ.setdefault("REFLEX_USE_GRANIAN", "true")

import reflex as rx

config = rx.Config(
    app_name="app",
    built_with_reflex=False,  # Compatibilidad en versiones anteriores.
    show_built_with_reflex=False,  # Flag actual para ocultar badge en frontend.
    # React StrictMode duplica los efectos de mount en dev (comportamiento
    # intencional de React 18 para detectar efectos no idempotentes). En este
    # proyecto eso causaba que cada `on_mount` de página disparara dos veces,
    # produciendo un doble ciclo de skeleton (visible en /portal/plazas y
    # /portal/contratos). En producción StrictMode no duplica efectos, así
    # que desactivarlo aquí solo afecta `reflex run` y elimina el doble mount
    # sin cambios en prod.
    react_strict_mode=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    # Google Fonts:
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;500;600;700&display=swap",
    ],

)
