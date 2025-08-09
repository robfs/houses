from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.message import Message
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual_image.widget import Image

from widgets import IDS, HouseList

__all__ = ["MainScreen"]


class MainContainer(Container):
    BORDER_TITLE = "Rightmove Properties"

    def compose(self) -> ComposeResult:
        lists = [HouseList(id=id) for id in IDS]
        yield Horizontal(Vertical(*lists), DetailContainer(id="detail-container"))


class DetailContainer(Container):
    BORDER_TITLE = "Details"

    def compose(self) -> ComposeResult:
        yield Image()

    def on_house_list_house_selection_chaged(self, message: Message) -> None:
        self.app.notify("Selected house changed")


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield MainContainer()
        yield Footer()
        yield Header()
