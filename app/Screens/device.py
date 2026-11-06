# =============================================================
# DEVICE
# =============================================================

import requests

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Color, Line
from kivy.metrics import dp
from datetime import datetime, timedelta

# =============================================================
# ANIMAÇÕES
# =============================================================

from Animacoes import (
    delayed,
    fade_in,
    dropdown_open,
    dropdown_close,
    slide_down,
    slide_right
)


# =============================================================
# KV
# =============================================================

Builder.load_file(
    "kv/device.kv"
)


# =============================================================
# API
# =============================================================

API_URL = "http://85.242.41.127:8000"


class SoilHumidityChart(Widget):

    def __init__(self, points=None, on_point_selected=None, **kwargs):
        super().__init__(**kwargs)
        self.points = points or []
        self.on_point_selected = on_point_selected
        self.point_positions = []
        self._axis_labels = []

        self.bind(size=self.redraw, pos=self.redraw)
        self.redraw()

    def _limpar_etiquetas(self):
        for etiqueta in self._axis_labels:
            self.remove_widget(etiqueta)
        self._axis_labels.clear()

    def _etiqueta(self, texto, pos, tamanho, font_size=10, halign="center"):
        etiqueta = Label(
            text=texto,
            color=(0.25, 0.35, 0.25, 1),
            font_size=f"{font_size}sp",
            size_hint=(None, None),
            size=tamanho,
            pos=pos,
            halign=halign,
            valign="middle"
        )
        etiqueta.text_size = tamanho
        self.add_widget(etiqueta)
        self._axis_labels.append(etiqueta)

    def redraw(self, *args):
        self.canvas.clear()
        self.point_positions.clear()
        self._limpar_etiquetas()

        margem_esquerda = dp(42)
        margem_direita = dp(8)
        margem_inferior = dp(34)
        margem_superior = dp(12)

        x0 = self.x + margem_esquerda
        y0 = self.y + margem_inferior

        largura = max(
            dp(10),
            self.width - margem_esquerda - margem_direita
        )
        altura = max(
            dp(10),
            self.height - margem_inferior - margem_superior
        )

        with self.canvas:
            Color(1, 1, 1, 1)
            from kivy.graphics import Rectangle, Ellipse
            Rectangle(pos=self.pos, size=self.size)

            # Grelha e eixo vertical de humidade (0–100%).
            for valor in range(0, 101, 20):
                y = y0 + altura * valor / 100

                Color(0.84, 0.88, 0.84, 1)
                Line(
                    points=[x0, y, x0 + largura, y],
                    width=1
                )

                self._etiqueta(
                    f"{valor}%",
                    (self.x, y - dp(8)),
                    (margem_esquerda - dp(5), dp(16)),
                    font_size=9,
                    halign="right"
                )

            Color(0.30, 0.40, 0.30, 1)
            Line(
                points=[x0, y0, x0, y0 + altura],
                width=1.2
            )
            Line(
                points=[x0, y0, x0 + largura, y0],
                width=1.2
            )

            # Desenhar a linha e os pontos.
            total = len(self.points)
            coordenadas = []

            for indice, ponto in enumerate(self.points):
                data, valor = ponto

                if valor is None:
                    continue

                try:
                    valor = float(valor)
                except (ValueError, TypeError):
                    continue

                x = x0 + largura * indice / max(1, total - 1)
                y = y0 + altura * max(0, min(100, valor)) / 100

                self.point_positions.append((x, y, data, valor))
                coordenadas.extend([x, y])

            if len(coordenadas) >= 4:
                Color(0.30, 0.67, 0.34, 1)
                Line(points=coordenadas, width=2)

            for x, y, data, valor in self.point_positions:
                Color(0.20, 0.55, 0.25, 1)
                Ellipse(
                    pos=(x - dp(3), y - dp(3)),
                    size=(dp(6), dp(6))
                )

        # Etiquetas horárias no eixo X.
        if self.points:
            total = len(self.points)
            indices = sorted(set([
                0,
                total // 2,
                total - 1
            ]))

            for indice in indices:
                data = self.points[indice][0]
                x = x0 + largura * indice / max(1, total - 1)

                if hasattr(data, "strftime"):
                    texto = data.strftime("%H:%M")
                else:
                    texto = str(data)[11:16]

                self._etiqueta(
                    texto,
                    (x - dp(25), self.y + dp(4)),
                    (dp(50), dp(18)),
                    font_size=9
                )

        # Identificação dos eixos.
        self._etiqueta(
            "Hora",
            (x0 + largura / 2 - dp(30), self.y - dp(1)),
            (dp(60), dp(16)),
            font_size=9
        )

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if not self.point_positions:
            return super().on_touch_down(touch)

        ponto = min(
            self.point_positions,
            key=lambda p: (
                (p[0] - touch.x) ** 2
                + (p[1] - touch.y) ** 2
            )
        )

        distancia = (
            (ponto[0] - touch.x) ** 2
            + (ponto[1] - touch.y) ** 2
        ) ** 0.5

        if distancia <= dp(24):
            if self.on_point_selected:
                self.on_point_selected(ponto[2], ponto[3])
            return True

        return super().on_touch_down(touch)



class device(Screen):

    # =========================================================
    # DADOS DO DISPOSITIVO
    # =========================================================
    user_id = None

    device_id = None
    device_name = None
    evento_atualizacao = None
    plant_id = None
    plant_name = None

    image_path = None

    plantas = []

    menu_plantas_aberto = False


    # =========================================================
    # ANIMAÇÃO DA PÁGINA DO DISPOSITIVO
    # =========================================================

    def animar_pagina(self):

        elementos = [
            self.ids.device_image,
            self.ids.device_name,
            self.ids.plant_name,
            self.ids.label_temperatura,
            self.ids.temperatura,
            self.ids.label_humidade,
            self.ids.humidade,
            self.ids.label_humidade_solo,
            self.ids.humidade_solo,
            self.ids.label_historico,
            self.ids.historico_vazio,
        ]

        atrasos = [0.00, 0.08, 0.16, 0.24, 0.32, 0.40, 0.48, 0.56, 0.64, 0.72, 0.80]

        for elemento, atraso in zip(elementos, atrasos):
            elemento.opacity = 0
            delayed(
                lambda elemento=elemento: fade_in(elemento, duration=.45),
                atraso
            )

    def on_pre_enter(self, *args):
        self.animar_pagina()

    def on_enter(self, *args):
        self.iniciar_atualizacao()
        self.verificar_rega_associada()
        self.carregar_historico_regas()

    def on_leave(self, *args):
        self.parar_atualizacao()

    def iniciar_atualizacao(self):
        self.parar_atualizacao()

        self.obter_dados_sensores()

        self.evento_atualizacao = Clock.schedule_interval(
            self.atualizar_dados_sensores,
            5
        )

    def atualizar_dados_sensores(self, dt):
        if self.device_id is not None:
            self.obter_dados_sensores()

    def parar_atualizacao(self):
        if self.evento_atualizacao is not None:
            self.evento_atualizacao.cancel()
            self.evento_atualizacao = None


    # =========================================================
    # CARREGAR DISPOSITIVO
    # =========================================================

    def carregar_dispositivo(
        self,
        dispositivo
    ):

        self.device_id = (
            dispositivo["id"]
        )

        self.device_name = (
            dispositivo["name"]
        )

        self.ids.device_name.text = (
            self.device_name
        )

        self.plant_id = None
        self.plant_name = None
        self.image_path = None

        self.ids.plant_name.text = (
            "Planta não definida"
        )

        self.ids.device_image.source = ""


        self.fechar_lista_plantas(
            animar=False
        )


        # Obter informação do dispositivo
        self.obter_informacao()



    # =========================================================
    # OBTER INFORMAÇÃO DO DISPOSITIVO
    # =========================================================

    def obter_informacao(self):

        try:

            resposta = requests.get(
                f"{API_URL}/device/{self.device_id}",
                timeout=5
            )

            resultado = (
                resposta.json()
            )


            if not resultado.get(
                "success"
            ):

                print(
                    "Erro ao obter dispositivo."
                )

                return


            dispositivo = (
                resultado["device"]
            )


            # -------------------------------------------------
            # Nome
            # -------------------------------------------------

            self.device_name = (
                dispositivo["name"]
            )

            self.ids.device_name.text = (
                self.device_name
            )


            # -------------------------------------------------
            # Planta
            # -------------------------------------------------

            self.plant_id = (
                dispositivo.get(
                    "plant_id"
                )
            )


            if self.plant_id:

                self.obter_planta(
                    self.plant_id
                )

            else:

                self.plant_id = None
                self.plant_name = None

                self.ids.plant_name.text = (
                    "Planta não definida"
                )

                self.ids.selecionar_planta.text = (
                    "Selecionar planta"
                )


            # -------------------------------------------------
            # Imagem
            # -------------------------------------------------

            self.image_path = (
                dispositivo.get(
                    "image_path"
                )
            )


            if self.image_path:

                self.ids.device_image.source = (
                    self.image_path
                )


        except Exception as erro:

            print(
                "Erro ao obter informação "
                "do dispositivo:",
                erro
            )


    # =========================================================
    # OBTER PLANTA
    # =========================================================

    def obter_planta(
        self,
        plant_id
    ):

        try:

            resposta = requests.get(
                f"{API_URL}/plants/{plant_id}",
                timeout=5
            )

            resultado = (
                resposta.json()
            )


            if not resultado.get(
                "success"
            ):

                return


            planta = (
                resultado["plant"]
            )


            self.plant_name = (
                planta["name"]
            )


            self.ids.plant_name.text = (
                self.plant_name
            )


            self.ids.selecionar_planta.text = (
                self.plant_name
            )


        except Exception as erro:

            print(
                "Erro ao obter informação "
                "da planta:",
                erro
            )


    # =========================================================
    # OBTER DADOS DOS SENSORES
    # =========================================================

    def obter_dados_sensores(self):

        try:

            resposta = requests.get(
                f"{API_URL}/devices/"
                f"{self.device_id}/data",
                timeout=5
            )

            resultado = (
                resposta.json()
            )


            if not resultado.get(
                "success"
            ):

                return


            dados = resultado.get(
                "data",
                []
            )


            if not dados:

                return


            atual = dados[0]


            temperatura = (
                atual.get(
                    "temperature"
                )
            )


            humidade = (
                atual.get(
                    "air_humidity"
                )
            )


            humidade_solo = (
                atual.get(
                    "soil_humidity"
                )
            )


            if temperatura is not None:

                self.ids.temperatura.text = (
                    f"{temperatura} °C"
                )


            if humidade is not None:

                self.ids.humidade.text = (
                    f"{humidade} %"
                )


            if humidade_solo is not None:

                self.ids.humidade_solo.text = (
                    f"{humidade_solo} %"
                )


        except Exception as erro:

            print(
                "Erro ao obter dados "
                "dos sensores:",
                erro
            )


    # =========================================================
    # ABRIR DEFINIÇÕES
    # =========================================================

    def abrir_definicoes(self):

        # -----------------------------------------------------
        # Fechar dropdown
        # -----------------------------------------------------

        self.fechar_lista_plantas(
            animar=False
        )


        # -----------------------------------------------------
        # Preencher dados atuais
        # -----------------------------------------------------

        self.ids.novo_nome.text = (
            self.device_name or ""
        )


        if self.plant_name:

            self.ids.selecionar_planta.text = (
                self.plant_name
            )

        else:

            self.ids.selecionar_planta.text = (
                "Selecionar planta"
            )


        self.ids.mensagem_config.text = ""


        # -----------------------------------------------------
        # Mostrar painel
        # -----------------------------------------------------

        self.ids.settings_panel.opacity = 1
        self.ids.settings_panel.disabled = False


        # -----------------------------------------------------
        # Preparar elementos para animação
        # -----------------------------------------------------

        elementos = [

            self.ids.label_nome,
            self.ids.novo_nome,

            self.ids.label_planta,
            self.ids.selecionar_planta,

            self.ids.label_imagem,
            self.ids.botao_imagem
        ]


        for elemento in elementos:

            elemento.opacity = 0


        self.ids.titulo_definicoes.opacity = 0

        self.ids.botao_guardar.opacity = 0
        self.ids.botao_desassociar.opacity = 0


        # =====================================================
        # TÍTULO
        #
        # Slide down + fade in
        # =====================================================

        def animar_titulo():

            slide_down(
                self.ids.titulo_definicoes,
                offset=.10,
                duration=.7
            )

            fade_in(
                self.ids.titulo_definicoes,
                duration=.7
            )


        delayed(
            animar_titulo,
            .05
        )


        # =====================================================
        # NOME
        #
        # Label + campo
        # Slide right + fade in
        # =====================================================

        def animar_nome():

            slide_right(
                self.ids.label_nome,
                offset=.10,
                duration=.55
            )

            fade_in(
                self.ids.label_nome,
                duration=.55
            )


            slide_right(
                self.ids.novo_nome,
                offset=.10,
                duration=.55
            )

            fade_in(
                self.ids.novo_nome,
                duration=.55
            )


        delayed(
            animar_nome,
            .25
        )


        # =====================================================
        # PLANTA
        #
        # Entra depois do nome
        # =====================================================

        def animar_planta():

            slide_right(
                self.ids.label_planta,
                offset=.10,
                duration=.55
            )

            fade_in(
                self.ids.label_planta,
                duration=.55
            )


            slide_right(
                self.ids.selecionar_planta,
                offset=.10,
                duration=.55
            )

            fade_in(
                self.ids.selecionar_planta,
                duration=.55
            )


        delayed(
            animar_planta,
            .50
        )


        # =====================================================
        # IMAGEM
        #
        # Entra depois da planta
        # =====================================================

        def animar_imagem():

            slide_right(
                self.ids.label_imagem,
                offset=.10,
                duration=.55
            )

            fade_in(
                self.ids.label_imagem,
                duration=.55
            )


            slide_right(
                self.ids.botao_imagem,
                offset=.10,
                duration=.55
            )

            fade_in(
                self.ids.botao_imagem,
                duration=.55
            )


        delayed(
            animar_imagem,
            .75
        )


        # =====================================================
        # GUARDAR
        #
        # Apenas fade-in
        # =====================================================

        delayed(
            lambda:
            fade_in(
                self.ids.botao_guardar,
                duration=.7
            ),
            1.05
        )


        # =====================================================
        # DESASSOCIAR
        #
        # Apenas fade-in
        # =====================================================

        delayed(
            lambda:
            fade_in(
                self.ids.botao_desassociar,
                duration=.7
            ),
            1.25
        )


    # =========================================================
    # FECHAR DEFINIÇÕES
    # =========================================================

    def fechar_definicoes(self):

        self.fechar_lista_plantas(
            animar=False
        )

        self.ids.settings_panel.opacity = 0
        self.ids.settings_panel.disabled = True


    # =========================================================
    # ABRIR LISTA DE PLANTAS
    # =========================================================

    def abrir_lista_plantas(self):

        if self.menu_plantas_aberto:

            self.fechar_lista_plantas()

            return


        try:

            resposta = requests.get(
                f"{API_URL}/plants",
                timeout=5
            )

            resultado = (
                resposta.json()
            )


            if not resultado.get(
                "success"
            ):

                self.ids.mensagem_config.text = (
                    "Não foi possível obter as plantas."
                )

                return


            self.plantas = (
                resultado.get(
                    "plants",
                    []
                )
            )


            if not self.plantas:

                self.ids.mensagem_config.text = (
                    "Não existem plantas disponíveis."
                )

                return


            self.ids.mensagem_config.text = ""


            # -------------------------------------------------
            # Preparar pesquisa
            # -------------------------------------------------

            self.ids.pesquisa_planta.text = ""

            self.ids.selecionar_planta.opacity = 0
            self.ids.selecionar_planta.disabled = True

            self.ids.pesquisa_planta.opacity = 1
            self.ids.pesquisa_planta.disabled = False


            # -------------------------------------------------
            # Abrir lista
            # -------------------------------------------------

            self.ids.lista_plantas.disabled = False

            self.menu_plantas_aberto = True


            self.mostrar_plantas(
                self.plantas
            )


            dropdown_open(
                self.ids.lista_plantas,
                target_height=180,
                duration=1
            )


            self.ids.pesquisa_planta.focus = True


        except Exception as erro:

            print(
                "Erro ao carregar plantas:",
                erro
            )

            self.ids.mensagem_config.text = (
                "Erro ao comunicar com a API."
            )


    # =========================================================
    # FECHAR LISTA DE PLANTAS
    # =========================================================

    def fechar_lista_plantas(
        self,
        animar=True
    ):

        self.menu_plantas_aberto = False


        # -----------------------------------------------------
        # Pesquisa
        # -----------------------------------------------------

        if "pesquisa_planta" in self.ids:

            self.ids.pesquisa_planta.opacity = 0

            self.ids.pesquisa_planta.disabled = True

            self.ids.pesquisa_planta.text = ""


        # -----------------------------------------------------
        # Botão
        # -----------------------------------------------------

        if "selecionar_planta" in self.ids:

            self.ids.selecionar_planta.opacity = 1

            self.ids.selecionar_planta.disabled = False


        # -----------------------------------------------------
        # Lista
        # -----------------------------------------------------

        if "lista_plantas" in self.ids:

            if animar:

                dropdown_close(
                    self.ids.lista_plantas,
                    duration=1
                )


                Clock.schedule_once(
                    lambda dt:
                    setattr(
                        self.ids.lista_plantas,
                        "disabled",
                        True
                    ),
                    1
                )


            else:

                self.ids.lista_plantas.height = 0

                self.ids.lista_plantas.opacity = 0

                self.ids.lista_plantas.disabled = True


    # =========================================================
    # MOSTRAR PLANTAS
    # =========================================================

    def mostrar_plantas(
        self,
        plantas
    ):

        lista = (
            self.ids.lista_resultados
        )

        lista.clear_widgets()


        botoes = []


        for planta in plantas:

            botao = Button(

                text=planta["name"],

                size_hint_y=None,

                height="44dp",

                background_normal="",

                background_color=(
                    1,
                    1,
                    1,
                    0
                ),

                color=(
                    0.49,
                    0.77,
                    0.50,
                    1
                ),

                font_name=(
                    "extras/"
                    "Montserrat-Bold.ttf"
                ),

                font_size="16sp",

                halign="center"
            )


            botao.plant_id = (
                planta["id"]
            )

            botao.plant_name = (
                planta["name"]
            )


            botao.bind(
                on_release=
                self.selecionar_planta
            )


            lista.add_widget(
                botao
            )

            botoes.append(
                botao
            )


        # -----------------------------------------------------
        # Fade-in dos resultados
        # -----------------------------------------------------

        for botao in botoes:

            botao.opacity = 0


        from Animacoes import fade_in_lista

        fade_in_lista(
            botoes,
            duration=.30,
            intervalo=.08
        )


    # =========================================================
    # FILTRAR PLANTAS
    # =========================================================

    def filtrar_plantas(
        self,
        texto
    ):

        texto = (
            texto.strip().lower()
        )


        if not texto:

            self.mostrar_plantas(
                self.plantas
            )

            return


        plantas_filtradas = []


        for planta in self.plantas:

            nome = (
                planta["name"].lower()
            )


            if texto in nome:

                plantas_filtradas.append(
                    planta
                )


        self.mostrar_plantas(
            plantas_filtradas
        )


    # =========================================================
    # SELECIONAR PLANTA
    # =========================================================

    def selecionar_planta(
        self,
        botao
    ):

        self.plant_id = (
            botao.plant_id
        )

        self.plant_name = (
            botao.plant_name
        )


        self.ids.selecionar_planta.text = (
            self.plant_name
        )

        self.ids.plant_name.text = (
            self.plant_name
        )


        self.fechar_lista_plantas()


    # =========================================================
    # GUARDAR ALTERAÇÕES
    # =========================================================

    def guardar_alteracoes(
        self
    ):

        novo_nome = (
            self.ids.novo_nome.text.strip()
        )


        # -----------------------------------------------------
        # Validar nome
        # -----------------------------------------------------

        if not novo_nome:

            self.ids.mensagem_config.text = (
                "Insira um nome para o dispositivo."
            )

            return


        # -----------------------------------------------------
        # Validar planta
        # -----------------------------------------------------

        if self.plant_id is None:

            self.ids.mensagem_config.text = (
                "Selecione uma planta."
            )

            return


        try:

            dados = {

                "name":
                    novo_nome,

                "plant_id":
                    self.plant_id

            }


            resposta = requests.put(

                f"{API_URL}/devices/"
                f"{self.device_id}",

                json=dados,

                timeout=5
            )


            resultado = (
                resposta.json()
            )


            # -------------------------------------------------
            # ERRO
            # -------------------------------------------------

            if not resultado.get(
                "success"
            ):

                self.ids.mensagem_config.text = (
                    resultado.get(
                        "message",
                        "Erro ao guardar alterações."
                    )
                )

                return


            # -------------------------------------------------
            # SUCESSO
            # -------------------------------------------------

            self.device_name = (
                novo_nome
            )


            self.ids.device_name.text = (
                novo_nome
            )


            self.ids.plant_name.text = (
                self.plant_name
            )


            self.ids.mensagem_config.text = (
                "Alterações guardadas com sucesso."
            )


            # -------------------------------------------------
            # Fechar automaticamente
            # -------------------------------------------------

            Clock.schedule_once(
                lambda dt:
                self.fechar_definicoes(),
                .7
            )


        except Exception as erro:

            print(
                "Erro ao guardar alterações:",
                erro
            )


            self.ids.mensagem_config.text = (
                "Erro ao comunicar com a API."
            )


    # =========================================================
    # ESCOLHER IMAGEM
    # =========================================================

    def escolher_imagem(self):

        layout = BoxLayout(
            orientation="vertical"
        )


        filechooser = FileChooserIconView(

            filters=[
                "*.png",
                "*.jpg",
                "*.jpeg"
            ]

        )


        botoes = BoxLayout(

            size_hint_y=None,

            height="50dp"

        )


        selecionar = Button(
            text="Selecionar"
        )


        cancelar = Button(
            text="Cancelar"
        )


        botoes.add_widget(
            selecionar
        )

        botoes.add_widget(
            cancelar
        )


        layout.add_widget(
            filechooser
        )

        layout.add_widget(
            botoes
        )


        popup = Popup(

            title="Escolher imagem",

            content=layout,

            size_hint=(.9, .9)

        )


        def selecionar_imagem(
            instance
        ):

            if filechooser.selection:

                caminho = (
                    filechooser.selection[0]
                )


                self.enviar_imagem(
                    caminho
                )


                popup.dismiss()


        selecionar.bind(
            on_release=
            selecionar_imagem
        )


        cancelar.bind(
            on_release=
            popup.dismiss
        )


        popup.open()

    # =========================================================
    # DESASSOCIAR DISPOSITIVO
    # =========================================================

    def desassociar_dispositivo(self):

        try:
            # Obter o user_id a partir do dispositivo
            resposta_dispositivo = requests.get(
                f"{API_URL}/device/{self.device_id}",
                timeout=5
            )

            resultado_dispositivo = (
                resposta_dispositivo.json()
            )

            if not resultado_dispositivo.get("success"):
                self.ids.mensagem_config.text = (
                    "Não foi possível obter os dados do dispositivo."
                )

                return

            dispositivo = resultado_dispositivo.get(
                "device",
                {}
            )

            user_id = dispositivo.get("user_id")

            if user_id is None:
                self.ids.mensagem_config.text = (
                    "Este dispositivo não está associado."
                )

                return

            # -------------------------------------------------
            # Desassociar dispositivo
            # -------------------------------------------------

            resposta = requests.delete(
                f"{API_URL}/devices/"
                f"{self.device_id}/association",
                params={
                    "user_id": user_id
                },
                timeout=5
            )

            resultado = resposta.json()

            if not resultado.get("success"):
                self.ids.mensagem_config.text = (
                    resultado.get(
                        "message",
                        "Erro ao desassociar dispositivo."
                    )
                )

                return

            # -------------------------------------------------
            # Sucesso
            # -------------------------------------------------

            self.fechar_definicoes()

            self.manager.current = "home"

        except Exception as erro:

            print(
                "Erro ao desassociar dispositivo:",
                erro
            )

            self.ids.mensagem_config.text = (
                "Erro ao comunicar com a API."
            )


    # =========================================================
    # ENVIAR IMAGEM
    # =========================================================

    def enviar_imagem(
        self,
        caminho
    ):

        try:

            with open(
                caminho,
                "rb"
            ) as imagem:

                resposta = requests.post(

                    f"{API_URL}/devices/"
                    f"{self.device_id}/image",

                    files={
                        "file": imagem
                    },

                    timeout=15
                )


            resultado = (
                resposta.json()
            )


            if resultado.get(
                "success"
            ):

                self.ids.device_image.source = (
                    caminho
                )

                self.image_path = (
                    caminho
                )

                self.ids.mensagem_config.text = (
                    "Imagem alterada com sucesso."
                )


            else:

                self.ids.mensagem_config.text = (
                    resultado.get(
                        "message",
                        "Erro ao enviar imagem."
                    )
                )


        except Exception as erro:

            print(
                "Erro ao enviar imagem:",
                erro
            )


            self.ids.mensagem_config.text = (
                "Erro ao enviar imagem."
            )

    def verificar_rega_associada(self):
        if self.user_id is None or self.device_id is None:
            return

        try:
            resposta = requests.get(
                f"{API_URL}/watering-devices/{self.user_id}",
                timeout=5
            )
            resultado = resposta.json()

            associado = False

            if resultado.get("success"):
                associado = any(
                    item.get("device_id") == self.device_id
                    for item in resultado.get("watering_devices", [])
                )

            if "botao_associar_rega" in self.ids:
                self.ids.botao_associar_rega.icon = (
                    "water-check" if associado else "water-plus"
                )

        except Exception as erro:
            print("Erro ao verificar associação de rega:", erro)

    def associar_rega(self):
        if self.device_id is None or self.user_id is None:
            print("Não foi possível identificar o utilizador ou dispositivo.")
            return

        try:
            resposta = requests.get(
                f"{API_URL}/watering-devices/{self.user_id}",
                timeout=5
            )
            resultado = resposta.json()

            if resultado.get("success"):
                existente = next(
                    (
                        item for item in resultado.get("watering_devices", [])
                        if item.get("device_id") == self.device_id
                    ),
                    None
                )

                if existente:
                    popup = Popup(
                        title="Módulo de rega associado",
                        content=Label(
                            text=(
                                "Esta planta já tem o módulo de rega\n"
                                f"{existente.get('name') or existente.get('code')} "
                                "associado."
                            )
                        ),
                        size_hint=(0.85, 0.3)
                    )
                    popup.open()
                    return

            tela = self.manager.get_screen("add_watering")
            tela.definir_utilizador(self.user_id)

            tela.definir_dispositivo_recolha({
                "id": self.device_id,
                "name": self.device_name
            })

            tela.return_screen = "device"
            self.manager.current = "add_watering"

        except Exception as erro:
            print("Erro ao associar módulo de rega:", erro)

    def regar_manualmente(self):
        """Solicita uma rega manual para o módulo associado."""

        if self.user_id is None or self.device_id is None:
            self.mostrar_popup_rega(
                "Não foi possível identificar o dispositivo. "
                "Volta à página e tenta novamente."
            )
            return

        try:
            resposta = requests.get(
                f"{API_URL}/watering-devices/{self.user_id}",
                timeout=5
            )
            resposta.raise_for_status()
            resultado = resposta.json()

            modulos = (
                resultado.get("watering_devices", [])
                if resultado.get("success")
                else []
            )

            modulo = next(
                (
                    item for item in modulos
                    if str(item.get("device_id"))
                    == str(self.device_id)
                ),
                None
            )

            if not modulo:
                self.mostrar_popup_rega(
                    "É necessário adicionar um dispositivo de rega "
                    "antes de poderes efetuar a rega manual.",
                    mostrar_botao_adicionar=True
                )
                return

            # Duração definida para a planta, ou 5 segundos.
            duracao = 5

            if self.plant_id is not None:
                resposta_planta = requests.get(
                    f"{API_URL}/plants/{self.plant_id}",
                    timeout=5
                )

                if resposta_planta.ok:
                    dados_planta = resposta_planta.json()
                    planta = dados_planta.get("plant", {})

                    try:
                        duracao = int(
                            planta.get("watering_duration_seconds")
                            or duracao
                        )
                    except (TypeError, ValueError):
                        pass

            resposta = requests.post(
                f"{API_URL}/watering-devices/"
                f"{modulo['id']}/command",
                json={
                    "duration_seconds": max(1, duracao),
                    "reason": "manual"
                },
                timeout=8
            )

            try:
                dados = resposta.json()
            except ValueError:
                dados = {}

            if resposta.ok and dados.get("success"):
                self.mostrar_popup_rega(
                    "Pedido de rega enviado com sucesso.\n"
                    f"Duração prevista: {max(1, duracao)} segundos."
                )
                self.carregar_historico_regas()
            else:
                mensagem = (
                    dados.get("detail")
                    or dados.get("message")
                    or "Não foi possível iniciar a rega manual."
                )
                self.mostrar_popup_rega(str(mensagem))

        except requests.RequestException:
            self.mostrar_popup_rega(
                "Não foi possível comunicar com o servidor. "
                "Verifica a ligação e tenta novamente."
            )

        except Exception as erro:
            print("Erro ao solicitar rega manual:", erro)
            self.mostrar_popup_rega(
                "Ocorreu um erro ao tentar iniciar a rega."
            )

    def mostrar_popup_rega(
        self,
        mensagem,
        mostrar_botao_adicionar=False
    ):
        """Mostra o resultado do pedido de rega."""

        conteudo = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(16)
        )

        texto = Label(
            text=mensagem,
            halign="center",
            valign="middle",
            color=(0.25, 0.32, 0.25, 1)
        )

        texto.bind(
            size=lambda instancia, tamanho: setattr(
                instancia,
                "text_size",
                (tamanho[0] - dp(8), None)
            )
        )

        conteudo.add_widget(texto)

        botoes = BoxLayout(
            size_hint_y=None,
            height=dp(44),
            spacing=dp(8)
        )

        fechar = Button(
            text="Fechar",
            background_normal="",
            background_color=(0.49, 0.77, 0.50, 1),
            color=(1, 1, 1, 1)
        )

        botoes.add_widget(fechar)

        popup = Popup(
            title="Rega manual",
            content=conteudo,
            size_hint=(0.86, None),
            height=dp(
                220 if mostrar_botao_adicionar else 190
            ),
            auto_dismiss=True,
            background="",
            background_color=(1, 1, 1, 1),
            title_color=(0.20, 0.35, 0.20, 1),
            separator_color=(0.49, 0.77, 0.50, 1)
        )

        fechar.bind(on_release=popup.dismiss)

        if mostrar_botao_adicionar:
            adicionar = Button(
                text="Adicionar dispositivo",
                background_normal="",
                background_color=(0.49, 0.77, 0.50, 1),
                color=(1, 1, 1, 1)
            )

            botoes.add_widget(adicionar)

            adicionar.bind(
                on_release=lambda *_: (
                    popup.dismiss(),
                    self.associar_rega()
                )
            )

        conteudo.add_widget(botoes)
        popup.open()

    def carregar_historico_regas(self):
        if self.device_id is None or self.user_id is None:
            return

        try:
            resposta = requests.get(
                f"{API_URL}/watering-devices/{self.user_id}",
                timeout=5
            )
            resposta.raise_for_status()
            resultado = resposta.json()

            if not resultado.get("success"):
                self.ids.historico_vazio.text = (
                    "Não foi possível consultar os módulos de rega."
                )
                return

            modulos = resultado.get("watering_devices", [])

            modulo = next(
                (
                    item for item in modulos
                    if str(item.get("device_id")) == str(self.device_id)
                ),
                None
            )

            if not modulo:
                self.ids.historico_vazio.text = (
                    "⚠ Ainda não tens um módulo de rega associado."
                )
                self.ids.historico_vazio.color = (0.85, 0.15, 0.15, 1)
                return

            resposta = requests.get(
                f"{API_URL}/watering-devices/{modulo['id']}/history",
                timeout=5
            )
            resposta.raise_for_status()
            dados = resposta.json()

            if not dados.get("success"):
                self.ids.historico_vazio.text = (
                    "Não foi possível carregar o histórico."
                )
                return

            regas = dados.get("history", [])

            if not regas:
                self.ids.historico_vazio.text = (
                    "Ainda não existem regas registadas."
                )
                self.ids.historico_vazio.color = (0.85, 0.15, 0.15, 1)
                return

            linhas = []

            for rega in regas[:5]:
                data = rega.get("executed_at") or rega.get("created_at")
                duracao = rega.get("duration_seconds")
                motivo = rega.get("reason") or "Motivo não indicado"
                estado = rega.get("status") or "Estado desconhecido"

                if data:
                    data = str(data).replace("T", " ")[:16]
                else:
                    data = "Data desconhecida"

                duracao_texto = (
                    f"{duracao} s" if duracao is not None
                    else "Duração desconhecida"
                )

                linhas.append(
                    f"{data}\n{duracao_texto} · {motivo} · {estado}"
                )

            self.ids.historico_vazio.color = (0.20, 0.25, 0.20, 1)
            self.ids.historico_vazio.text = "\n\n".join(linhas)

        except requests.RequestException as erro:
            print("Erro ao carregar histórico de regas:", erro)
            self.ids.historico_vazio.text = (
                "Erro de ligação ao consultar o histórico."
            )

    def abrir_grafico_humidade(self):
        if self.device_id is None:
            return

        try:
            resposta = requests.get(
                f"{API_URL}/devices/{self.device_id}/data",
                timeout=8
            )
            resposta.raise_for_status()
            resultado = resposta.json()
            dados = resultado.get("data", [])

        except Exception as erro:
            print("Erro ao obter dados para o gráfico:", erro)
            dados = []

        conteudo = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=dp(10)
        )

        titulo = Label(
            text="Humidade do solo ao longo do tempo",
            size_hint_y=None,
            height=dp(30),
            color=(0.25, 0.45, 0.27, 1)
        )
        conteudo.add_widget(titulo)

        barra = BoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(6)
        )
        conteudo.add_widget(barra)

        detalhe = Label(
            text="Seleciona um ponto para consultar a leitura.",
            size_hint_y=None,
            height=dp(36),
            color=(0.2, 0.3, 0.2, 1)
        )
        conteudo.add_widget(detalhe)

        grafico = SoilHumidityChart(
            on_point_selected=lambda data, valor: setattr(
                detalhe,
                "text",
                f"Humidade: {valor:.1f}% | Hora: "
                + (
                    data.strftime("%d/%m/%Y %H:%M")
                    if hasattr(data, "strftime")
                    else str(data)
                )
            )
        )
        conteudo.add_widget(grafico)

        fechar = Button(
            text="Fechar",
            size_hint_y=None,
            height=dp(42),
            background_normal="",
            background_color=(0.49, 0.77, 0.50, 1),
            color=(1, 1, 1, 1)
        )
        conteudo.add_widget(fechar)

        popup = Popup(
            title="Histórico de humidade",
            content=conteudo,
            size_hint=(0.95, 0.78),
            background="",
            background_color=(1, 1, 1, 1),
            title_color=(0.20, 0.35, 0.20, 1),
            separator_color=(0.49, 0.77, 0.50, 1),
            auto_dismiss=True
        )

        def mostrar_periodo(periodo):
            agora = datetime.now().astimezone()

            if periodo == "Diário":
                limite = agora - timedelta(days=1)
            elif periodo == "Semanal":
                limite = agora - timedelta(days=7)
            else:
                limite = agora - timedelta(days=30)

            pontos = []

            for registo in dados:
                valor = registo.get("soil_humidity")
                marca = (
                        registo.get("timestamp")
                        or registo.get("created_at")
                        or registo.get("recorded_at")
                )

                if valor is None or not marca:
                    continue

                try:
                    data = datetime.fromisoformat(
                        str(marca).replace("Z", "+00:00")
                    )

                    if data.tzinfo is None:
                        data = data.astimezone()

                    if data >= limite:
                        pontos.append((data, float(valor)))

                except (ValueError, TypeError):
                    continue

            pontos.sort(key=lambda ponto: ponto[0])
            grafico.points = pontos
            grafico.redraw()

            titulo.text = (
                f"Humidade do solo — {periodo.lower()} "
                f"({len(pontos)} registos)"
            )

            if not pontos:
                detalhe.text = (
                    "Não existem leituras neste período."
                )

        for periodo in ("Diário", "Semanal", "Mensal"):
            botao = Button(
                text=periodo,
                background_normal="",
                background_color=(0.85, 0.93, 0.85, 1),
                color=(0.2, 0.4, 0.2, 1)
            )
            botao.bind(
                on_release=lambda instancia, p=periodo:
                mostrar_periodo(p)
            )
            barra.add_widget(botao)

        mostrar_periodo("Diário")
        fechar.bind(on_release=popup.dismiss)
        popup.open()

    # =========================================================
    # VOLTAR
    # =========================================================

    def voltar(self):

        self.manager.current = "home"
