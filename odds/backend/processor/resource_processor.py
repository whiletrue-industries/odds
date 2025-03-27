import asyncio
import base64
from collections import Counter
from typing import Any, List
import httpx
import uuid
import os
import csv
import bs4


csv.field_size_limit(10000000)

import dataflows as DF
from sqlalchemy import create_engine
from sqlalchemy.sql import text

from ...common.datatypes import Dataset, Resource, Field, DataCatalog
from ...common.datatypes_website import WebsiteResource
from ...common.store import store
from ...common.config import config, CACHE_DIR
from ...common.realtime_status import realtime_status as rts
from ...common.llm import llm_runner
from ...common.llm.llm_query import LLMQuery
from ..settings import ALLOWED_FORMATS, DOCUMENT_FORMATS, DOCUMENT_MIMETYPES


TMP_DIR = os.environ.get('RESOURCE_PROCESSOR_CACHE_DIR') or CACHE_DIR / 'resource-processor-temp'
try:
    TMP_DIR.mkdir(exist_ok=True, parents=True)
except:
    pass
TMP_DIR = str(TMP_DIR)

TIMEOUT_VALIDATE = 600
TIMEOUT_DOWNLOAD = 600
TIMEOUT_DB = 600

class MDConverterQuery(LLMQuery):

    WEBSITE_PROMPT = """Please read the contents of the following website (in simplified HTML format) and assess the data.
If it contains information relevant to users, do your best to extract the textual data contained in the website into markdown format, as accurately as possible.
If the website contains tables, lists, or other structured data, please try to extract that data into a tabular format.
It doesn't have to be perfect, but try to capture the essence of the data as best as you can and format it in a way that would be useful, without modifying the text itself.
Finally, if it doesn't contain any relevant information (for example, it is only a directory page linking to other pages, login page, a search page, a blank page etc.), simply answer with the single word "IRRELEVANT" and nothing more.
Remember, you must output ONLY a markdown-formatted text __or__ the ONLY word "IRRELEVANT" as the final result. Do not include any other preamble or postamble text in your response. Reply in {language}.
----------"""

    DATA_URI_PROMPT = """Please read the contents of the following document (attached) and assess the data.
If it contains information relevant to users, do your best to extract the textual data contained in the document into markdown format, as accurately as possible.
If the document contains tables, lists, or other structured data, please try to extract that data into a tabular format.
If the document is very large, you can skip some parts of it, but please try to keep the most relevant information or summarize it in a way that is useful.
It doesn't have to be perfect, but try to capture the essence of the data as best as you can and format it in a way that would be useful, without modifying the text itself.
Finally, if it doesn't contain any relevant information (for example, it is only a cover letter describing other documents, a blank page etc.), simply answer with the single word "IRRELEVANT" and nothing more.
Remember, you must output ONLY a markdown-formatted text __or__ the ONLY word "IRRELEVANT" as the final result. Do not include any other preamble or postamble text in your response. Reply in {language}.
"""

    def __init__(self, catalog: DataCatalog, resource: Resource, data_b64: str = None):
        super().__init__(None, catalog)
        self.resource = resource
        self.data_b64 = data_b64
        self.language = self.catalog.language or 'English'

    def model(self) -> str:
        return 'cheap'

    def temperature(self) -> float:
        return 0
    
    # def prepare_content(self, content):
    #     soup = bs4.BeautifulSoup(content, 'html.parser')
    #     for comment in soup.find_all(text=lambda text: isinstance(text, bs4.Comment)):
    #         comment.extract()
    #     for tag in soup.find_all('img'):
    #         if tag.get('src', '').startswith('data:'):
    #             tag.decompose()
    #     return str(soup)


    def prompt(self) -> list[tuple[str, str]]:
        if self.data_b64:
            prompt = [
                { "type": "text", "text": self.DATA_URI_PROMPT.format(language=self.language) },
                {
                    'type': 'file',
                    'file': {
                        'filename': self.resource.url.split('/')[-1],
                        'file_id': self.resource.id,
                        'file_data': self.data_b64,
                    }
                }
            ]
        else:
            prompt = self.WEBSITE_PROMPT.format(language=self.language)
            content = self.resource.content
            # content = self.prepare_content(content)
            prompt += content
            prompt = prompt[:int(self.max_tokens()*0.75)]

        # print("XXXXX", self.resource.content)

        return [
            ('system', 'You are an experienced data analyst and web developer.'),
            ('user', prompt)
        ]

    def handle_result(self, result: str) -> Any:
        if result.strip().upper() == 'IRRELEVANT' or 'IRRELEVANT' in result:
            self.resource.status = 'irrelevant'
            self.resource.loading_error = 'IRRELEVANT'
            self.resource.status_loaded = False
        else:
            self.resource.status = 'loaded'
            self.resource.content = result
            self.resource.status_loaded = True

    def expects_json(self) -> bool:
        return False

    def max_tokens(self) -> int:
        return 20480


class ResourceProcessor:

    sem: asyncio.Semaphore = None

    MISSING_VALUES = ['None', 'NULL', 'N/A', 'NA', 'NAN', 'NaN', 'nan', '-']
    BIG_FILE_SIZE = 10000000
    MAX_FIELDS = 1000

    @staticmethod
    def check_format(resource: Resource):
        if resource.file_format.lower() not in ALLOWED_FORMATS:
            return None
        return resource
    
    @staticmethod
    def format_idx(resource: Resource):
        return ALLOWED_FORMATS.index(resource.file_format.lower())

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
            DF.load(filename, 
                    override_schema={'missingValues': self.MISSING_VALUES},
                    deduplicate_headers=True,
                    deduplicate_headers_case_sensitive=False,
                    deduplicate_headers_format='__%s',
                    http_timeout=60
            ),
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
            resource.status = 'loaded'
            resource.status_loaded = True
        rts.set(ctx, f'SQLITE DATA {resource.url} HAS {resource.row_count} ROWS')
        return resource
    
    async def process_tabular(self, catalog: DataCatalog, dataset: Dataset, resource: Resource, to_delete: List[str], ctx: str):
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
                            async with asyncio.timeout(TIMEOUT_DOWNLOAD):
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
                async with asyncio.timeout(TIMEOUT_VALIDATE):
                    dp = await asyncio.to_thread(self.validate_data, ctx, filename, stream)
                potential_fields = [
                    Field(name=field['name'], data_type=field['type'])
                    for field in 
                    dp.resources[0].descriptor['schema']['fields']
                ]
                existing_fields = dict((f.name, f) for f in resource.fields or [])
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
                    if col_name in existing_fields:
                        field.title = existing_fields[col_name].title
                        field.description = existing_fields[col_name].description

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
                async with asyncio.timeout(TIMEOUT_DB):
                    resource = await asyncio.to_thread(self.write_db, ctx, sqlite_filename, stream.name, data, resource, field_names)
                    deleted = await store.storeDB(resource, dataset, sqlite_filename, ctx)
                if not deleted:
                    to_delete.append(sqlite_filename)

            except Exception as e:
                rts.set(ctx, f'FAILED TO LOAD {resource.url}: {e}', 'error')
                resource.status = 'failed'
                resource.loading_error = str(e)
                return
            finally:
                rts.clear(ctx)

    async def process_website(self, catalog: DataCatalog, dataset: Dataset, resource: WebsiteResource, to_delete: List[str], ctx: str):
        resource.content = open(resource.url, 'r').read()
        query = MDConverterQuery(catalog, resource)
        await llm_runner.run(query, [dataset.id])

        rts.clear(ctx)

    async def process_document(self, catalog: DataCatalog, dataset: Dataset, resource: Resource, to_delete: List[str], ctx: str):
        content = open(resource.url, 'rb').read()
        content = base64.b64encode(content).decode('ascii').replace('\n', '')
        query = MDConverterQuery(catalog, resource, content)
        await llm_runner.run(query, [dataset.id])
        rts.clear(ctx)

    async def process(self, resource: Resource, dataset: Dataset, catalog: DataCatalog, ctx: str):
        if not ResourceProcessor.check_format(resource):
            return None
        if not resource.url:
            return None
        dataset.versions['resource_analyzer'] = config.feature_versions.resource_analyzer
        if resource.status_loaded and not resource.loading_error:
            resource.status = 'loaded'
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
                rts.set(ctx, f'PROCESSING Format {resource.file_format}')
                if resource.file_format == 'website':
                    await self.process_website(catalog, dataset, resource, to_delete, ctx)
                elif resource.file_format in DOCUMENT_FORMATS:
                    await self.process_document(catalog, dataset, resource, to_delete, ctx)
                else:
                    await self.process_tabular(catalog, dataset, resource, to_delete, ctx)

        finally:
            for filename in to_delete:
                try:
                    os.unlink(filename)
                except Exception as e:
                    rts.set(ctx, f'FAILED TO DELETE {filename}: {e}', 'error')

    def set_concurrency_limit(self, concurrency_limit):
        self.concurrency_limit = concurrency_limit
        return self