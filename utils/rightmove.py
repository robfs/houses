from urllib.parse import urlparse

import httpx
import orjson
import regex
import requests

__all__ = ["RightMove", "RightMoveFetcher", "RightMoveParser"]


def check_url_host_in(url: str, valid: set[str]) -> bool:
    host = urlparse(url).hostname
    if not host:
        raise ValueError(f"Could not detect host in url: {url}")
    return host in valid


class RightMove:
    @staticmethod
    def get_property_url(property_number: str) -> str:
        return f"https://www.rightmove.co.uk/properties/{property_number}"


class RightMoveFetcher:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }
    valid_hosts: set[str] = {"rightmove.co.uk", "www.rightmove.co.uk"}

    def supports_url(self, url: str) -> bool:
        return check_url_host_in(url.lower(), self.valid_hosts)

    def fetch(self, url: str) -> str:
        response = requests.get(url, headers=self.HEADERS)
        response.raise_for_status()
        return response.text

    async def fetch_async(self, url: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.HEADERS)
            return response.text


class RightMoveParser:
    _valid_hosts: set[str] = {"rightmove.co.uk", "www.rightmove.co.uk"}

    def supports_url(self, url: str) -> bool:
        return check_url_host_in(url, self._valid_hosts)

    def _get_page_model(self, content: str) -> str:
        pattern = r"window\.PAGE_MODEL\s*=\s*(\{(?:[^{}]|(?1))*\})"
        match_ = regex.search(pattern, content, regex.DOTALL)
        if not match_:
            raise ValueError("Couldn't locate page model.")
        return match_.group(1).strip()

    def parse(self, content: str) -> dict:
        script = self._get_page_model(content)
        return orjson.loads(script)


async def main():
    property_number = "163179074"
    site = RightMove()
    url = site.get_property_url(property_number)
    fetcher = RightMoveFetcher()
    content = await fetcher.fetch_async(url)
    parser = RightMoveParser()
    return parser.parse(content)


if __name__ == "__main__":
    import asyncio
    import pprint

    data = asyncio.run(main())
    pprint.pprint(data)
