
from pathlib import Path

from PIL import Image as PILImage

from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import Screen
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle


# Caminhos das imagens
PROJECT_DIR = Path(__file__).resolve().parent.parent
TREE_PATH = PROJECT_DIR / "extras" / "arvore.png"
LOGO_PATH = PROJECT_DIR / "extras" / "logofinal2.png"


# Proporções das imagens originais
LETTER_HEIGHT_RATIO = 178 / 234
TREE_T_HEIGHT_RATIO = 172 / 368
TREE_TRUNK_LEFT_RATIO = 81 / 279
LETTER_GAP_RATIO = 0.08
LOGO_BASELINE_RATIO = 56 / 234

# Cores da animação final
GREEN_COLOR = (0.51, 0.81, 0.54, 1)
WHITE_COLOR = (1, 1, 1, 1)

# Pausa entre o logótipo completo e os retângulos
RECTANGLES_DELAY = 0.4

# Duração das animações dos retângulos
GREEN_TRANSITION_DURATION = 0.30
WHITE_TRANSITION_DURATION = 0.30


class WhiteCover(Widget):
    """Retângulo branco que esconde a parte direita do logótipo."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(*WHITE_COLOR)
            self.rect = Rectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self.update_rect,
            size=self.update_rect
        )

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class ColorPanel(Widget):
    """Painel de cor utilizado na transição final."""

    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(*color)
            self.rect = Rectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self.update_rect,
            size=self.update_rect
        )

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size


class Splash(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.animation_started = False
        self.animation_finished = False
        self.transition_started = False

        # Fundo branco
        with self.canvas.before:
            Color(*WHITE_COLOR)
            self.background = Rectangle(
                pos=self.pos,
                size=self.size
            )

        self.bind(
            pos=self.update_background,
            size=self.update_background
        )

        # Preparar imagens sem margens transparentes
        self.tree_image_path = self.prepare_image(
            TREE_PATH, "tree"
        )
        self.logo_image_path = self.prepare_image(
            LOGO_PATH, "logo"
        )

        # Logótipo completo
        self.logo = Image(
            source=str(self.logo_image_path),
            size_hint=(None, None),
            fit_mode="contain",
            opacity=1
        )
        self.add_widget(self.logo)

        # Cobertura branca do t original
        self.cover = WhiteCover(
            size_hint=(None, None)
        )
        self.add_widget(self.cover)

        # Árvore com o t
        self.tree = Image(
            source=str(self.tree_image_path),
            size_hint=(None, None),
            fit_mode="contain",
            opacity=0
        )
        self.add_widget(self.tree)

        Clock.schedule_once(self.wait_for_layout, 0.3)

    def prepare_image(self, source, name):
        """Cria uma cópia da imagem sem margens transparentes."""

        if not source.is_file():
            raise FileNotFoundError(
                f"Não foi encontrada a imagem: {source}"
            )

        output_dir = PROJECT_DIR / "extras" / "splash_cache"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{name}_cropped.png"

        with PILImage.open(source) as original:
            image = original.convert("RGBA")
            bbox = image.getchannel("A").getbbox()

            if bbox:
                image = image.crop(bbox)

            image.save(output_path)

        return output_path

    def update_background(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size

    def update_cover(self, *args):
        """Cobre desde o tronco final do t até à margem direita."""

        if not hasattr(self, "final_tree_x"):
            return

        trunk_x = (
            self.final_tree_x
            + self.tree_width_final * TREE_TRUNK_LEFT_RATIO
        )

        self.cover.pos = (trunk_x, 0)
        self.cover.size = (
            max(0, self.width - trunk_x),
            self.height
        )

    def wait_for_layout(self, dt):
        if self.animation_started:
            return

        if self.width <= 100 or self.height <= 100:
            Clock.schedule_once(self.wait_for_layout, 0.2)
            return

        self.animation_started = True
        self.start_animation()

    def start_animation(self, *args):
        w, h = self.size

        if (
            not self.tree.texture
            or not self.logo.texture
            or self.tree.texture.height == 0
            or self.logo.texture.height == 0
        ):
            self.animation_started = False
            Clock.schedule_once(self.wait_for_layout, 0.2)
            return

        # Proporções das imagens
        self.tree_ratio = (
            self.tree.texture.width / self.tree.texture.height
        )
        self.logo_ratio = (
            self.logo.texture.width / self.logo.texture.height
        )

        # Dimensões iniciais da árvore
        self.tree_height_initial = min(
            h * 0.30,
            w * 0.35 / self.tree_ratio
        )
        self.tree_width_initial = (
            self.tree_height_initial * self.tree_ratio
        )

        # Dimensões finais do logótipo
        self.logo_height = min(
            h * 0.18,
            w * 0.78 / self.logo_ratio
        )
        self.logo_width = self.logo_height * self.logo_ratio

        # Altura visual das letras
        self.letter_height = (
            self.logo_height * LETTER_HEIGHT_RATIO
        )

        # Dimensões finais da árvore
        self.tree_height_final = (
            self.letter_height / TREE_T_HEIGHT_RATIO
        )
        self.tree_width_final = (
            self.tree_height_final * self.tree_ratio
        )

        # Limites para ecrãs pequenos
        scale = min(
            1.0,
            (h * 0.42) / self.tree_height_final,
            (w * 0.25) / self.tree_width_final
        )

        self.tree_height_final *= scale
        self.tree_width_final *= scale

        # Centro inicial da árvore
        self.initial_center = (w / 2, h / 2)

        self.tree.size = (
            self.tree_width_initial,
            self.tree_height_initial
        )
        self.tree.center = self.initial_center
        self.tree.opacity = 1

        # Calcular as posições finais
        gap = self.letter_height * LETTER_GAP_RATIO

        trunk_offset = (
            self.tree_width_final * TREE_TRUNK_LEFT_RATIO
        )

        total_width = (
            self.logo_width
            + gap
            + self.tree_width_final
            - trunk_offset
        )

        left = (w - total_width) / 2

        self.final_logo_x = left

        self.final_tree_x = (
            self.final_logo_x
            + self.logo_width
            + gap
            - trunk_offset
        )

        # Posição vertical final do logótipo
        final_tree_y = (
            h / 2 - self.tree_height_final / 2
        )

        self.final_logo_y = (
            final_tree_y
            - self.logo_height * LOGO_BASELINE_RATIO
        )

        # Logótipo com tamanho final desde o início
        self.logo.size = (
            self.logo_width,
            self.logo_height
        )
        self.logo.y = self.final_logo_y

        # Começa fora da área visível
        self.initial_logo_x = max(
            self.width,
            self.final_tree_x
        )
        self.logo.x = self.initial_logo_x
        self.logo.opacity = 1

        # Configurar a cobertura branca
        self.update_cover()

        # Ordem de desenho
        self.remove_widget(self.logo)
        self.remove_widget(self.cover)
        self.remove_widget(self.tree)

        self.add_widget(self.logo)
        self.add_widget(self.cover)
        self.add_widget(self.tree)

        # Pausa inicial
        Clock.schedule_once(self.next_animation_step, 0.5)

    def next_animation_step(self, dt):
        Clock.schedule_once(self.start_tree_resize, 0.75)

    def start_tree_resize(self, dt):
        animation = Animation(
            size=(
                self.tree_width_final,
                self.tree_height_final
            ),
            duration=0.25,
            t="out_cubic"
        )

        animation.bind(
            on_progress=self.keep_tree_centered
        )
        animation.bind(
            on_complete=self.start_logo_movement
        )

        animation.start(self.tree)

    def keep_tree_centered(self, *args):
        self.tree.center = self.initial_center
        self.update_cover()

    def start_logo_movement(self, *args):
        # Manter o tamanho e a altura finais do logótipo
        self.logo.y = self.final_logo_y

        # Árvore para a posição final
        tree_animation = Animation(
            x=self.final_tree_x,
            duration=0.5,
            t="out_cubic"
        )

        # Texto para a posição final
        logo_animation = Animation(
            x=self.final_logo_x,
            duration=0.5,
            t="out_cubic"
        )

        tree_animation.bind(
            on_progress=lambda *args: self.update_cover()
        )
        tree_animation.bind(
            on_complete=lambda *args: self.update_cover()
        )

        # Esperar antes de iniciar os retângulos
        logo_animation.bind(
            on_complete=self.wait_before_rectangles
        )

        tree_animation.start(self.tree)
        logo_animation.start(self.logo)

    def wait_before_rectangles(self, *args):
        """Pausa antes de iniciar a transição dos retângulos."""
        Clock.schedule_once(
            self.start_green_transition,
            RECTANGLES_DELAY
        )

    def start_green_transition(self, *args):
        """O painel verde sobe e cobre todo o ecrã."""

        if self.transition_started:
            return

        self.transition_started = True

        w, h = self.size

        self.green_panel = ColorPanel(
            color=GREEN_COLOR,
            size_hint=(None, None),
            size=(w, h),
            pos=(0, -h)
        )
        self.add_widget(self.green_panel)

        green_animation = Animation(
            y=0,
            duration=GREEN_TRANSITION_DURATION,
            t="out_cubic"
        )

        green_animation.bind(
            on_complete=self.start_white_transition
        )

        green_animation.start(self.green_panel)

    def start_white_transition(self, *args):
        """O painel branco sobe até cobrir todo o ecrã."""

        w, h = self.size

        self.white_panel = ColorPanel(
            color=WHITE_COLOR,
            size_hint=(None, None),
            size=(w, h),
            pos=(0, -h)
        )
        self.add_widget(self.white_panel)

        white_animation = Animation(
            y=0,
            duration=WHITE_TRANSITION_DURATION,
            t="out_cubic"
        )

        white_animation.bind(
            on_complete=self.finish_animation
        )

        white_animation.start(self.white_panel)

    def finish_animation(self, *args):
        """Termina a animação e abre o ecrã de login/registo."""

        self.animation_finished = True

        if (
            self.manager
            and "registerLogin" in self.manager.screen_names
        ):
            self.manager.current = "registerLogin"
