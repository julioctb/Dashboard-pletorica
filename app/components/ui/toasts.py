import reflex as rx

#TODO: hacer una alerta flotante

def mensaje_flotante(mensaje: str, tipo_mensaje: str) -> rx.Component:
    return rx.cond(
        tipo_mensaje == 'info',
        rx.toast.info(mensaje)
    )