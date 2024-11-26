from typing import AsyncIterator
import httpx
from hashlib import sha256

from ....common.datatypes_website import WebsiteResource

from ....common.config import config, CACHE_DIR
from ....common.datatypes import Dataset, DataCatalog
from ....common.retry import Retry
from ....common.realtime_status import realtime_status as rts
from ..catalog_scanner import CatalogScanner


import asyncio
import json
from pathlib import Path
import httpx
from urllib.parse import urljoin
import re
import nh3
import bs4 

class AllowedAttributes():

    def __init__(self, url) -> None:
        self.links = set()
        self.url = url

    def __call__(self, tag, name, value):
        if tag in ('a', 'abbr', 'acronym'):
            if 'name' == 'title':
                return value
            if tag =='a' and name == 'href' and value:
                link = urljoin(self.url, value)
                self.links.add(link)
                return link
        return None

class Scraper:

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    WORKER_COUNT = 5
    PERIOD = 0.25
    CACHE = CACHE_DIR / 'web-scraper'
    WS = re.compile(r'\s+', re.UNICODE | re.MULTILINE)
    ALLOWED_TAGS = {'a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
            'em', 'i', 'li', 'ol', 'strong', 'ul', 'table', 'tr', 'td', 'th', 'tbody', 'thead', 'title'}
    CLEAN_TAGS = {'script', 'style', 'meta', 'iframe'}

    def __init__(self, base_urls) -> None:
        self.base_urls = base_urls
        self.q = asyncio.Queue()
        self.out_q = asyncio.Queue()
        self.outstanding = set()
        self.all_urls = set()
        self.all_hashes = set()
        self.CACHE.mkdir(parents=True, exist_ok=True)

    async def queue(self, url: str) -> None:
        if url not in self.all_urls:
            self.all_urls.add(url)
            # print('OS +', url, len(self.outstanding))
            self.outstanding.add(url)
            self.q.put_nowait(url)

    def mark_done(self, url: str) -> None:
        # print(f'OS - ({len(self.outstanding)}): {url}')
        self.outstanding.remove(url)
        if self.done():
            for i in range(self.WORKER_COUNT):
                self.q.put_nowait(None)
            self.out_q.put_nowait(None)

    def done(self) -> None:
        return len(self.outstanding) == 0

    async def scrape(self, url: str) -> list[str]:
        links = None
        content = None
        title = None
        final_url = None
        key = url.split('://')[1].replace('/', '_').replace(':', '_').replace('.', '_').replace('?', '_').replace('&', '_')
        cache_file = self.CACHE / f'{key}.json'
        cache_file_clean = self.CACHE / f'{key}.clean.html'
        if cache_file.exists():
            with open(cache_file) as file:
                data = json.load(file)
                content = data.get('content')
                content_type = data.get('content_type')
                final_url = data.get('final_url')
                print(f'GOT FROM CACHE: {url} -> {final_url}')

        if content is None:
            async with httpx.AsyncClient() as client:
                await asyncio.sleep(self.PERIOD * self.WORKER_COUNT)
                r = await client.get(url, follow_redirects=True, headers=self.headers, timeout=30)
                r.raise_for_status()
                # check content type to ensure it's html:
                content_type = r.headers.get('content-type', '').lower()
                if content_type.startswith('text/html'):
                    content = r.text
                final_url = str(r.url)
                with open(cache_file, 'w') as file:
                    json.dump({
                        'content': content,
                        'content_type': content_type,
                        'final_url': final_url
                    }, file)
                
        if not content or not content_type.startswith('text/html'):
            links = []
        if links is None:
            if final_url != url:
                if not any(final_url.startswith(base_url) for base_url in self.base_urls):
                    links = []
                else:
                    links = [final_url]
        # print(f'{url}: GOT STATUS', r.status_code)
        # use bs4 to get canonical link:
        if links is None:
            content_hash = sha256(content.encode()).hexdigest()
            if content_hash in self.all_hashes:
                links = []
            else:
                self.all_hashes.add(content_hash)
        if links is None:
            soup = bs4.BeautifulSoup(content, 'html.parser')
            canonical = soup.find('link', rel='canonical')
            if canonical:
                canonical = canonical.get('href')
                if not url.startswith(canonical):
                    links = [canonical]
            title = soup.find('title').text
        if links is None:
            allowed_attributes = AllowedAttributes(final_url)
            content = nh3.clean(
                content,
                tags=self.ALLOWED_TAGS,
                clean_content_tags=self.CLEAN_TAGS,
                attribute_filter=allowed_attributes,
                link_rel='',
                url_schemes={'http', 'https'},
            )
            content = self.WS.sub(' ', content)
            # print(f'{url}: CLEANED CONTENT', content)
            # print(f'{url}: LINKS', allowed_attributes.links)
            with open(cache_file_clean, 'w') as file:
                file.write(content)
            self.out_q.put_nowait(dict(
                key=key,
                title=title or key,
                url=url,
                local_path=str(cache_file_clean),
                content=content
            ))
            links = allowed_attributes.links

        _links = []
        for link in links:
            if any(link.startswith(base_url) for base_url in self.base_urls):
                link = link.split('#')[0]
                link = link.strip()
                _links.append(link)
        return _links

    async def worker(self, i: int) -> None:
        while not self.done():
            url = await self.q.get()
            if url is None:
                break
            # print(f'{url}: worker {i} starting (Q LEN {self.q.qsize()})')
            try:
                new_urls = await self.scrape(url)
            except Exception as e:
                print(f'{url} worker {i} error scraping: {e!r}')
                new_urls = []
            for new_url in new_urls:
                await self.queue(new_url)
            self.mark_done(url)

    async def __call__(self):
        for base_url in self.base_urls:
            await self.queue(base_url)
        async with asyncio.TaskGroup() as tg:
            for i in range(self.WORKER_COUNT):
                tg.create_task(self.worker(i))
            while True:
                try:
                    item = await self.out_q.get()
                    if item is None:
                        break
                    yield item
                except GeneratorExit:
                    break


class WebsiteCatalogScanner(CatalogScanner):

    def __init__(self, catalog: DataCatalog, ctx: str):
        self.catalog = catalog
        self.ctx = ctx

    def done(self, num_rows):
        if config.limit_catalog_datasets and num_rows >= config.limit_catalog_datasets:
            return True
        return False

    async def scan(self) -> AsyncIterator[Dataset]:
        bases = self.catalog.url
        if not isinstance(bases, list):
            bases = [bases]
        scraper = Scraper(bases)
        count = 0
        async for item in scraper():
            count += 1
            if config.debug and count % 100 == 0:
                rts.set(self.ctx, f"Got {count} pages from {self.catalog.id}")

            resources = [
                WebsiteResource(
                    item['local_path'], 'website', title='webpage contents', content=item['content']
                )
            ]

            dataset = Dataset(
                self.catalog.id, item['key'], item['title'],
                resources=resources,
                link=item['url']
            )
            yield dataset
            if self.done(count):
                break
