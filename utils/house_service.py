from collections.abc import Sequence

from protocols import PropertyFetcher, PropertyParser, PropertySite, PropertyStore

__all__ = ["HouseService"]


class HouseService:
    def __init__(
        self,
        site: PropertySite,
        fetchers: Sequence[PropertyFetcher],
        parsers: Sequence[PropertyParser],
        stores: Sequence[PropertyStore],
    ) -> None:
        self.site: PropertySite = site
        self.fetchers: Sequence[PropertyFetcher] = fetchers
        self.parsers: Sequence[PropertyParser] = parsers
        self.stores: Sequence[PropertyStore] = stores

    def get_property_data(self, property_id: str) -> dict:
        url = self.site.get_property_url(property_id)
        store = self.get_store(url)
        data = store.get(url)
        if data:
            return data
        fetcher = self.get_fetcher(url)
        parser = self.get_parser(url)
        content = fetcher.fetch(url)
        data = parser.parse(content)
        store.set(url, data)
        return data

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
