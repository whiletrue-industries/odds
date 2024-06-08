from .llm_query import LLMQuery
from .llm_cache import LLMCache
from ..cost_collector import CostCollector

class LLMRunner:

    def __init__(self, name, costs) -> None:
        self.cache = LLMCache(name)
        self.cost_collector = CostCollector(name, costs)

    async def run(self, query: LLMQuery, conversation=[]) -> None:
        pass
