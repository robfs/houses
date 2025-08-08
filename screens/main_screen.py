"""Main app file."""

import json
import re
from urllib.request import urlopen

import regex
import requests
from bs4 import BeautifulSoup
from PIL import Image as PilImage
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label
from textual_image.widget import Image

from utils.json_store import JSONStore

__all__ = ["MainScreen"]


TO_REVIEW = "to-review"
TO_VIEW = "to-view"
VIEWED_YES = "viewed-yes"
VIEWED_NO = "viewed-no"


IDS = [TO_REVIEW, TO_VIEW, VIEWED_YES, VIEWED_NO]


class MoveScreen(ModalScreen[str]):
    DEFAULT_CSS = """
    MoveScreen {
            align: center middle;

            Container {
                border: $accent double;
                border-title-color: $accent;
                height: 5;
                width: 70;
                layout: grid;
                grid-size: 4 1;
                grid-gutter: 1;
                align: center middle;

                Label {
                    grid-columns: 1fr;
                    }
                }
            }
    """
    BINDINGS = [
        ("q", "dismiss", "Close"),
        ("v", "move_to_view", "To View"),
        ("r", "move_to_review", "To Review"),
        ("y", "move_to_yes", "Viewed Yes"),
        ("n", "move_to_no", "Viewed No"),
    ]

    def compose(self) -> ComposeResult:
        container = Container(
            Label("To Reivew (r)"),
            Label("To View (v)"),
            Label("Viewed - yes (y)"),
            Label("Viewed - No (n)"),
        )
        container.border_title = "Move to"
        yield container
        yield Footer()

    def action_move_to_view(self) -> None:
        self.dismiss(TO_VIEW)

    def action_move_to_review(self) -> None:
        self.dismiss(TO_REVIEW)

    def action_move_to_yes(self) -> None:
        self.dismiss(VIEWED_YES)

    def action_move_to_no(self) -> None:
        self.dismiss(VIEWED_NO)


class AddHouseScreen(ModalScreen[tuple[bool, list[str]]]):
    DEFAULT_CSS = """
    AddHouseScreen {
            align: center middle;

            Container {
                height: 10;
                width: 50;
                border: $accent double;
                border-title-color: $accent;
                align: center middle;
                }
            }
    """

    def compose(self) -> ComposeResult:
        input = Input(
            id="property-number",
            placeholder="Rightmove proerty number",
            value="163721768",
        )
        buttons = Horizontal(Button("Save", id="save"), Button("Cancel", id="cancel"))
        yield Container(input, buttons)

    def add_houses(self) -> tuple[bool, list[str]]:
        input_value = self.query_one("#property-number", Input).value
        property_numbers = input_value.split()
        return (True, property_numbers)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save":
            dismiss = self.add_houses()
            self.dismiss(dismiss)
        else:
            self.dismiss((False, []))


class DetailContainer(Container):
    DEFAULT_CSS = """
    DetailContainer {
        border: $accent round;
        border-title-color: $accent;
        border-title-background: $background;
        background: $surface;
    }
    """
    BORDER_TITLE = "Details"

    def compose(self) -> ComposeResult:
        yield Image()


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                HouseList(id=TO_REVIEW),
                HouseList(id=TO_VIEW),
                HouseList(id=VIEWED_YES),
                HouseList(id=VIEWED_NO),
            ),
            DetailContainer(),
        )
        yield Footer()
        yield Header()
