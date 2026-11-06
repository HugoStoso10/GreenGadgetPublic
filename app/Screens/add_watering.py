# =============================================================
# BIBLIOTECAS
# =============================================================

import requests

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.clock import Clock


# =============================================================
# ANIMAÇÕES
# =============================================================

from Animacoes import (
    delayed,
    fade_in,
    slide_down
)


# =============================================================
# CONFIGURAÇÃO
# =============================================================

Builder.load_file("kv/add_watering.kv")

API_URL = "http://85.242.41.127:8000"

# IP padrão do ESP32 quando cria o seu Access Point
ESP32_IP = "192.168.4.1"


# =============================================================
# ECRÃ ADICIONAR DISPOSITIVO DE REGA
# =============================================================

class add_watering(Screen):

    user_id = None
    codigo_dispositivo = None
    dispositivo_selecionado = None
    dispositivos_recolha = []

    def definir_dispositivo_recolha(self, dispositivo):
        """
        Pré-seleciona o dispositivo de dados associado
        à planta que está aberta.
        """
        self.dispositivo_recolha_preselecionado = dispositivo

        if dispositivo:
            self.dispositivo_selecionado = dispositivo

    # =========================================================
    # LIMPAR FORMULÁRIO
    # =========================================================

    def limpar_formulario(self):

        self.dispositivo_recolha_preselecionado = None
        self.codigo_dispositivo = None
        self.dispositivo_selecionado = None
        self.dispositivos_recolha = []

        # Limpar campos
        self.ids.TextFieldCodigo.text = ""
        self.ids.campo_ssid.text = ""
        self.ids.campo_password.text = ""

        # Limpar seleção
        self.ids.btn_dispositivo.text = "Selecionar dispositivo"

        # Limpar mensagem
        self.ids.erro_texto.text = ""

        # -----------------------------------------------------
        # Fase código
        # -----------------------------------------------------

        self.ids.TextFieldCodigo.disabled = False
        self.ids.btn.disabled = False

        # -----------------------------------------------------
        # Fase dispositivo
        # -----------------------------------------------------

        self.ids.btn_dispositivo.disabled = True
        self.ids.btn_dispositivo_continuar.disabled = True

        # -----------------------------------------------------
        # Fase Wi-Fi
        # -----------------------------------------------------

        self.ids.campo_ssid.disabled = True
        self.ids.campo_password.disabled = True
        self.ids.btn_wifi.disabled = True

        # -----------------------------------------------------
        # Visibilidade
        # -----------------------------------------------------

        self.ids.texto_explicativo.opacity = 1
        self.ids.TextFieldCodigo.opacity = 1
        self.ids.btn.opacity = 1

        self.ids.texto_dispositivo.opacity = 0
        self.ids.btn_dispositivo.opacity = 0
        self.ids.btn_dispositivo_continuar.opacity = 0

        self.ids.texto_wifi.opacity = 0
        self.ids.campo_ssid.opacity = 0
        self.ids.campo_password.opacity = 0
        self.ids.btn_wifi.opacity = 0


    # =========================================================
    # AO ENTRAR NA JANELA
    # =========================================================

    def on_enter(self):

        self.limpar_formulario()
        self.mostrar_fase_codigo()
        self.animar_entrada()


    # =========================================================
    # FASE 1 — CÓDIGO
    # =========================================================

    def mostrar_fase_codigo(self):

        # Mostrar código
        self.ids.texto_explicativo.opacity = 1
        self.ids.TextFieldCodigo.opacity = 1
        self.ids.TextFieldCodigo.disabled = False

        self.ids.btn.opacity = 1
        self.ids.btn.disabled = False

        # Esconder seleção
        self.ids.texto_dispositivo.opacity = 0
        self.ids.btn_dispositivo.opacity = 0
        self.ids.btn_dispositivo.disabled = True

        self.ids.btn_dispositivo_continuar.opacity = 0
        self.ids.btn_dispositivo_continuar.disabled = True

        # Esconder Wi-Fi
        self.ids.texto_wifi.opacity = 0

        self.ids.campo_ssid.opacity = 0
        self.ids.campo_ssid.disabled = True

        self.ids.campo_password.opacity = 0
        self.ids.campo_password.disabled = True

        self.ids.btn_wifi.opacity = 0
        self.ids.btn_wifi.disabled = True


    # =========================================================
    # ANIMAÇÕES DE ENTRADA
    # =========================================================

    def animar_entrada(self):

        self.ids.logo_add.opacity = 0
        self.ids.botao_voltar.opacity = 0

        self.ids.titulo_add.opacity = 0
        self.ids.texto_explicativo.opacity = 0
        self.ids.TextFieldCodigo.opacity = 0
        self.ids.btn.opacity = 0

        self.ids.texto_dispositivo.opacity = 0
        self.ids.btn_dispositivo.opacity = 0
        self.ids.btn_dispositivo_continuar.opacity = 0

        self.ids.texto_wifi.opacity = 0
        self.ids.campo_ssid.opacity = 0
        self.ids.campo_password.opacity = 0
        self.ids.btn_wifi.opacity = 0

        # -----------------------------------------------------
        # Logo
        # -----------------------------------------------------

        delayed(
            lambda: fade_in(
                self.ids.logo_add,
                duration=0.8
            ),
            0
        )

        # -----------------------------------------------------
        # Botão voltar
        # -----------------------------------------------------

        delayed(
            lambda: fade_in(
                self.ids.botao_voltar,
                duration=0.8
            ),
            0
        )

        # -----------------------------------------------------
        # Título
        # -----------------------------------------------------

        delayed(
            lambda: slide_down(
                self.ids.titulo_add,
                offset=.10,
                duration=.7
            ),
            0.10
        )

        delayed(
            lambda: fade_in(
                self.ids.titulo_add,
                duration=.7
            ),
            0.10
        )

        # -----------------------------------------------------
        # Texto
        # -----------------------------------------------------

        delayed(
            lambda: slide_down(
                self.ids.texto_explicativo,
                offset=.10,
                duration=.7
            ),
            0.25
        )

        delayed(
            lambda: fade_in(
                self.ids.texto_explicativo,
                duration=.7
            ),
            0.25
        )

        # -----------------------------------------------------
        # Campo código
        # -----------------------------------------------------

        delayed(
            lambda: slide_down(
                self.ids.TextFieldCodigo,
                offset=.10,
                duration=.7
            ),
            0.40
        )

        delayed(
            lambda: fade_in(
                self.ids.TextFieldCodigo,
                duration=.7
            ),
            0.40
        )

        # -----------------------------------------------------
        # Botão
        # -----------------------------------------------------

        delayed(
            lambda: fade_in(
                self.ids.btn,
                duration=.7
            ),
            0.55
        )


    # =========================================================
    # DEFINIR UTILIZADOR
    # =========================================================

    def definir_utilizador(self, user_id):

        self.user_id = user_id


    # =========================================================
    # FASE 1 — VALIDAR CÓDIGO
    # =========================================================

    def adicionar(self):

        codigo = self.ids.TextFieldCodigo.text.strip()

        # -----------------------------------------------------
        # Validar código
        # -----------------------------------------------------

        if not codigo:

            self.mostrar_erro(
                "Insira o código do dispositivo de rega."
            )

            return

        # -----------------------------------------------------
        # Validar utilizador
        # -----------------------------------------------------

        if self.user_id is None:

            self.mostrar_erro(
                "Utilizador não identificado."
            )

            return

        try:

            # -------------------------------------------------
            # Verificar módulo de rega na API
            # -------------------------------------------------

            resposta = requests.get(
                f"{API_URL}/watering-devices/code/{codigo}",
                timeout=5
            )

            if resposta.status_code != 200:

                self.mostrar_erro(
                    "Dispositivo de rega não encontrado."
                )

                return

            resultado = resposta.json()

            if not resultado.get("success", False):

                self.mostrar_erro(
                    resultado.get(
                        "message",
                        "Dispositivo de rega não encontrado."
                    )
                )

                return

            watering_device = resultado.get(
                "watering_device",
                {}
            )

            # -------------------------------------------------
            # Verificar se já está associado
            # -------------------------------------------------

            if watering_device.get("user_id") is not None:

                self.mostrar_erro(
                    "Este dispositivo de rega já está associado."
                )

                return

            # -------------------------------------------------
            # Guardar código
            # -------------------------------------------------

            self.codigo_dispositivo = codigo

            # -------------------------------------------------
            # Obter dispositivos de recolha
            # -------------------------------------------------

            resposta_dispositivos = requests.get(
                f"{API_URL}/devices/{self.user_id}",
                timeout=5
            )

            if resposta_dispositivos.status_code != 200:

                self.mostrar_erro(
                    "Não foi possível obter os dispositivos de recolha."
                )

                return

            resultado_dispositivos = (
                resposta_dispositivos.json()
            )

            if not resultado_dispositivos.get(
                "success",
                False
            ):

                self.mostrar_erro(
                    resultado_dispositivos.get(
                        "message",
                        "Não foi possível obter os dispositivos."
                    )
                )

                return

            dispositivos = resultado_dispositivos.get(
                "devices",
                []
            )

            # -------------------------------------------------
            # Verificar se existem dispositivos
            # -------------------------------------------------

            if not dispositivos:

                self.mostrar_erro(
                    "Não existem dispositivos de recolha disponíveis."
                )

                return

            # -------------------------------------------------
            # Guardar dispositivos
            # -------------------------------------------------

            self.dispositivos_recolha = dispositivos

            # -------------------------------------------------
            # Passar para fase de seleção
            # -------------------------------------------------

            self.mostrar_fase_dispositivo()

        except requests.exceptions.ConnectionError:

            self.mostrar_erro(
                "Não foi possível ligar ao servidor."
            )

        except requests.exceptions.Timeout:

            self.mostrar_erro(
                "O servidor demorou demasiado a responder."
            )

        except Exception as erro:

            print(
                "Erro ao verificar dispositivo de rega:",
                erro
            )

            self.mostrar_erro(
                "Erro inesperado."
            )


    # =========================================================
    # FASE 2 — SELECIONAR DISPOSITIVO DE RECOLHA
    # =========================================================

    def mostrar_fase_dispositivo(self):

        # -----------------------------------------------------
        # Esconder código
        # -----------------------------------------------------

        self.ids.texto_explicativo.opacity = 0

        self.ids.TextFieldCodigo.opacity = 0
        self.ids.TextFieldCodigo.disabled = True

        self.ids.btn.opacity = 0
        self.ids.btn.disabled = True

        # -----------------------------------------------------
        # Mostrar seleção
        # -----------------------------------------------------

        self.ids.texto_dispositivo.opacity = 1

        self.ids.btn_dispositivo.opacity = 1
        self.ids.btn_dispositivo.disabled = False

        self.ids.btn_dispositivo_continuar.opacity = 1
        self.ids.btn_dispositivo_continuar.disabled = True

        # -----------------------------------------------------
        # Esconder Wi-Fi
        # -----------------------------------------------------

        self.ids.texto_wifi.opacity = 0

        self.ids.campo_ssid.opacity = 0
        self.ids.campo_ssid.disabled = True

        self.ids.campo_password.opacity = 0
        self.ids.campo_password.disabled = True

        self.ids.btn_wifi.opacity = 0
        self.ids.btn_wifi.disabled = True

        self.ids.erro_texto.text = ""


    # =========================================================
    # ABRIR LISTA DE DISPOSITIVOS
    # =========================================================

    def abrir_dispositivos(self):

        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button

        dispositivos = getattr(
            self,
            "dispositivos_recolha",
            []
        )

        if not dispositivos:

            self.mostrar_erro(
                "Não existem dispositivos disponíveis."
            )

            return

        layout = BoxLayout(
            orientation="vertical",
            spacing=5,
            padding=10
        )

        popup = Popup(
            title="Selecionar dispositivo",
            content=layout,
            size_hint=(0.85, 0.65)
        )

        for dispositivo in dispositivos:

            nome = dispositivo.get(
                "name",
                "Sem nome"
            )

            codigo = dispositivo.get(
                "code",
                ""
            )

            texto = nome

            if codigo:

                texto += f"\n{codigo}"

            botao = Button(
                text=texto,
                size_hint_y=None,
                height=70
            )

            botao.bind(
                on_release=lambda btn, d=dispositivo:
                self.selecionar_dispositivo(
                    d,
                    popup
                )
            )

            layout.add_widget(botao)

        popup.open()


    # =========================================================
    # SELECIONAR DISPOSITIVO
    # =========================================================

    def selecionar_dispositivo(
        self,
        dispositivo,
        popup=None
    ):

        self.dispositivo_selecionado = dispositivo

        nome = dispositivo.get(
            "name",
            "Sem nome"
        )

        codigo = dispositivo.get(
            "code",
            ""
        )

        if codigo:

            self.ids.btn_dispositivo.text = (
                f"{nome} ({codigo})"
            )

        else:

            self.ids.btn_dispositivo.text = nome

        self.ids.btn_dispositivo_continuar.disabled = False

        self.ids.erro_texto.text = ""

        if popup:

            popup.dismiss()


    # =========================================================
    # FASE 3 — CONFIGURAÇÃO WI-FI
    # =========================================================

    def mostrar_configuracao_wifi(self):

        # -----------------------------------------------------
        # Verificar seleção
        # -----------------------------------------------------

        if self.dispositivo_selecionado is None:

            self.mostrar_erro(
                "Selecione primeiro um dispositivo de recolha."
            )

            return

        # -----------------------------------------------------
        # Esconder seleção
        # -----------------------------------------------------

        self.ids.texto_dispositivo.opacity = 0

        self.ids.btn_dispositivo.opacity = 0
        self.ids.btn_dispositivo.disabled = True

        self.ids.btn_dispositivo_continuar.opacity = 0
        self.ids.btn_dispositivo_continuar.disabled = True

        # -----------------------------------------------------
        # Mostrar Wi-Fi
        # -----------------------------------------------------

        self.ids.texto_wifi.opacity = 1

        self.ids.campo_ssid.opacity = 1
        self.ids.campo_ssid.disabled = False

        self.ids.campo_password.opacity = 1
        self.ids.campo_password.disabled = False

        self.ids.btn_wifi.opacity = 1
        self.ids.btn_wifi.disabled = False

        self.ids.erro_texto.text = ""


    # =========================================================
    # ENVIAR WI-FI PARA ESP32 DE REGA
    # =========================================================

    def associar_wifi(self):

        ssid = self.ids.campo_ssid.text.strip()
        password = self.ids.campo_password.text

        # -----------------------------------------------------
        # Validar SSID
        # -----------------------------------------------------

        if not ssid:

            self.mostrar_erro(
                "Insira o nome da rede Wi-Fi."
            )

            return

        # -----------------------------------------------------
        # Validar password
        # -----------------------------------------------------

        if not password:

            self.mostrar_erro(
                "Insira a password da rede Wi-Fi."
            )

            return

        # -----------------------------------------------------
        # Validar dispositivo selecionado
        # -----------------------------------------------------

        if self.dispositivo_selecionado is None:

            self.mostrar_erro(
                "Selecione um dispositivo de recolha."
            )

            return

        device_id = self.dispositivo_selecionado.get("id")

        if device_id is None:

            self.mostrar_erro(
                "O dispositivo selecionado não possui um ID válido."
            )

            return

        # -----------------------------------------------------
        # Mensagem
        # -----------------------------------------------------

        self.ids.erro_texto.text_color = (
            0.49,
            0.77,
            0.50,
            1
        )

        self.ids.erro_texto.text = (
            "A configurar o dispositivo..."
        )

        self.ids.btn_wifi.disabled = True

        try:

            # -------------------------------------------------
            # Enviar configuração para ESP32 de REGA
            # -------------------------------------------------

            resposta = requests.post(

                f"http://{ESP32_IP}/wifi",

                json={
                    "ssid": ssid,
                    "password": password,
                    "user_id": self.user_id,
                    "device_id": device_id
                },

                timeout=3
            )

            resultado = resposta.json()

            # -------------------------------------------------
            # ESP32 recebeu configuração
            # -------------------------------------------------

            if resultado.get("success", False):

                self.ids.erro_texto.text_color = (
                    0.49,
                    0.77,
                    0.50,
                    1
                )

                self.ids.erro_texto.text = (
                    "Dispositivo configurado com sucesso!\n"
                    "A voltar aos dispositivos de rega..."
                )

                # O ESP32 continua o processo em background.
                Clock.schedule_once(
                    lambda dt:
                    self.finalizar_associacao(),
                    7
                )

            else:

                self.ids.btn_wifi.disabled = False

                self.mostrar_erro(
                    resultado.get(
                        "message",
                        "Não foi possível configurar o Wi-Fi."
                    )
                )

        except requests.exceptions.ConnectionError:

            self.ids.btn_wifi.disabled = False

            self.mostrar_erro(
                "Não foi possível comunicar com o ESP32.\n"
                "Ligue-se à rede do dispositivo de rega."
            )

        except requests.exceptions.Timeout:

            # -------------------------------------------------
            # O ESP32 pode ter recebido o pedido e continuar
            # a processá-lo em background.
            # -------------------------------------------------

            self.ids.erro_texto.text_color = (
                0.49,
                0.77,
                0.50,
                1
            )

            self.ids.erro_texto.text = (
                "A configurar o dispositivo...\n"
                "A voltar aos dispositivos de rega..."
            )

            Clock.schedule_once(
                lambda dt:
                self.finalizar_associacao(),
                7
            )

        except Exception as erro:

            print(
                "Erro ao configurar Wi-Fi:",
                erro
            )

            self.ids.btn_wifi.disabled = False

            self.mostrar_erro(
                "Erro inesperado ao configurar o Wi-Fi."
            )


    # =========================================================
    # FINALIZAR ASSOCIAÇÃO
    # =========================================================

    def finalizar_associacao(self):
        destino = getattr(self, "return_screen", "home")

        self.limpar_formulario()

        if self.manager.has_screen(destino):
            self.manager.current = destino
        else:
            self.manager.current = "home"

        if destino == "device":
            tela = self.manager.get_screen("device")
            tela.carregar_historico_regas()
            tela.verificar_rega_associada()


    # =========================================================
    # MOSTRAR ERRO
    # =========================================================

    def mostrar_erro(self, mensagem):

        self.ids.erro_texto.text_color = (
            1,
            0,
            0,
            1
        )

        self.ids.erro_texto.text = mensagem


    # =========================================================
    # VOLTAR
    # =========================================================

    def voltar(self):
        destino = getattr(self, "return_screen", "home")

        self.limpar_formulario()

        if self.manager.has_screen(destino):
            self.manager.current = destino
        else:
            self.manager.current = "home"