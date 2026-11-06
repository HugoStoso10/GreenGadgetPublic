#Bibliotecas
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from Animacoes import delayed, fade_in, slide_up
#Ficheiros
Builder.load_file("kv/register-login.kv")

class registerLogin(Screen):
    #Controlador de animação
    animacao_feita = False

    def on_enter(self):
        #Travão de animação
        if self.animacao_feita:
            return

        #Chamar todos os elementos para animação
        logo = self.ids.Logo
        texto = self.ids.Texto
        btn = self.ids.btn

        # Animações vão ser chamadas do ficheiro Animacoes.py
        delayed(lambda: fade_in(logo), 0)
        delayed(lambda: fade_in(texto), .3)
        delayed(lambda: [fade_in(btn), slide_up(btn)], 1)

        self.animacao_feita = True

    #Botão register mudar para janela para o registro
    def mudar_register(self):
        self.manager.current = "register"

    # Botão register mudar para janela para o login
    def mudar_login(self):
        self.manager.current = "login"