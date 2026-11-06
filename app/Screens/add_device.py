# =============================================================
# BIBLIOTECAS
# =============================================================

import requests

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder


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

Builder.load_file("kv/add_device.kv")

API_URL = "http://85.242.41.127:8000"

# IP padrão do ESP32 quando cria o seu Access Point
ESP32_IP = "192.168.4.1"


# =============================================================
# ECRÃ ADICIONAR DISPOSITIVO
# =============================================================

class add_device(Screen):

    user_id = None
    codigo_dispositivo = None


    # =========================================================
    # LIMPAR FORMULÁRIO / REPOR ESTADO INICIAL
    # =========================================================

    def limpar_formulario(self):

        self.codigo_dispositivo = None

        # Limpar todos os campos
        self.ids.TextFieldCodigo.text = ""
        self.ids.campo_ssid.text = ""
        self.ids.campo_password.text = ""

        # Limpar mensagem
        self.ids.erro_texto.text = ""

        # Reativar fase do código
        self.ids.TextFieldCodigo.disabled = False
        self.ids.btn.disabled = False

        # Desativar fase Wi-Fi
        self.ids.campo_ssid.disabled = True
        self.ids.campo_password.disabled = True
        self.ids.btn_wifi.disabled = True

        # Repor visibilidade
        self.ids.texto_explicativo.opacity = 1
        self.ids.TextFieldCodigo.opacity = 1
        self.ids.btn.opacity = 1

        self.ids.texto_wifi.opacity = 0
        self.ids.campo_ssid.opacity = 0
        self.ids.campo_password.opacity = 0
        self.ids.btn_wifi.opacity = 0


    # =========================================================
    # AO ENTRAR NA JANELA
    # =========================================================

    def on_enter(self):

        # Cada vez que se entra neste ecrã, começar de novo.
        self.limpar_formulario()
        self.mostrar_fase_codigo()
        self.animar_entrada()


    # =========================================================
    # FASE 1 — CÓDIGO
    # =========================================================

    def mostrar_fase_codigo(self):

        self.ids.texto_explicativo.opacity = 1
        self.ids.TextFieldCodigo.opacity = 1
        self.ids.btn.opacity = 1

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

        self.ids.texto_wifi.opacity = 0
        self.ids.campo_ssid.opacity = 0
        self.ids.campo_ssid.disabled = True
        self.ids.campo_password.opacity = 0
        self.ids.campo_password.disabled = True
        self.ids.btn_wifi.opacity = 0


        # Logo

        delayed(
            lambda: fade_in(
                self.ids.logo_add,
                duration=0.8
            ),
            0
        )


        # Botão voltar

        delayed(
            lambda: fade_in(
                self.ids.botao_voltar,
                duration=0.8
            ),
            0
        )


        # Título

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


        # Texto

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


        # Campo código

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


        # Botão

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
        # Verificar código
        # -----------------------------------------------------

        if not codigo:

            self.mostrar_erro(
                "Insira o código do dispositivo."
            )

            return


        # -----------------------------------------------------
        # Verificar utilizador
        # -----------------------------------------------------

        if self.user_id is None:

            self.mostrar_erro(
                "Utilizador não identificado."
            )

            return


        try:

            # -------------------------------------------------
            # Verificar se o dispositivo existe
            # -------------------------------------------------

            resposta = requests.get(
                f"{API_URL}/devices/code/{codigo}",
                timeout=5
            )

            if resposta.status_code != 200:

                self.mostrar_erro(
                    "Dispositivo não encontrado."
                )

                return


            resultado = resposta.json()

            if not resultado.get("success", False):

                self.mostrar_erro(
                    resultado.get(
                        "message",
                        "Dispositivo não encontrado."
                    )
                )

                return


            # -------------------------------------------------
            # Guardar código
            # -------------------------------------------------

            self.codigo_dispositivo = codigo


            # -------------------------------------------------
            # Passar para configuração Wi-Fi
            # -------------------------------------------------

            self.mostrar_configuracao_wifi()


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
                "Erro ao verificar dispositivo:",
                erro
            )

            self.mostrar_erro(
                "Erro inesperado."
            )


    # =========================================================
    # FASE 2 — MOSTRAR CONFIGURAÇÃO WI-FI
    # =========================================================

    def mostrar_configuracao_wifi(self):

        # Esconder fase do código

        self.ids.texto_explicativo.opacity = 0
        self.ids.TextFieldCodigo.opacity = 0
        self.ids.TextFieldCodigo.disabled = True
        self.ids.btn.opacity = 0
        self.ids.btn.disabled = True


        # Mostrar fase Wi-Fi

        self.ids.texto_wifi.opacity = 1
        self.ids.campo_ssid.opacity = 1
        self.ids.campo_ssid.disabled = False
        self.ids.campo_password.opacity = 1
        self.ids.campo_password.disabled = False
        self.ids.btn_wifi.opacity = 1
        self.ids.btn_wifi.disabled = False


        self.ids.erro_texto.text = ""


    # =========================================================
    # ENVIAR WI-FI PARA ESP32
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


        self.ids.erro_texto.text_color = (
            0.49,
            0.77,
            0.50,
            1
        )

        self.ids.erro_texto.text = (
            "A configurar o dispositivo..."
        )


        try:

            # -------------------------------------------------
            # Enviar credenciais diretamente para ESP32
            # -------------------------------------------------

            resposta = requests.post(

                f"http://{ESP32_IP}/wifi",

                json={
                    "ssid": ssid,
                    "password": password,
                    "user_id": self.user_id
                },

                timeout=15
            )


            resultado = resposta.json()


            # -------------------------------------------------
            # ESP32 confirmou configuração
            # -------------------------------------------------

            if resultado.get("success", False):

                # O ESP32 já confirmou a configuração Wi-Fi
                # e a associação do dispositivo à conta.
                self.ids.erro_texto.text_color = (
                    0.49,
                    0.77,
                    0.50,
                    1
                )

                self.ids.erro_texto.text = (
                    "Dispositivo associado com sucesso!\n"
                    "A voltar ao início..."
                )

                # Desativar o botão para evitar pedidos duplicados.
                self.ids.btn_wifi.disabled = True

                from kivy.clock import Clock

                # Dar tempo para o utilizador ver a confirmação.
                Clock.schedule_once(
                    lambda dt: self.finalizar_associacao(),
                    1.2
                )


            else:

                self.mostrar_erro(
                    resultado.get(
                        "message",
                        "Não foi possível configurar o Wi-Fi."
                    )
                )


        except requests.exceptions.ConnectionError:

            self.mostrar_erro(
                "Não foi possível comunicar com o ESP32.\n"
                "Ligue-se à rede GreenGadget-Setup."
            )


        except requests.exceptions.Timeout:

            self.mostrar_erro(
                "O ESP32 demorou demasiado a responder."
            )


        except Exception as erro:

            print(
                "Erro ao configurar Wi-Fi:",
                erro
            )

            self.mostrar_erro(
                "Erro inesperado ao configurar o Wi-Fi."
            )


    # =========================================================
    # FINALIZAR ASSOCIAÇÃO
    # =========================================================

    def finalizar_associacao(self):

        # Limpar o estado deste ecrã para que, quando voltar,
        # seja possível adicionar outro dispositivo sem dados antigos.
        self.limpar_formulario()

        # Voltar ao Home.
        self.manager.current = "home"


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

        self.limpar_formulario()
        self.manager.current = "home"