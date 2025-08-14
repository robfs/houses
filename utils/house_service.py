from collections.abc import Sequence

from protocols import (
    Property,
    PropertyFetcher,
    PropertyParser,
    PropertySite,
    PropertyStore,
)

__all__ = ["HouseService"]


class HouseService:
    def __init__(
        self,
        sites: Sequence[PropertySite],
        fetchers: Sequence[PropertyFetcher],
        parsers: Sequence[PropertyParser],
        stores: Sequence[PropertyStore],
    ) -> None:
        self.sites: Sequence[PropertySite] = sites
        self.fetchers: Sequence[PropertyFetcher] = fetchers
        self.parsers: Sequence[PropertyParser] = parsers
        self.stores: Sequence[PropertyStore] = stores

    def get_property(self, site_name: str, property_id: str) -> Property:
        data = self.get_property_from_store(site_name, property_id)
        if data is not None:
            return data
        return self.get_property_from_url(site_name, property_id)

    def get_property_from_store(
        self, site_name: str, property_id: str
    ) -> Property | None:
        site = self.get_site(site_name)
        url = site.get_property_url(property_id)
        store = self.get_store(url)
        return store.get(url)

    def add_property(self, site_name: str, property_id: str, status: str) -> Property:
        # [TODO] enable save from property object. store url on property object
        property = self.get_property_from_url(site_name, property_id)

    def save_property(self, url: str, property: Property, status: str) -> str:
        store = self.get_store(url)
        return store.set(url, property, status)

    def get_property_from_url(self, site_name: str, property_id: str) -> Property:
        site = self.get_site(site_name)
        url = site.get_property_url(property_id)
        fetcher = self.get_fetcher(url)
        parser = self.get_parser(url)
        content = fetcher.fetch(url)
        property = parser.parse(content)
        return property

    def get_site(self, site_name: str) -> PropertySite:
        for site in self.sites:
            if site.name() == site_name:
                return site
        raise ValueError(f"No site available for: {site_name}")

    def get_fetcher(self, url: str) -> PropertyFetcher:
        for fetcher in self.fetchers:
            if fetcher.supports_url(url):
                return fetcher
        raise ValueError(f"No fetcher available for url: {url}")

    def get_parser(self, url: str) -> PropertyParser:
        for parser in self.parsers:
            if parser.supports_url(url):
                return parser
        raise ValueError(f"No parser available for url: {url}")

    def get_store(self, url: str) -> PropertyStore:
        for store in self.stores:
            if store.supports_url(url):
                return store
        raise ValueError(f"No store available for url: {url}")


if __name__ == "__main__":
    from utils import RightMove, RightMoveFetcher, RightMoveParser, RightMoveStore

    property_number = "163179074"
    site_name = "rightmove"

    sites = [RightMove()]
    fetchers = [RightMoveFetcher()]
    parsers = [RightMoveParser()]
    stores = [RightMoveStore("houses_test.db")]
    service = HouseService(sites, fetchers, parsers, stores)
