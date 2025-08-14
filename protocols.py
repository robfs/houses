from collections.abc import Sequence
from typing import Protocol

__all__ = [
    "Property",
    "PropertyFetcher",
    "PropertySite",
    "PropertyParser",
    "PropertyService",
    "PropertyStore",
]


class Property(Protocol):
    data: dict
    status: str | None

    def __init__(self, data: dict, status: str | None = None) -> None: ...
    @staticmethod
    def supports_url(url: str) -> bool: ...


class PropertySite(Protocol):
    def name(self) -> str: ...
    def get_property_url(self, property_id: str) -> str: ...
    def get_property_constructor(self) -> type[Property]: ...


class PropertyFetcher(Protocol):
    def supports_url(self, url: str) -> bool: ...
    def fetch(self, url: str) -> str: ...
    async def fetch_async(self, url: str) -> str: ...


class PropertyParser(Protocol):
    def supports_url(self, url: str) -> bool: ...
    def parse(self, content: str) -> Property: ...


class PropertyStore(Protocol):
    def get_property_constructor(self) -> type[Property]: ...
    def set(self, url: str, property: Property, status: str | None = None) -> str: ...
    def get(self, url: str) -> Property | None: ...
    def delete(self, url: str) -> str: ...
    def update(self, url: str, *args, **kwargs) -> str: ...
    def supports_url(self, url: str) -> bool: ...


class PropertyService(Protocol):
    sites: Sequence[PropertySite]
    fetchers: Sequence[PropertyFetcher]
    parsers: Sequence[PropertyParser]
    stores: Sequence[PropertyStore]

    def __init__(
        self,
        sites: Sequence[PropertySite],
        fetchers: Sequence[PropertyFetcher],
        parsers: Sequence[PropertyParser],
        stores: Sequence[PropertyStore],
    ) -> None: ...
    def get_property(self, site_name: str, property_id: str) -> Property: ...
    def add_property(
        self, site_name: str, property_id: str, status: str
    ) -> Property: ...
