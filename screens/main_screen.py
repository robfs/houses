from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual_image.widget import Image

from widgets import IDS, HouseList

__all__ = ["MainScreen"]


class MainContainer(Container):
    BORDER_TITLE = "Rightmove Properties"

    def compose(self) -> ComposeResult:
        lists = [HouseList(id=id) for id in IDS]
        yield Horizontal(Vertical(*lists), DetailContainer())


class DetailContainer(Container):
    BORDER_TITLE = "Details"

    def compose(self) -> ComposeResult:
        yield Image()


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield MainContainer()
        yield Footer()
        yield Header()
