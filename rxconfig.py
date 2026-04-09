import os

# Evita fallback implícito a Uvicorn en Reflex 0.8.x y elimina warning de runtime.
os.environ.setdefault("REFLEX_USE_GRANIAN", "true")

import reflex as rx

config = rx.Config(
    app_name="app",
    built_with_reflex=False,  # Compatibilidad en versiones anteriores.
    show_built_with_reflex=False,  # Flag actual para ocultar badge en frontend.
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
    # Google Fonts:
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Source+Sans+Pro:wght@400;500;600;700&display=swap",
    ],

)
