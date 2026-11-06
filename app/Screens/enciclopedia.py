
import threading
import requests

from kivy.uix.screenmanager import Screen
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window

Builder.load_file("kv/enciclopedia.kv")

API_URL = "http://85.242.41.127:8000"


class enciclopedia(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._carregamento_em_curso = False
        self._plantas_carregadas = False
        self._swipe_start = None
        self._window_bound = False

    def on_enter(self, *args):
        self.opacity = 0
        Animation(opacity=1, duration=0.18).start(self)

        self._ativar_gestos()

        if not self._plantas_carregadas:
            self.carregar_plantas()

    def on_leave(self, *args):
        self._desativar_gestos()

    def _ativar_gestos(self):
        if not self._window_bound:
            Window.bind(on_touch_down=self._window_touch_down)
            Window.bind(on_touch_up=self._window_touch_up)
            self._window_bound = True

    def _desativar_gestos(self):
        if self._window_bound:
            Window.unbind(on_touch_down=self._window_touch_down)
            Window.unbind(on_touch_up=self._window_touch_up)
            self._window_bound = False

        self._swipe_start = None

    def _window_touch_down(self, window, touch):
        if self.manager and self.manager.current == "enciclopedia":
            self._swipe_start = touch.pos

    def _window_touch_up(self, window, touch):
        if (
            not self._swipe_start
            or not self.manager
            or self.manager.current != "enciclopedia"
        ):
            self._swipe_start = None
            return

        inicio_x, inicio_y = self._swipe_start
        dx = touch.x - inicio_x
        dy = touch.y - inicio_y
        self._swipe_start = None

        if dx > dp(75) and abs(dx) > abs(dy) * 1.3:
            self.voltar_home()

    def carregar_plantas(self):
        if self._carregamento_em_curso:
            return

        self._carregamento_em_curso = True
        self.ids.estado.text = "A carregar espécies..."

        threading.Thread(
            target=self._pedido_plantas,
            daemon=True
        ).start()

    def _pedido_plantas(self):
        try:
            resposta = requests.get(
                f"{API_URL}/plants",
                timeout=8
            )
            resposta.raise_for_status()
            resultado = resposta.json()

            if resultado.get("success"):
                plantas = resultado.get("plants", [])
                mensagem = (
                    "" if plantas
                    else "Ainda não existem espécies na enciclopédia."
                )
            else:
                plantas = []
                mensagem = resultado.get(
                    "message",
                    "Não foi possível carregar a enciclopédia."
                )

        except Exception as erro:
            print("Erro ao carregar enciclopédia:", erro)
            plantas = []
            mensagem = "Não foi possível ligar à API."

        Clock.schedule_once(
            lambda dt: self._mostrar_plantas(plantas, mensagem)
        )

    def _mostrar_plantas(self, plantas, mensagem):
        self._carregamento_em_curso = False

        if not self.manager:
            return

        grid = self.ids.plants_grid
        grid.clear_widgets()

        self.ids.estado.text = mensagem
        self.ids.estado.opacity = 1 if mensagem else 0

        for planta in plantas:
            nome = planta.get("name", "Planta")
            cientifico = planta.get("scientific_name") or ""

            botao = Button(
                text=f"{nome}\n{cientifico}" if cientifico else nome,
                size_hint_y=None,
                height=dp(76),
                background_normal="",
                background_down="",
                background_color=(0.93, 0.96, 0.93, 1),
                color=(0.25, 0.45, 0.27, 1),
                font_size="14sp"
            )

            botao.bind(
                on_release=lambda btn, p=planta:
                self.mostrar_detalhes(p)
            )

            grid.add_widget(botao)

        self._plantas_carregadas = bool(plantas)

    def mostrar_detalhes(self, planta):
        nome = planta.get("name", "Planta")
        cientifico = planta.get("scientific_name") or ""
        linhas = []

        if cientifico:
            linhas.append(cientifico)

        campos = [
            ("min_soil_humidity", "max_soil_humidity",
             "Humidade do solo", "%"),
            ("min_air_temperature", "max_air_temperature",
             "Temperatura do ar", "°C"),
            ("min_air_humidity", "max_air_humidity",
             "Humidade do ar", "%")
        ]

        for minimo, maximo, titulo, unidade in campos:
            if planta.get(minimo) is not None or planta.get(maximo) is not None:
                linhas.append(
                    f"{titulo}: {planta.get(minimo, '—')}–"
                    f"{planta.get(maximo, '—')} {unidade}"
                )

        for campo, titulo in [
            ("drought_tolerance", "Tolerância à seca"),
            ("soil_type_preference", "Solo"),
            ("care_notes", "Cuidados")
        ]:
            if planta.get(campo):
                linhas.append(f"{titulo}: {planta[campo]}")

        conteudo = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12)
        )

        texto = Label(
            text="\n\n".join(linhas)
            if linhas else "Não existem mais informações disponíveis.",
            color=(0.2, 0.25, 0.2, 1),
            halign="left",
            valign="top"
        )
        texto.bind(
            size=lambda instancia, valor:
            setattr(instancia, "text_size", valor)
        )
        conteudo.add_widget(texto)

        fechar = Button(
            text="Fechar",
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_color=(0.49, 0.77, 0.50, 1),
            color=(1, 1, 1, 1)
        )
        conteudo.add_widget(fechar)

        popup = Popup(
            title=nome,
            content=conteudo,
            size_hint=(0.9, 0.75),
            background="",
            background_color=(1, 1, 1, 1),
            title_color=(0.2, 0.35, 0.2, 1),
            separator_color=(0.49, 0.77, 0.5, 1)
        )

        fechar.bind(on_release=popup.dismiss)
        popup.open()

    def voltar_home(self):
        if self.manager and self.manager.has_screen("home"):
            self.manager.current = "home"
