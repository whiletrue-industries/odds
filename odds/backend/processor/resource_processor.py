import asyncio
from collections import Counter
import dataclasses
import tempfile
import httpx

import dataflows as DF
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from ...common.datatypes import Dataset, Resource, Field, DataCatalog
from ...common.store import store
from ...common.config import config
from ...common.realtime_status import realtime_status as rts


class ResourceProcessor:

    sem: asyncio.Semaphore = None

    ALLOWED_FORMATS = ['csv', 'xlsx', 'xls']
    MISSING_VALUES = ['None', 'NULL', 'N/A', 'NA', 'NAN', 'NaN', 'nan', '-']
    BIG_FILE_SIZE = 10000000

    @staticmethod
    def check_format(resource: Resource):
        if resource.file_format.lower() not in ResourceProcessor.ALLOWED_FORMATS:
            return None
        return resource
    
    @staticmethod
    def format_idx(resource: Resource):
        return ResourceProcessor.ALLOWED_FORMATS.index(resource.file_format.lower())

    def limiter(self):
        def func(rows):
            for i, row in enumerate(rows):
                if i < 10000:
                    yield row
        return func

    async def process(self, resource: Resource, dataset: Dataset, catalog: DataCatalog, ctx: str):
        if not ResourceProcessor.check_format(resource):
            return None
        if not resource.url:
            return None
        if not self.sem:
            self.sem = asyncio.Semaphore(self.concurrency_limit)
        resource.status_selected = True
        async with self.sem:
            with tempfile.TemporaryDirectory() as tmpdir:
                with open(tmpdir + '/stream.ndjson', 'w') as stream:
                    try:
                        rts.set(ctx, f'LOADING FROM URL {resource.url}')
                        suffix = resource.url.split('?')[0].split('.')[-1]
                        filename = tmpdir + '/data.' + suffix

                        with open(filename, 'wb') as f:
                            total_size = 0
                            async with httpx.AsyncClient() as client:
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0'
                                }
                                headers.update(catalog.http_headers)
                                async with client.stream('GET', resource.url, headers=headers, timeout=60, follow_redirects=True) as response:
                                    async for chunk in response.aiter_bytes():
                                        f.write(chunk)
                                        total_size += len(chunk)
                            
                        rts.set(ctx, f'DOWNLOADED for {total_size} BYTES from {resource.url} to {filename}')
                        dp, _ = DF.Flow(
                            DF.load(filename, override_schema={'missingValues': self.MISSING_VALUES}, deduplicate_headers=True),
                            DF.update_resource(-1, name='data'),
                            DF.validate(on_error=DF.schema_validator.clear),
                            DF.stream(stream)
                        ).process()
                        if total_size > self.BIG_FILE_SIZE:
                            rts.set(ctx, f'STREAMED BIG FILE {resource.url} TO {stream.name}')
                        resource.fields = [
                            Field(name=field['name'], data_type=field['type'])
                            for field in 
                            dp.resources[0].descriptor['schema']['fields']
                        ]

                        data = DF.Flow(
                            DF.unstream(stream.name),
                            self.limiter(),
                        ).results(on_error=None)[0][0]
                        if total_size > self.BIG_FILE_SIZE:
                            rts.set(ctx, f'READ BIG FILE DATA {resource.url} TO {len(data)} ROWS')

                        for field in resource.fields:
                            col_name = field.name
                            
                            values = [row[col_name] for row in data]
                            true_values = [x for x in values if x is not None]            
                            field.sample_values = [str(x) for x, _ in Counter(values).most_common(10)]
                            field.missing_values_percent = int(100 * (len(values) - len(true_values)) / len(values))
                            if field.data_type in ('number', 'integer', 'date', 'time', 'datetime'):
                                try:
                                    field.max_value = str(max(true_values))
                                    field.min_value = str(min(true_values))
                                except:
                                    pass
                        
                        stream.close()
                        sqlite_filename = tmpdir + '/db.sqlite'
                        sqlite_url = 'sqlite:///' + sqlite_filename
                        engine = create_engine(sqlite_url)
                        DF.Flow(
                            DF.unstream(stream.name),
                            DF.dump_to_sql({'data': {'resource-name': 'data'}}, engine=engine),
                        ).process()
                        if total_size > self.BIG_FILE_SIZE:
                            rts.set(ctx, f'DUMPED BIG FILE DATA {resource.url} TO {sqlite_filename}')
                        with engine.connect() as conn:
                            # row count:
                            resource.row_count = conn.execute(text('SELECT COUNT(*) FROM data')).fetchone()[0]
                            # get the table's CREATE TABLE text:
                            resource.db_schema = conn.execute(text('SELECT sql FROM sqlite_master WHERE type="table" AND name="data"')).fetchone()[0]
                            resource.status_loaded = True
                        if total_size > self.BIG_FILE_SIZE:
                            rts.set(ctx, f'SQLITE BIG FILE DATA {resource.url} HAS {resource.row_count} ROWS')
                        await store.storeDB(resource, dataset, sqlite_filename, ctx)
                        rts.clear(ctx)

                    except Exception as e:
                        rts.set(ctx, f'FAILED TO LOAD {resource.url}: {e}', 'error')
                        resource.loading_error = str(e)
                        return
        dataset.versions['resource_analyzer'] = config.feature_versions.resource_analyzer

    def set_concurrency_limit(self, concurrency_limit):
        self.concurrency_limit = concurrency_limit
        return self