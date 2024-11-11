import asyncio
from collections import Counter
import httpx
import uuid
import os
import csv
csv.field_size_limit(10000000)

import dataflows as DF
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from ...common.datatypes import Dataset, Resource, Field, DataCatalog
from ...common.store import store
from ...common.config import config, CACHE_DIR
from ...common.realtime_status import realtime_status as rts


TMP_DIR = os.environ.get('RESOURCE_PROCESSOR_CACHE_DIR') or CACHE_DIR / 'resource-processor-temp'
try:
    TMP_DIR.mkdir(exist_ok=True, parents=True)
except:
    pass
TMP_DIR = str(TMP_DIR)

class ResourceProcessor:

    sem: asyncio.Semaphore = None

    ALLOWED_FORMATS = ['csv', 'xlsx', 'xls']
    MISSING_VALUES = ['None', 'NULL', 'N/A', 'NA', 'NAN', 'NaN', 'nan', '-']
    BIG_FILE_SIZE = 10000000
    MAX_FIELDS = 1000

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
                if i % 100000 == 0:
                    rts.set(ctx, message(i))
                yield row
        return func


    def validate_data(self, ctx, filename, stream):
        dp, _ = DF.Flow(
            DF.load(filename, override_schema={'missingValues': self.MISSING_VALUES}, deduplicate_headers=True, http_timeout=60),
            DF.update_resource(-1, name='data'),
            DF.validate(on_error=DF.schema_validator.clear),
            self.updater(ctx, lambda i: f'LOADED {i} ROWS TO DISK'),
            DF.stream(stream)
        ).process()
        rts.set(ctx, f'VALIDATED {filename} to {stream.name}')
        return dp

    def load_sample(self, ctx, stream_name):
        data = DF.Flow(
            DF.unstream(stream_name),
            self.limiter(),
        ).results(on_error=None)[0][0]
        rts.set(ctx, f'READ DATA {len(data)} ROWS from {stream_name}')
        return data
    
    def write_db(self, ctx, sqlite_filename, stream_name, data, resource, field_names):
        sqlite_url = f'sqlite:///{sqlite_filename}'
        engine = create_engine(sqlite_url)
        DF.Flow(
            DF.unstream(stream_name),
            DF.select_fields(field_names),
            self.updater(ctx, lambda i: f'DUMPED {i} ROWS TO SQLITE'),
            DF.dump_to_sql({'data': {'resource-name': 'data'}}, engine=engine),
        ).process()
        rts.set(ctx, f'DUMPED {len(data)} ROWS from {resource.url} TO {sqlite_filename}')
        with engine.connect() as conn:
            # row count:
            resource.row_count = conn.execute(text('SELECT COUNT(*) FROM data')).fetchone()[0]
            # get the table's CREATE TABLE text:
            resource.db_schema = conn.execute(text('SELECT sql FROM sqlite_master WHERE type="table" AND name="data"')).fetchone()[0]
            resource.status_loaded = True
        rts.set(ctx, f'SQLITE DATA {resource.url} HAS {resource.row_count} ROWS')
        return resource

    async def process(self, resource: Resource, dataset: Dataset, catalog: DataCatalog, ctx: str):
        if not ResourceProcessor.check_format(resource):
            return None
        if not resource.url:
            return None
        dataset.versions['resource_analyzer'] = config.feature_versions.resource_analyzer
        if resource.status_loaded and not resource.loading_error:
            resource.loading_error = None
            return None
        if resource.loading_error:
            if resource.loading_error.startswith('TOO MANY FIELDS'):
                past_num_fields = resource.loading_error.split('-')[-1]
                past_num_fields = int(past_num_fields)
                if past_num_fields > self.MAX_FIELDS:
                    return None
        resource.status_selected = True
        resource.loading_error = None
        resource.status_loaded = False
        to_delete = []
        if not self.sem:
            self.sem = asyncio.Semaphore(self.concurrency_limit)
        try:
            async with self.sem:
                rand = uuid.uuid4().hex
                with open(f'{TMP_DIR}/{rand}.ndjson', 'w') as stream:
                    to_delete.append(f'{TMP_DIR}/{rand}.ndjson')
                    try:
                        rts.set(ctx, f'LOADING FROM URL {resource.url}')
                        usable_url = await resource.get_openable_url(ctx)
                        if usable_url.startswith('http'):
                            suffix = usable_url.split('?')[0].split('.')[-1]
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
                                    report = 0
                                    async with client.stream('GET', resource.url, headers=headers, timeout=60, follow_redirects=True) as response:
                                        async for chunk in response.aiter_bytes():  
                                            f.write(chunk)
                                            total_size += len(chunk)
                                            while total_size - report > 1000000:
                                                report += 1000000
                                                rts.set(ctx, f'DOWNLOADED {report} BYTES from {resource.url} to {filename}')
                            
                            rts.set(ctx, f'DOWNLOADED {total_size} BYTES from {resource.url} to {filename}')
                        else:
                            filename = usable_url
                        dp = await asyncio.to_thread(self.validate_data, ctx, filename, stream)
                        potential_fields = [
                            Field(name=field['name'], data_type=field['type'])
                            for field in 
                            dp.resources[0].descriptor['schema']['fields']
                        ]

                        data = await asyncio.to_thread(self.load_sample, ctx, stream.name)

                        if len(data) == 0:
                            resource.loading_error = 'NO DATA'
                            rts.set(ctx, f'NO DATA {resource.url}')
                            return

                        resource.fields = []
                        field_names = []
                        for field in potential_fields:
                            col_name = field.name
                            
                            values = [row[col_name] for row in data]
                            true_values = [x for x in values if x is not None]
                            if len(true_values) == 0:
                                continue
                            resource.fields.append(field)
                            try:
                                field.sample_values = [str(x) for x, _ in Counter(true_values).most_common(10)]
                                field.sample_values = [x for x in field.sample_values if len(x) < 100]
                                if len(field.sample_values) == 1:
                                    # if all values are the same, no need for this field in the db
                                    continue
                            except:
                                pass
                            field_names.append(col_name)
                            if len(values) > 0 and len(true_values) != len(values):
                                field.missing_values_percent = int(100 * (len(values) - len(true_values)) / len(values))
                            if field.data_type in ('number', 'integer', 'date', 'time', 'datetime'):
                                true_values = set(true_values)
                                try:
                                    field.max_value = str(max(true_values))
                                    field.min_value = str(min(true_values))
                                except:
                                    pass                    
                        if len(field_names) > self.MAX_FIELDS:
                            resource.loading_error = f'TOO MANY FIELDS - {len(field_names)}'
                            rts.set(ctx, f'SKIPPING {resource.url} TOO MANY FIELDS')
                            return

                        stream.close()

                        sqlite_filename = f'{TMP_DIR}/{rand}.sqlite'
                        resource = await asyncio.to_thread(self.write_db, ctx, sqlite_filename, stream.name, data, resource, field_names)
                        deleted = await store.storeDB(resource, dataset, sqlite_filename, ctx)
                        if not deleted:
                            to_delete.append(sqlite_filename)

                    except Exception as e:
                        rts.set(ctx, f'FAILED TO LOAD {resource.url}: {e}', 'error')
                        resource.loading_error = str(e)
                        return
                    finally:
                        rts.clear(ctx)

        finally:
            for filename in to_delete:
                try:
                    os.unlink(filename)
                except Exception as e:
                    rts.set(ctx, f'FAILED TO DELETE {filename}: {e}', 'error')

    def set_concurrency_limit(self, concurrency_limit):
        self.concurrency_limit = concurrency_limit
        return self