import httpx

from .config import config, CACHE_DIR
from .datatypes import Resource
from .retry import Retry
from .realtime_status import realtime_status as rts

from io import StringIO
import csv

TEMP_RESOURCE_DIR = CACHE_DIR / 'socrata-resource-temp'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0'
}


class SocrataResource(Resource):

    def __init__(self, *args, **kwargs) -> None:
        kwargs['kind'] = 'socrata'
        super().__init__(*args, **kwargs)

    async def get_openable_url(self, ctx: str) -> str:
        resource_url = self.url
        resource_id = resource_url.split('/')[-1].split('.')[0]

        TEMP_RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
        out_filename = TEMP_RESOURCE_DIR / f"{resource_id}.csv"
        if not out_filename.exists():
            if config.debug:
                rts.set(ctx, f"Caching socrata resource to {out_filename}")
            async with httpx.AsyncClient() as client:
                with open(out_filename, 'w') as f:
                    loaded = False
                    offset = 0
                    limit = 500
                    while not loaded:
                        get_url = f'{resource_url}?$limit={limit}&$offset={offset}'
                        r = await Retry()(client, 'get', get_url, headers=headers, timeout=240)
                        r.raise_for_status()
                        
                        chunk = StringIO()
                        async for text_chunk in r.aiter_text():
                            chunk.write(text_chunk)
                        chunk.seek(0)

                        reader = csv.reader(chunk)
                        writer = csv.writer(f)

                        line_count = 0
                        for i, row in enumerate(reader):
                            if i > 0 or offset == 0:
                                writer.writerow(row)
                            if i > 0:
                                line_count += 1

                        if config.debug and offset % 10000 == 0:
                            rts.set(ctx, f"Caching socrata resource {get_url}, offset {offset}, line count {line_count}")

                        if line_count <= 1:
                            loaded = True
                        offset += line_count        
        return str(out_filename)
