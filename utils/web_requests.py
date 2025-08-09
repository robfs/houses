import asyncio
import re
from collections.abc import Generator
from typing import AsyncGenerator

import httpx
import orjson as json
import regex
import requests
from bs4 import BeautifulSoup

__all__ = ["get_property_models", "get_property_models_async"]


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


def rightmove_url(property_number: str) -> str:
    return f"https://www.rightmove.co.uk/properties/{property_number}"


def get_property_response(property_number: str) -> requests.Response:
    url = rightmove_url(property_number)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response


def extract_model_script(response: requests.Response | httpx.Response) -> str:
    soup = BeautifulSoup(response.text)
    pattern = re.compile(r"window\.(\w+)\s*=\s*\{")
    script = soup.find("script", string=pattern)
    if not script:
        return ""
    return script.get_text(strip=True)


def extract_models(script_text: str) -> dict[str, dict]:
    models = {}
    pattern = r"window\.(\w+)\s*=\s*(\{(?:[^{}]|(?2))*\})"
    for match in regex.finditer(pattern, script_text, regex.DOTALL):
        model_name = match.group(1)
        js_content = match.group(2)
        try:
            models[model_name] = json.loads(js_content)
        except json.JSONDecodeError as e:
            print(f"Failed to parse {model_name}: {e}")
    return models


def get_property_models(property_number: str) -> dict[str, dict]:
    response = get_property_response(property_number)
    script_text = extract_model_script(response)
    return extract_models(script_text)


async def get_property_images_async(urls: list[str]) -> AsyncGenerator[bytes]:
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url, headers=HEADERS) for url in urls]
        for task in asyncio.as_completed(tasks):
            response = await task
            yield response.content


async def get_property_response_async(property_number: str) -> httpx.Response:
    url = rightmove_url(property_number)
    async with httpx.AsyncClient() as client:
        return await client.get(url, headers=HEADERS)


async def get_property_models_async(property_number: str) -> dict[str, dict]:
    response = await get_property_response_async(property_number)
    script_text = extract_model_script(response)
    return extract_models(script_text)
