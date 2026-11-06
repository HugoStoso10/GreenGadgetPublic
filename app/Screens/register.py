#Bibliotecas
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from Animacoes import delayed, fade_in, slide_right
import re, requests
#Ficheiros
Builder.load_file("kv/register.kv")

#url da api (mudar quando o servidor estiver funcional)
API_URL = "http://85.242.41.127:8000"

class register(Screen):
    # Controlador de animação
    animacao_feita = False

    def on_enter(self):
        # Travão de animação
        if self.animacao_feita:
            return

        logo = self.ids.Logo
        texto = self.ids.Text
        nome = self.ids.TextFieldNome
        email = self.ids.TextFieldEmail
        pass1 = self.ids.TextFieldPassword
        pass2 = self.ids.TextFieldPassword2
        btn = self.ids.btn
        btn2 = self.ids.Verpass

        # Animações
        delayed(lambda: fade_in(logo), 0)
        delayed(lambda: fade_in(texto), .3)
        delayed(lambda: [fade_in(nome), slide_right(nome)],0.6)
        delayed(lambda: [fade_in(email), slide_right(email)], 0.9)
        delayed(lambda: [fade_in(pass1), slide_right(pass1)], 1)
        delayed(lambda: [fade_in(pass2), slide_right(pass2)], 1.2)
        delayed(lambda : fade_in(btn2), 1.5)
        delayed(lambda: fade_in(btn), 1.8)

        # Definir que as animações já foram executadas e não as volta a executar se voltar a janela
        self.animacao_feita = True


    #Função para retornar de janela
    def voltar(self):
        self.manager.current = "registerLogin"

    #Função para mostrar/esconder o conteudo no campo de password
    def toggle_password(self):
        pass1 = self.ids.TextFieldPassword
        pass2 = self.ids.TextFieldPassword2
        btn = self.ids.Verpass

        x = not pass1.password
        pass1.password = x
        pass2.password = x


        if x:
            btn.icon = "eye-off"
            btn.text = "Ver palavra passe"
        else:
            btn.icon = "eye"
            btn.text = "Esconder palavra passe"

    # Função que faz o controlo da criação de conta
    def criar_conta(self):
        dados = self.get_form_data()
        erro = self.validar_registo(dados)

        # Erros da app
        if erro:
            self.ids.erro_texto.text_color = (1, 0, 0, 1)
            self.ids.erro_texto.text = erro
            return

        # Enviar dados para a API
        try:
            resposta = requests.post(
                f"{API_URL}/register",
                json={
                    "name": dados["nome"],
                    "email": dados["email"],
                    "password": dados["password"]
                },
                timeout=5
            )

            resultado = resposta.json()

            # Conta criada com sucesso
            if resultado["success"]:
                self.ids.erro_texto.text_color = (0.49, 0.77, 0.50, 1)
                self.ids.erro_texto.text = resultado["message"]

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
            "nome": self.ids.TextFieldNome.text.strip(),
            "email": self.ids.TextFieldEmail.text.strip(),
            "password": self.ids.TextFieldPassword.text,
            "password2": self.ids.TextFieldPassword2.text,
        }

    def validar_registo(self, dados):
        validacoes = [
            (not dados["nome"], "Insira o seu nome."),
            (not dados["email"], "Insira o seu e-mail."),
            (
                re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", dados["email"]) is None,
                "Insira um e-mail válido."
            ),
            (not dados["password"], "Insira a palavra-passe."),
            (not dados["password2"], "Tem que confirmar a palavra-pass."),
            (len(dados["password"]) < 8, "A palavra-passe deve ter pelo menos 8 caracteres."),
            (dados["password"] != dados["password2"], "As palavras-passe não coincidem."),
        ]

        for condicao, mensagem in validacoes:
            if condicao:
                return mensagem

        return None