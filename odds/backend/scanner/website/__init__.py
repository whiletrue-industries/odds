import asyncio
import json
from pathlib import Path
import httpx
# import bleach
from urllib.parse import urljoin
import re
import nh3
import bs4 

CACHE_DIR = Path('.caches/web-scraper')
CACHE_DIR.mkdir(parents=True, exist_ok=True)

WS = re.compile(r'\s+', re.UNICODE | re.MULTILINE)
ALLOWED_TAGS = {'a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
        'em', 'i', 'li', 'ol', 'strong', 'ul', 'table', 'tr', 'td', 'th', 'tbody', 'thead', 'title'}
CLEAN_TAGS = {'script', 'style', 'meta', 'iframe'}
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
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0'
    }
    WORKER_COUNT = 5

    def __init__(self, base_urls) -> None:
        self.base_urls = base_urls
        self.q = asyncio.Queue()
        self.out_q = asyncio.Queue()
        self.outstanding = set()
        self.all_urls = set()

    def queue(self, url: str) -> None:
        if url not in self.all_urls:
            self.all_urls.add(url)
            self.outstanding.add(url)
            self.q.put_nowait(url)

    def mark_done(self, url: str) -> None:
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
        key = url.replace('/', '_').replace(':', '_').replace('.', '_')
        cache_file = CACHE_DIR / f'{key}.json'
        if cache_file.exists():
            with open(cache_file) as file:
                data = json.load(file)
                content = data.get('content')
                content_type = data.get('content_type')
                final_url = data.get('final_url')

        if content is None:
            async with httpx.AsyncClient(headers=self.headers, timeout=30) as client:
                await asyncio.sleep(self.WORKER_COUNT / 4)
                r = await client.get(url, follow_redirects=True)
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
                
        if not content_type.startswith('text/html'):
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
            soup = bs4.BeautifulSoup(content, 'html.parser')
            canonical = soup.find('link', rel='canonical')
            if canonical:
                canonical = canonical.get('href')
                if not url.startswith(canonical):
                    links = [canonical]
        if links is None:
            allowed_attributes = AllowedAttributes(final_url)
            content = nh3.clean(
                content,
                tags=ALLOWED_TAGS,
                clean_content_tags=CLEAN_TAGS,
                attribute_filter=allowed_attributes,
                link_rel='',
                url_schemes={'http', 'https'},
            )
            content = WS.sub(' ', content)
            processed = True
            # print(f'{url}: CLEANED CONTENT', content)
            # print(f'{url}: LINKS', allowed_attributes.links)
            self.out_q.put_nowait(dict(
                url=url,
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
                self.queue(new_url)
            self.mark_done(url)

    async def __call__(self):
        for base_url in self.base_urls:
            self.queue(base_url)
        async with asyncio.TaskGroup() as tg:
            for i in range(self.WORKER_COUNT):
                tg.create_task(self.worker(i))
            while True:
                item = await self.out_q.get()
                if item is None:
                    break
                yield item

async def main(bases):
    scraper = Scraper(bases)
    count = 0
    async for item in scraper():
        count += 1
        print(f'GOT ITEM {count}: {item['url']}, {len(item['content'])} chars, #Q {scraper.q.qsize()}')

if __name__ == '__main__':
    asyncio.run(main(['https://www.camden.gov.uk/', 'https://democracy.camden.gov.uk/']))