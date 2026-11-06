# ---------------------------------------------------------------------------------
#   FICHEIRO MAIN - Serve como gestor da app que organiza e liga as várias janelas
#
#   BILBIOTECAS USADAS: kivy; kivyMD; ffpyplayer; Re;
#
#-----------------------------------------------------------------------------------------------------------------------

#Bibliotecas
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.config import Config
from kivy.core.window import Window

#Ficheiros
from Screens.Splash import Splash
from Screens.registerLogin import registerLogin
from Screens.register import register
from Screens.login import login
from Screens.home import home
from Screens.add_device import add_device
from Screens.device import device
from Screens.add_watering import add_watering
from Screens.enciclopedia import enciclopedia


#Classe vai iniciar a app e abrir como primeira janela o splash
#Tambem declara todas as janelas da app
class MainApp(MDApp):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(Splash(name="splash"))
        sm.add_widget(registerLogin(name="registerLogin"))
        sm.add_widget(register(name="register"))
        sm.add_widget(login(name="login"))
        sm.add_widget(home(name="home"))
        sm.add_widget(add_device(name="add_device"))
        sm.add_widget(device(name="device"))
        sm.add_widget(add_watering(name="add_watering"))
        sm.add_widget(enciclopedia(name="enciclopedia"))
        sm.current = "splash"
        return sm
if __name__ == "__main__":
    MainApp().run()
