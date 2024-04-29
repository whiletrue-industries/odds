import asyncio
from typing import Any, Type

from ...common.llm.llm_query import LLMQuery
from ...common.llm import llm_runner
from ...common.config import config


class FrontendQuery(LLMQuery):

    def __init__(self):
        super().__init__(None, None)

    def model(self) -> str:
        return 'expensive'

    def temperature(self) -> float:
        return 0

    def prompt(self) -> list[tuple[str, str]]:
        pass

    def handle_result(self, result: dict) -> Any:
        pass


class FrontendQueryRunner:

    sem: asyncio.Semaphore = None
    concurrency_limit: int = 3

    def __init__(self, query_cls: Type[LLMQuery]):
        self.query_cls = query_cls

    async def __call__(self, *args, **kwargs) -> None:
        if not self.sem:
            self.sem = asyncio.Semaphore(self.concurrency_limit)
        conversation = kwargs.get('conversation', [])
        async with self.sem:
            query = self.query_cls(*args)
            ret = await llm_runner.run(query, conversation=conversation)
            if config.debug:
                print('FQ', self.query_cls.__name__, repr(ret)[:200])
            return ret
