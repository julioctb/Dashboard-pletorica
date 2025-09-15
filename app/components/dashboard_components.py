import reflex as rx
from typing import Dict, List

#componente para mostrar una tarjeta estadística 
def stat_card(title:str, value:str, subtitle: str ="", color: str ="blue") -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(
                    "users" if "empleado" in title.lower() else
                    "building" if "empresa" in title.lower() else
                    "dollar-sign", 
                    size=24,
                    color= f"var(--{color}9)"
                ),
                rx.spacer(),
                align="center",
                width="100%"
            ),
            rx.text(value,size='6',weight='bold',color=f"var({color}-11)"),
            rx.text(title,size='2',weight='medium',color=f"var(--gray-11)"),
            rx.cond(
                subtitle  != "",
                rx.text(subtitle, size = "1", color="var(--gray-9)"),
                rx.text("")
            ),
            spacing="2",
            align="start"
        ),
        width = "100%",
        padding="4"

    )