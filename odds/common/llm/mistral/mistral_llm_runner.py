from typing import Any
import httpx
import json

from ..llm_runner import LLMRunner
from ..llm_query import LLMQuery
from ...config import config
from ...retry import Retry

class MistralLLMRunner(LLMRunner):

    MODELS = dict(
        cheap='open-mixtral-8x7b',
        expensive='open-mixtral-8x22b',
    )
    COSTS = dict(
        cheap=dict(
            prompt=0.7/1000000,
            completion=0.7/1000000
        ),
        expensive=dict(
            prompt=2/1000000,
            completion=6/1000000
        ),
    )

    def __init__(self):
        super().__init__('mistral', self.COSTS)

    async def internal_fetch_data(self, request: dict, query: LLMQuery) -> Any:
        cached = self.cache.get_cache(request)
        if cached is not None:
            return cached
        headers = {
            'Authorization': f'Bearer {config.credentials.mistral.key}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        async with httpx.AsyncClient() as client:
            response = await Retry()(client, 'post',
                'https://api.mistral.ai/v1/chat/completions',
                json=request,
                headers=headers,
                timeout=240,
            )
            if response is not None:
                result = response.json()
                if result['usage']:
                    self.cost_collector.start_transaction()
                    self.cost_collector.update_cost(query.model(), 'prompt', result['usage']['prompt_tokens'])
                    self.cost_collector.update_cost(query.model(), 'completion', result['usage']['completion_tokens'])
                    self.cost_collector.end_transaction()
                if result.get('choices') and result['choices'][0].get('message') and result['choices'][0]['message'].get('content'):
                    content: str = result['choices'][0]['message']['content']
                    self.cache.set_cache(request, content)
                    return content

    async def run(self, query: LLMQuery, conversation=[]) -> Any:
        prompt = query.prompt()
        self.cache.store_log(conversation, prompt)
        request = dict(
            model=self.MODELS[query.model()],
            messages=[
                dict(
                    role=p[0],
                    content=p[1]
                )
                for p in prompt
            ],
            temperature=query.temperature()
        )
        if query.expects_json():
            request['response_format'] = {'type': 'json_object'} 
        content = await self.internal_fetch_data(request, query)
        if content is not None:
            self.cache.store_log(conversation, [('assistant', content)])
            if query.expects_json():
                parsed = None
                try:
                    parsed = json.loads(content)
                except:
                    pass
                try:
                    selected_brackets_p = None
                    selected_brackets = None
                    for brackets in ['[]', '{}']:
                        if brackets[0] in content and brackets[1] in content and (selected_brackets_p is None or content.index(brackets[0]) < selected_brackets_p):
                            selected_brackets_p = content.index(brackets[0])
                            selected_brackets = brackets

                    if selected_brackets is not None:
                        content = content[content.index(selected_brackets[0]):content.rindex(selected_brackets[1])+1]
                        parsed = json.loads(content)
                except:
                    pass
            else:
                parsed = content
            if parsed is None:
                print('ERROR PARSING RESULT', query.dataset, content)
            else:
                return query.handle_result(parsed)
        else:
            self.cache.store_error(conversation)
            return query.handle_result(None)
    