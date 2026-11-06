# =============================================================
# ANIMAÇÕES DA APLICAÇÃO GREENGADGET
# =============================================================

from kivy.animation import Animation
from kivy.clock import Clock


# =============================================================
# ATRASO
# =============================================================

def delayed(func, delay=0):

    Clock.schedule_once(
        lambda dt: func(),
        delay
    )


# =============================================================
# FADE-IN
# =============================================================

def fade_in(widget, duration=1):

    Animation.cancel_all(
        widget,
        "opacity"
    )

    Animation(
        opacity=1,
        duration=duration,
        t="out_quad"
    ).start(widget)


# =============================================================
# FADE-OUT
# =============================================================

def fade_out(widget, duration=1):

    Animation.cancel_all(
        widget,
        "opacity"
    )

    Animation(
        opacity=0,
        duration=duration,
        t="in_quad"
    ).start(widget)


# =============================================================
# SLIDE-UP
# =============================================================

def slide_up(widget, offset=.08, duration=.8):

    # Guardar posição original
    final_x = widget.x
    final_y = widget.y

    # Converter para posicionamento absoluto
    widget.pos_hint = {}

    # Começar ligeiramente abaixo
    widget.x = final_x
    widget.y = final_y - (
        widget.parent.height * offset
    )

    # Animar para a posição original
    Animation(
        x=final_x,
        y=final_y,
        duration=duration,
        t="out_quad"
    ).start(widget)


# =============================================================
# SLIDE DA ESQUERDA PARA A DIREITA
# =============================================================

def slide_right(widget, offset=.15, duration=.8):

    # Guardar posição original
    final_x = widget.x
    final_y = widget.y

    # Converter para posicionamento absoluto
    # Isto evita conflitos com x / center_x / pos_hint
    widget.pos_hint = {}

    # Começar à esquerda
    widget.x = final_x - (
        widget.parent.width * offset
    )

    widget.y = final_y

    # Animar para a posição original
    Animation(
        x=final_x,
        y=final_y,
        duration=duration,
        t="out_quad"
    ).start(widget)


# =============================================================
# SLIDE-DOWN
# =============================================================

def slide_down(widget, offset=.10, duration=.8):

    # Guardar posição original
    final_x = widget.x
    final_y = widget.y

    # Converter para posicionamento absoluto
    widget.pos_hint = {}

    # Começar acima
    widget.x = final_x

    widget.y = final_y + (
        widget.parent.height * offset
    )

    # Descer para a posição original
    Animation(
        x=final_x,
        y=final_y,
        duration=duration,
        t="out_quad"
    ).start(widget)


# =============================================================
# DROPDOWN - ABRIR
# =============================================================

def dropdown_open(
    widget,
    target_height=180,
    duration=1
):

    Animation.cancel_all(
        widget,
        "height",
        "opacity"
    )

    widget.height = 0
    widget.opacity = 1

    Animation(
        height=target_height,
        duration=duration,
        t="out_cubic"
    ).start(widget)


# =============================================================
# DROPDOWN - FECHAR
# =============================================================

def dropdown_close(
    widget,
    duration=1
):

    Animation.cancel_all(
        widget,
        "height",
        "opacity"
    )

    Animation(
        height=0,
        opacity=0,
        duration=duration,
        t="in_cubic"
    ).start(widget)


# =============================================================
# FADE-IN DA LISTA DE PLANTAS
# =============================================================

def fade_in_lista(
    widgets,
    duration=.30,
    intervalo=.08
):

    for indice, widget in enumerate(widgets):

        widget.opacity = 0

        Clock.schedule_once(

            lambda dt, w=widget:
            fade_in(
                w,
                duration
            ),

            indice * intervalo
        )