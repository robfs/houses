import typing

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive, var
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual_image.widget import Image

from widgets import IDS, HouseList

if typing.TYPE_CHECKING:
    from widgets import HouseList

__all__ = ["MainScreen"]


class MainContainer(Container):
    BORDER_TITLE = "Rightmove Properties"

    def compose(self) -> ComposeResult:
        lists = [HouseList(id=id) for id in IDS]
        yield Horizontal(
            Vertical(*lists, id="house-lists"),
            DetailContainer(Image(id="gallery-main"), id="detail-container"),
        )


class DetailContainer(VerticalScroll):
    BORDER_TITLE = "Details"
    main_image_index: reactive[int] = reactive(1, always_update=True)
    n_images: var[int] = var(0)


class MainScreen(Screen):
    BINDINGS = [("n", "next_image", "Next Image"), ("p", "prev_image", "Prev Image")]

    def compose(self) -> ComposeResult:
        yield MainContainer()
        yield Footer()
        yield Header()

    def action_next_image(self) -> None:
        container = self.query_one(DetailContainer)
        if container.main_image_index < container.n_images + 1:
            container.main_image_index += 1
        else:
            container.main_image_index = 1

    def action_prev_image(self) -> None:
        container = self.query_one(DetailContainer)
        if container.main_image_index == 1:
            container.main_image_index = container.n_images + 1
        else:
            container.main_image_index -= 1
