
import requests

from kivy.animation import Animation
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import ButtonBehavior
from kivy.uix.label import Label
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window

Builder.load_file("kv/home.kv")

API_URL = "http://85.242.41.127:8000"


class PlantCard(ButtonBehavior, BoxLayout):

    def __init__(self, nome, tem_rega, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(5),
            padding=(dp(8), dp(12)),
            size_hint=(1, None),
            height=dp(122),
            **kwargs
        )

        self.background_color = (0.93, 0.97, 0.93, 1)

        with self.canvas.before:
            Color(*self.background_color)
            self.fundo = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(8)]
            )

        self.bind(pos=self._atualizar_fundo, size=self._atualizar_fundo)

        self.nome_label = Label(
            text=nome,
            color=(0.20, 0.43, 0.24, 1),
            font_name="extras/Montserrat-Bold.ttf",
            font_size="13sp",
            halign="center",
            valign="middle",
            size_hint=(1, 0.58),
            shorten=True,
            shorten_from="right"
        )
        self.nome_label.bind(
            size=self._ajustar_texto
        )
        self.add_widget(self.nome_label)

        if tem_rega:
            texto_estado = "Sistema de rega associado"
            cor_estado = (0.20, 0.50, 0.25, 1)
        else:
            texto_estado = "Sem módulo de rega associado"
            cor_estado = (0.85, 0.15, 0.15, 1)

        self.estado_label = Label(
            text=texto_estado,
            color=cor_estado,
            font_name="extras/Montserrat-VariableFont_wght.ttf",
            font_size="10sp",
            halign="center",
            valign="middle",
            size_hint=(1, 0.42)
        )
        self.estado_label.bind(size=self._ajustar_texto)
        self.add_widget(self.estado_label)

    def _atualizar_fundo(self, *args):
        self.fundo.pos = self.pos
        self.fundo.size = self.size

    @staticmethod
    def _ajustar_texto(etiqueta, tamanho):
        etiqueta.text_size = (
            max(1, tamanho[0] - dp(4)),
            max(1, tamanho[1])
        )


class home(Screen):
    user_id = None

    def definir_utilizador(self, user_id):
        self.user_id = user_id

    def on_enter(self, *args):
        self._swipe_start = None

        # Fade-in da janela Home
        self.opacity = 0
        Animation.cancel_all(self, "opacity")
        Animation(opacity=1, duration=0.25).start(self)

        # Ativar os gestos de navegação
        Window.bind(on_touch_down=self._home_touch_down)
        Window.bind(on_touch_up=self._home_touch_up)

        self.carregar_dispositivos()

    def carregar_dispositivos(self):
        grid = self.ids.devices_grid
        grid.clear_widgets()

        if self.user_id is None:
            self._mostrar_estado(
                "Inicia sessão para consultar os teus dispositivos."
            )
            return

        self._mostrar_estado("A carregar dispositivos...")

        try:
            resposta = requests.get(
                f"{API_URL}/devices/{self.user_id}",
                timeout=6
            )
            resposta.raise_for_status()
            resultado = resposta.json()

            if not resultado.get("success"):
                self._mostrar_estado(
                    resultado.get(
                        "message",
                        "Não foi possível carregar os dispositivos."
                    )
                )
                return

            dispositivos = resultado.get("devices", [])

            resposta_rega = requests.get(
                f"{API_URL}/watering-devices/{self.user_id}",
                timeout=6
            )
            resposta_rega.raise_for_status()
            resultado_rega = resposta_rega.json()

            modulos_rega = (
                resultado_rega.get("watering_devices", [])
                if resultado_rega.get("success")
                else []
            )

            if not dispositivos:
                self._mostrar_estado(
                    "Ainda não tens dispositivos de dados associados.\n"
                    "Carrega em + para adicionar um."
                )
                return

            self._mostrar_estado("")

            for dispositivo in dispositivos:
                device_id = dispositivo.get("id")
                nome = dispositivo.get("name") or "Dispositivo de dados"

                tem_rega = any(
                    str(modulo.get("device_id")) == str(device_id)
                    for modulo in modulos_rega
                )

                cartao = PlantCard(
                    nome=nome,
                    tem_rega=tem_rega
                )

                cartao.bind(
                    on_release=lambda instancia, d=dispositivo:
                    self.abrir_dispositivo(d)
                )

                grid.add_widget(cartao)

        except requests.RequestException as erro:
            print("Erro de comunicação com a API:", erro)
            self._mostrar_estado(
                "Não foi possível contactar o servidor."
            )

        except Exception as erro:
            print("Erro ao carregar dispositivos:", erro)
            self._mostrar_estado(
                "Ocorreu um erro ao carregar os dispositivos."
            )

    def _mostrar_estado(self, mensagem):
        self.ids.estado_vazio.text = mensagem
        self.ids.estado_vazio.opacity = 1 if mensagem else 0

    def abrir_dispositivo(self, dispositivo):
        tela = self.manager.get_screen("device")
        tela.user_id = self.user_id
        tela.carregar_dispositivo(dispositivo)
        self.manager.current = "device"

    def adicionar_dispositivo(self):
        tela = self.manager.get_screen("add_device")
        tela.definir_utilizador(self.user_id)
        self.manager.current = "add_device"

    def abrir_enciclopedia(self):
        if self.manager.has_screen("enciclopedia"):
            self.manager.current = "enciclopedia"
        else:
            print("A janela da enciclopédia não está registada.")

    def logout(self):
        self.user_id = None
        if self.manager.has_screen("login"):
            self.manager.current = "login"

    def on_leave(self, *args):
        Window.unbind(on_touch_down=self._home_touch_down)
        Window.unbind(on_touch_up=self._home_touch_up)
        self._swipe_start = None

    def _home_touch_down(self, window, touch):
        if self.manager and self.manager.current == "home":
            self._swipe_start = touch.pos

    def _home_touch_up(self, window, touch):
        if (
                self._swipe_start is None
                or not self.manager
                or self.manager.current != "home"
        ):
            self._swipe_start = None
            return

        inicio_x, inicio_y = self._swipe_start
        dx = touch.x - inicio_x
        dy = touch.y - inicio_y
        self._swipe_start = None

        # Deslizar da direita para a esquerda abre a enciclopédia.
        if dx < -dp(75) and abs(dx) > abs(dy) * 1.3:
            if self.manager.has_screen("enciclopedia"):
                self.manager.current = "enciclopedia"

