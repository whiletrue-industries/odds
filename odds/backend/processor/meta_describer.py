import asyncio
import dataclasses
import json

from ...common.datatypes import DataCatalog, Dataset
from ...common.llm import llm_runner
from ...common.llm.llm_query import LLMQuery
from ...common.store import store
from ...common.config import config
from ...common.realtime_status import realtime_status as rts


MAX_STR_LEN = 50000

class MetaDescriberQuery(LLMQuery):

    def __init__(self, dataset: Dataset, catalog: DataCatalog, ctx: str):
        super().__init__(dataset, catalog)
        self.upgraded = True
        self.ctx = ctx

    def model(self) -> str:
        return 'cheap' if not self.upgraded else 'expensive'

    def temperature(self) -> float:
        return 0

    def handle_result(self, result: dict) -> None:
        try:
            self.dataset.better_title = result.get('title')
            self.dataset.summary = result.get('summary')
            self.dataset.better_description = result.get('description')
        except Exception as e:
            print(f'{self.ctx}:ERROR', e)
            print(f'{self.ctx}:RESULT', result)

    def upgrade(self):
        self.upgraded = True

    def max_tokens(self) -> int:
        return 512


class MetaDescriberQueryDataset(MetaDescriberQuery):

    INSTRUCTIONS = '''Following are details on a dataset containing public data.
    Provide a summary of this dataset from "{catalog_name}" ({catalog_description}) in JSON format, including a concise summary and a more detailed description.
    The JSON should look like this:
    {{
        "title": "<What is a good title for this dataset? provide a name, concise but descriptive, using simple terms and avoiding jargon, that would be a good title this dataset.>",
        "summary": "<A one-sentence summary for this dataset. Provide a short snippet, concise and descriptive, using simple terms and avoiding jargon, summarizing the contents of this dataset. The summary should always start with the words 'Data of', 'Information of', 'List of' or similar.>",
        "description": "<Provide a good description of this dataset in a single paragraph, using simple terms and avoiding jargon.>"
    }}

    Include in the description and summary information regarding relevant time periods, geographic regions, and other relevant details.
    {language}
    Return only the json object, without any additional formatting, explanation or context.
    --------------
    '''
    def prompt(self) -> list[tuple[str, str]]:
        data = dataclasses.asdict(self.dataset)
        failed_resources = [f"{r['title']} ({r['file_format']})" for r in data['resources'] if not r.get('status_loaded') and r.get('title')]
        data['resources'] = [
            {k: v for k, v in r.items() if k in ('title', 'fields', 'row_count', 'content')}
            for r in data['resources']
            if r.get('status_loaded')]
        data = {k: v for k, v in data.items() if k in ('id', 'title', 'description', 'publisher', 'publisher_description', 'resources')}
        for k in ('title', 'description', 'publisher', 'publisher_description'):
            data[k] = (data[k] or '')[:250]

        for resource in data['resources'][::-1]:
            encoded = json.dumps(data, indent=2, ensure_ascii=False)
            if len(encoded) > MAX_STR_LEN:
                resource.pop('fields', None)
                if resource['title']:
                    resource['title'] = resource['title'][:128]
                if resource['content']:
                    resource['content'] = resource['content'][:1000]
            else:
                break
        if len(failed_resources) > 0:
            data['other_available_resources'] = failed_resources
        encoded = json.dumps(data, indent=2, ensure_ascii=False)

        language = 'Always match in your response the language of the dataset\'s title, summary and description.'
        if self.catalog.language:
            language = f'Title, summary and description MUST be returned in {self.catalog.language}.'
        instructions = self.INSTRUCTIONS.format(language=language, catalog_name=self.catalog.title, catalog_description=self.catalog.description)

        return [
            ('system', 'You are an experienced data analyst.'),
            ('user', instructions + encoded)
        ]


class MetaDescriberQueryWebsite(MetaDescriberQuery):

    INSTRUCTIONS = '''Following are the contents of a web page containing information with some interest to the public.
    Provide a summary of this web page in JSON format, including a concise summary and a more detailed description.
    The JSON should look like this:
    {{
        "summary": "<What is a good tagline for this web page? provide a short snippet, concise and descriptive, using simple terms and avoiding jargon, summarizing the contents of this page.>",
        "description": "<Provide a good description of this webpage in a single paragraph, using simple terms and avoiding jargon.>"
    }}
    Include in the description and summary information regarding relevant time periods, geographic regions, and other relevant details.
    {language}
    Return only the json object, without any additional formatting, explanation or context.
    --------------
    '''
    def prompt(self) -> list[tuple[str, str]]:
        content = self.dataset.resources[0].content

        language = 'Always match in your response the language of the page\'s title and description.'
        if self.catalog.language:
            language = f'Both summary and description MUST be returned in {self.catalog.language}.'
        instructions = self.INSTRUCTIONS.format(language=language)

        return [
            ('system', 'You are an experienced data analyst.'),
            ('user', instructions + content)
        ]

class EvaluateDescriptionsQuery(LLMQuery):

    INSTRUCTIONS = '''Following are two titles and descriptions for a dataset.
    The first one is the original title and description, and the second one is a new title and description.
    Provide a score from 0 to 100 indicating how much better the new title and description are compared to the original title and description.
    Use the following guidelines to determine the score - the score can be any number between 0 and 100, not just the ones listed below:
    0: No improvement, the new title and description are the same as the original.
    0-33: Minor improvement, the new title and description are slightly better than the original, contain a bit more information or are better phrased.
    33-66: Moderate improvement, the new title and description are significantly better than the original, contain more information or are better phrased.
    66-100: Major improvement, the old title and description were very bad and the new title and description are a significant improvement, with much more information and much better phrasing.
    100: Perfect improvement, the old title and description were completely useless and are now replaced by new ones that are perfect.
    The first one is the original title and description, and the second one is a new title and description.

    Consider separately the title and description, and how much better they are compared to the original title and description.
    The title and description should be evaluated separately, and the score should reflect the overall improvement of both, giving the same weight to both.
    
    Your response should be a single number between 0 and 100, indicating how much better the new title and description are compared to the original title and description.
    Do not include any additional text or formatting in your response - just the number.
    
    -----
    Original title: {original_title}
    Original description:
    {original_description}
    -----
    New title: {new_title}
    New description:
    {new_description}
    '''
    def prompt(self) -> list[tuple[str, str]]:    
        return [
            ('system', 'You are an experienced data analyst.'),
            ('user', self.INSTRUCTIONS.format(
                original_title=self.dataset.title or '<no title>',
                original_description=self.dataset.description or '<no description>',
                new_title=self.dataset.better_title or '<no new title>',
                new_description=self.dataset.better_description or '<no new description>'
            ))
        ]
    
    def handle_result(self, result: str) -> None:
        try:
            result = result.strip()
            result = int(result)
            self.dataset.improvement_score = result
        except Exception as e:
            print(f'{self.ctx}:ERROR', e)
            print(f'{self.ctx}:RESULT', result)
            self.dataset.improvement_score = -1

    def expects_json(self) -> bool:
        return False

    def model(self) -> str:
        return 'cheap'

class MetaDescriber:

    sem: asyncio.Semaphore = None
    concurrency_limit: int = 3

    async def describe(self, catalog: DataCatalog, dataset: Dataset, ctx: str) -> None:
        # rts.set(ctx, f'DESCRIBING {dataset.title} {dataset.catalogId}')
        if not self.sem:
            self.sem = asyncio.Semaphore(self.concurrency_limit)

        async with self.sem:
            if dataset.resources[0].kind == 'website':
                if self.dataset.resources[0].content:
                    query = MetaDescriberQueryWebsite(dataset, catalog, ctx)
                else:
                    rts.set(ctx, f'NO CONTENT')
                    return
            else:
                query = MetaDescriberQueryDataset(dataset, catalog, ctx)
            await llm_runner.run(query, [dataset.id])
            # if dataset.better_title is None and not query.upgraded:
            #     query.upgrade()
            #     await llm_runner.run(query)
            if dataset.better_title is not None and dataset.better_description is not None:
                query = EvaluateDescriptionsQuery(dataset, catalog)
                await llm_runner.run(query)
            dataset.versions['meta_describer'] = config.feature_versions.meta_describer
            rts.set(ctx, f'DESCRIBED ({catalog.language}) {dataset.title} --({dataset.improvement_score})--> {dataset.better_title or 'empty'} ({dataset.summary})')
