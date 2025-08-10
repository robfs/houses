import typing
from io import BytesIO

from PIL import Image as PILImage
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header
from textual_image.widget import Image

from utils import get_property_images_async
from widgets import IDS, HouseList

if typing.TYPE_CHECKING:
    from widgets import HouseList

__all__ = ["MainScreen"]


class MainContainer(Container):
    BORDER_TITLE = "Rightmove Properties"

    def compose(self) -> ComposeResult:
        lists = [HouseList(id=id) for id in IDS]
        yield Horizontal(Vertical(*lists), DetailContainer(id="detail-container"))


class DetailContainer(VerticalScroll):
    BORDER_TITLE = "Details"

    async def on_house_list_house_selection_changed(
        self, message: HouseList.HouseSelectionChanged
    ) -> None:
        self.remove_children()
        images = await get_property_images_async(message.property_number)
        for image in images:
            image_widget = Image(PILImage.open(BytesIO(image)))
            self.mount(image_widget)
            # image_widget.scroll_visible()


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield MainContainer()
        yield Footer()
        yield Header()
