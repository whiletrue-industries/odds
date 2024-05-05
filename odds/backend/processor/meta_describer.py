import asyncio
import dataclasses
import json

from ...common.datatypes import Dataset
from ...common.llm import llm_runner
from ...common.llm.llm_query import LLMQuery
from ...common.store import store
from ...common.config import config
from ...common.realtime_status import realtime_status as rts


INSTRUCTIONS = '''Following are details on a dataset containing public data. Provide a summary of this dataset in JSON format, including a concise summary and a more detailed description.
The JSON should look like this:
{
    "summary": "<What is a good tagline for this dataset? provide a short snippet, concise and descriptive, using simple terms and avoiding jargon, summarizing the contents of this dataset. The tagline should always start with the words 'Data of', 'Information of', 'List of' or similar.>",
    "description": "<Provide a good description of this dataset in a single paragraph, using simple terms and avoiding jargon.>"
}
Include in the description and summary information regarding relevant time periods, geographic regions, and other relevant details.
Return only the json object, without any additional formatting, explanation or context.
--------------
'''


class MetaDescriberQuery(LLMQuery):

    def __init__(self, dataset: Dataset, ctx: str):
        super().__init__(dataset, None)
        self.upgraded = True
        self.ctx = ctx

    def model(self) -> str:
        return 'cheap' if not self.upgraded else 'expensive'

    def prompt(self) -> list[tuple[str, str]]:
        data = dataclasses.asdict(self.dataset)
        data['resources'] = [
            {k: v for k, v in r.items() if k in ('title', 'fields', 'row_count')}
            for r in data['resources']
            if r.get('status_loaded')]
        for resource in data['resources'][3:]:
            resource.pop('fields')
            resource['title'] = resource['title'][:128]
        data = {k: v for k, v in data.items() if k in ('id', 'title', 'description', 'publisher', 'publisher_description', 'resources')}
        for k in ('title', 'description', 'publisher', 'publisher_description'):
            data[k] = data[k][:250]
        data = json.dumps(data, indent=2, ensure_ascii=False)

        return [
            ('system', 'You are an experienced data analyst.'),
            ('user', INSTRUCTIONS + data)
        ]

    def temperature(self) -> float:
        return 0

    def handle_result(self, result: dict) -> None:
        try:
            self.dataset.better_title = result['summary']
            self.dataset.better_description = result['description']
        except Exception as e:
            print(f'{self.ctx}:ERROR', e)
            print(f'{self.ctx}:RESULT', result)

    def upgrade(self):
        self.upgraded = True

    def max_tokens(self) -> int:
        return 512
            


class MetaDescriber:

    sem: asyncio.Semaphore = None
    concurrency_limit: int = 3

    async def describe(self, dataset: Dataset, ctx: str) -> None:
        # rts.set(ctx, f'DESCRIBING {dataset.title} {dataset.catalogId}')
        if not self.sem:
            self.sem = asyncio.Semaphore(self.concurrency_limit)

        async with self.sem:
            query = MetaDescriberQuery(dataset, ctx)
            await llm_runner.run(query, [dataset.id])
            if dataset.better_title is None:
                query.upgrade()
                await llm_runner.run(query)
            dataset.versions['meta_describer'] = config.feature_versions.meta_describer
            rts.set(ctx, f'DESCRIBED {dataset.title} -> {dataset.better_title}')
