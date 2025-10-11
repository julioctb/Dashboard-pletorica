import reflex as rx

config = rx.Config(
    app_name="app",
    built_with_reflex=False,  # Oculta el badge "Built with Reflex"
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)