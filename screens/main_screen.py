import typing
from io import BytesIO
from itertools import cycle

from PIL import Image as PILImage
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive, var
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
        yield Horizontal(
            Vertical(*lists, id="house-lists"),
            DetailContainer(Image(id="gallery-main"), id="detail-container"),
        )


class DetailContainer(VerticalScroll):
    BORDER_TITLE = "Details"
    main_image_index: reactive[int] = reactive(1, always_update=True)
    n_images: var[int] = var(0)

    async def on_house_list_house_selection_changed(
        self, message: HouseList.HouseSelectionChanged
    ) -> None:
        if not message.property_number:
            return None
        self.app.notify("firing")
        self.remove_children(Horizontal)
        images = get_property_images_async(message.property_number)
        classes = cycle([("double", 2), ("triple", 3)])
        n = 0
        async for image in images:
            image_widget = Image(PILImage.open(BytesIO(image)))
            horizontals = self.query(Horizontal)
            if not horizontals:
                class_, n = next(classes)
                self.mount(Horizontal(image_widget, classes=class_))
                continue
            horizontal = horizontals.last()
            if len(horizontal.children) < n:
                horizontal.mount(image_widget)
            else:
                class_, n = next(classes)
                self.mount(Horizontal(image_widget, classes=class_))
            self.n_images += 1
        self.main_image_index = 1

    def watch_main_image_index(self, image_index: int) -> None:
        images = self.query(Image)
        if len(images) < 2:
            self.app.notify("FAILED!")
            return
        image = images[image_index]
        main_image = self.query_one("#gallery-main", Image)
        self.app.notify(f"{image.image}")
        main_image.image = image.image
        main_image.image


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
