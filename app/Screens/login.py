#Bibliotecas
import re, requests
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from Animacoes import delayed, fade_in, slide_right

API_URL = "http://85.242.41.127:8000"

#Ficheiros
Builder.load_file("kv/login.kv")

class login(Screen):
    # Controlador de animação
    animacao_feita = False

    def on_enter(self):
        # Travão de animação
        if self.animacao_feita:
            return

        logo = self.ids.Logo
        texto = self.ids.Text
        email = self.ids.TextFieldEmail
        password = self.ids.TextFieldPassword
        btn = self.ids.Verpass
        btn2 = self.ids.btn

        delayed(lambda: fade_in(logo), 0)
        delayed(lambda: fade_in(texto), .3)
        delayed(lambda: [fade_in(email), slide_right(email)], .6)
        delayed(lambda: [fade_in(password), slide_right(password)], .9)
        delayed(lambda: fade_in(btn), 1.2)
        delayed(lambda: fade_in(btn2), 1.5)


        self.animacao_feita = True

    #Função para voltar à janela anterior
    def voltar(self):
        self.manager.current = "registerLogin"


    # Função para mostrar/esconder o conteudo no campo de password
    def toggle_password(self):
        password = self.ids.TextFieldPassword
        btn = self.ids.Verpass

        x = not password.password
        password.password = x

        if x:
            btn.icon = "eye-off"
            btn.text = "Ver palavra passe"
        else:
            btn.icon = "eye"
            btn.text = "Esconder palavra passe"

    # Função que faz o controlo do login
    def iniciar_login(self):
        dados = self.get_form_data()
        erro = self.validar_login(dados)

        # Erros da app
        if erro:
            self.ids.erro_texto.text_color = (1, 0, 0, 1)
            self.ids.erro_texto.text = erro
            return

        # Enviar dados para a API
        try:
            resposta = requests.post(
                f"{API_URL}/login",
                json={
                    "email": dados["email"],
                    "password": dados["password"]
                },
                timeout=5
            )

            resultado = resposta.json()

            # Login correto
            if resultado["success"]:
                self.ids.erro_texto.text_color = (0.49, 0.77, 0.50, 1)
                self.ids.erro_texto.text = resultado["message"]
                user_id = resultado["user"]["id"]
                self.manager.get_screen("home").definir_utilizador(user_id)
                self.manager.get_screen("add_device").definir_utilizador(user_id)
                self.manager.current = "home"

            # Erro vindo da API
            else:
                self.ids.erro_texto.text_color = (1, 0, 0, 1)
                self.ids.erro_texto.text = resultado["message"]

        except requests.exceptions.ConnectionError:
            self.ids.erro_texto.text_color = (1, 0, 0, 1)
            self.ids.erro_texto.text = "Não foi possível ligar ao servidor."

        except requests.exceptions.Timeout:
            self.ids.erro_texto.text_color = (1, 0, 0, 1)
            self.ids.erro_texto.text = "O servidor demorou demasiado a responder."

        except Exception as erro:
            print(erro)
            self.ids.erro_texto.text_color = (1, 0, 0, 1)
            self.ids.erro_texto.text = "Erro inesperado."

    # Função que vai buscar o conteudo dos textfield
    def get_form_data(self):
        return {
            "email": self.ids.TextFieldEmail.text.strip(),
            "password": self.ids.TextFieldPassword.text,
        }

    # Função de validação
    def validar_login(self, dados):
        validacoes = [
            (not dados["email"],
             "Insira o seu e-mail."),
            (
                re.match(
                    r"^[\w\.-]+@[\w\.-]+\.\w+$",
                    dados["email"]
                ) is None,
                "Insira um e-mail válido."
            ),
            (not dados["password"],
             "Insira a palavra-passe."),
        ]

        for condicao, mensagem in validacoes:
            if condicao:
                return mensagem
        return None