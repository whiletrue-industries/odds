import asyncio
from collections import Counter
import httpx
import uuid
import os

import dataflows as DF
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from ...common.datatypes import Dataset, Resource, Field, DataCatalog
from ...common.store import store
from ...common.config import config, CACHE_DIR
from ...common.realtime_status import realtime_status as rts


TMP_DIR = CACHE_DIR / 'resource-processor-temp'
TMP_DIR.mkdir(exist_ok=True, parents=True)
TMP_DIR = str(TMP_DIR)

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

    def updater(self, ctx, message):
        def func(rows):
            for i, row in enumerate(rows):
                if i % 1000 == 0:
                    rts.set(ctx, message(i))
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
        to_delete = []
        try:
            async with self.sem:
                rand = uuid.uuid4().hex
                with open(f'{TMP_DIR}/{rand}.ndjson', 'w') as stream:
                    to_delete.append(f'{TMP_DIR}/{rand}.ndjson')
                    try:
                        rts.set(ctx, f'LOADING FROM URL {resource.url}')
                        suffix = resource.url.split('?')[0].split('.')[-1]
                        suffix = suffix.replace('/', '.')
                        filename = f'{TMP_DIR}/{rand}.{suffix}'

                        with open(filename, 'wb') as f:
                            to_delete.append(filename)
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
                            
                        rts.set(ctx, f'DOWNLOADED {total_size} BYTES from {resource.url} to {filename}')
                        dp, _ = DF.Flow(
                            DF.load(filename, override_schema={'missingValues': self.MISSING_VALUES}, deduplicate_headers=True),
                            DF.update_resource(-1, name='data'),
                            DF.validate(on_error=DF.schema_validator.clear),
                            self.updater(ctx, lambda i: f'LOADED {i} ROWS TO DISK'),
                            DF.stream(stream)
                        ).process()
                        rts.set(ctx, f'VALIDATED {total_size} BYTES from {resource.url} to {stream.name}')
                        potential_fields = [
                            Field(name=field['name'], data_type=field['type'])
                            for field in 
                            dp.resources[0].descriptor['schema']['fields']
                        ]

                        data = DF.Flow(
                            DF.unstream(stream.name),
                            self.limiter(),
                        ).results(on_error=None)[0][0]
                        rts.set(ctx, f'READ DATA {total_size} BYTES / {len(data)} ROWS from {resource.url}')

                        if len(data) == 0:
                            resource.loading_error = 'NO DATA'
                            rts.set(ctx, f'NO DATA {resource.url}')
                            return

                        resource.fields = []
                        for field in potential_fields:
                            col_name = field.name
                            
                            values = [row[col_name] for row in data]
                            true_values = [x for x in values if x is not None]
                            if len(true_values) == 0:
                                continue
                            resource.fields.append(field)
                            try:
                                field.sample_values = [str(x) for x, _ in Counter(values).most_common(10)]
                            except:
                                pass
                            if len(values) > 0:
                                field.missing_values_percent = int(100 * (len(values) - len(true_values)) / len(values))
                            if field.data_type in ('number', 'integer', 'date', 'time', 'datetime'):
                                try:
                                    field.max_value = str(max(true_values))
                                    field.min_value = str(min(true_values))
                                except:
                                    pass                    
                        if len(resource.fields) > 50:
                            resource.loading_error = f'TOO MANY FIELDS - {len(resource.fields)}'
                            rts.set(ctx, f'SKIPPING {resource.url} TOO MANY FIELDS')
                            return

                        stream.close()
                        sqlite_filename = f'{TMP_DIR}/{rand}.sqlite'
                        to_delete.append(sqlite_filename)
                        sqlite_url = f'sqlite:///{sqlite_filename}'
                        engine = create_engine(sqlite_url)
                        DF.Flow(
                            DF.unstream(stream.name),
                            self.updater(ctx, lambda i: f'DUMPED {i} ROWS TO SQLITE'),
                            DF.dump_to_sql({'data': {'resource-name': 'data'}}, engine=engine),
                        ).process()
                        rts.set(ctx, f'DUMPED {total_size} BYTES / {len(data)} ROWS from {resource.url} TO {sqlite_filename}')
                        with engine.connect() as conn:
                            # row count:
                            resource.row_count = conn.execute(text('SELECT COUNT(*) FROM data')).fetchone()[0]
                            # get the table's CREATE TABLE text:
                            resource.db_schema = conn.execute(text('SELECT sql FROM sqlite_master WHERE type="table" AND name="data"')).fetchone()[0]
                            resource.status_loaded = True
                        rts.set(ctx, f'SQLITE DATA {resource.url} HAS {resource.row_count} ROWS == {len(data)} ROWS')
                        await store.storeDB(resource, dataset, sqlite_filename, ctx)
                        rts.clear(ctx)

                    except Exception as e:
                        rts.set(ctx, f'FAILED TO LOAD {resource.url}: {e}', 'error')
                        resource.loading_error = str(e)
                        return
            dataset.versions['resource_analyzer'] = config.feature_versions.resource_analyzer
        finally:
            for filename in to_delete:
                try:
                    os.unlink(filename)
                except Exception as e:
                    rts.set(ctx, f'FAILED TO DELETE {filename}: {e}', 'error')

    def set_concurrency_limit(self, concurrency_limit):
        self.concurrency_limit = concurrency_limit
        return self