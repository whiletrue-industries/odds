import json

import guidance

from . import get_context_from_documents
from ckangpt import config
from ckangpt.guidance_openai_variable_max_tokens import GuidanceOpenAIVariableMaxTokens


EXAMPLES = [
    {
        'query': 'Please find details about garbage disposal in the UK',
        'context': '''
ID: https://data.gov.uk/waste-and-recycling-customer-satisfaction-cbc
Title: Waste and Recycling Customer Satisfaction
---
ID: https://data.gov.uk/waste-collection-contract-cbc
Title: Waste Collection Contract
---
ID: https://data.gov.uk/budget-2018-19
Title: Budget for 2018/19
''',
        'response': {
            'relevant_datasets': [
                {"id": "https://data.gov.uk/waste-collection-contract-cbc", "relevancy": 8},
                {"id": "https://data.gov.uk/waste-and-recycling-customer-satisfaction-cbc", "relevancy": 3}
            ],
            'need_more_context': False
        }
    },
    {
        'query': 'Where to find synagogues in London?',
        'context': '''
ID: https://data.gov.uk/foo-bar-baz
Title: Foo Bar Baz
''',
        'response': {
            'relevant_datasets': [],
            'need_more_context': True
        }
    },
]


LOCATE_DATASETS = '''
{{#system~}}
You are a dataset retrieval system.
{{/system}}

{{#user~}}
You locate datasets which contain relevant data based on the user query.
You will have context containing a list of datasets which might be relevant to the user query. You can use this list
to identify relevant datasets. The query is a sentence describing the user's intent.

Your response is a json object with the following fields:
* "relevant_datasets": a list of datasets relevant to the user query. Each dataset is a json object with the following fields:
  - "id": the dataset ID
  - "relevancy": a number from 1 to 10 indicating how relevant the dataset is to the user query
* "need_more_context": boolean indicating whether you need more context to find relevant datasets

Do not include the user query in the response. Do not write any explanations in the response. Do not add any datasets which are not in the context.
{{/user}}

{{#each examples}}
{{#user}}
Context:
{{this.context}}

Query: {{this.query}}
{{/user}}

{{#assistant}}
{{json_dumps this.response}}
{{/assistant}}
{{/each}}

{{#user}}
Context:
__GET_CONTEXT__

Query: {{user_prompt}}
{{/user}}

{{#assistant~}}
{{gen 'response'}}
{{~/assistant}}
'''


def get_context(user_prompt, db_query, document_ids, num_results):

    def _get_context(max_tokens):
        if db_query:
            assert not document_ids
            context, *_ = get_context_from_documents.main(from_db_query=db_query, num_results=num_results, max_tokens=max_tokens)
        elif document_ids:
            context, *_ = get_context_from_documents.main(from_document_ids=document_ids, num_results=num_results, max_tokens=max_tokens)
        else:
            context, *_ = get_context_from_documents.main(from_user_prompt=user_prompt, num_results=num_results, max_tokens=max_tokens)
        return context

    return _get_context


def main(user_prompt, db_query=None, document_ids=None, num_results=config.DEFAULT_NUM_RESULTS):
    llm = GuidanceOpenAIVariableMaxTokens(config.model_name(), chat_mode=True, caching=config.ENABLE_CACHE)
    llm.variable_max_tokens_context['GET_CONTEXT'] = get_context(user_prompt, db_query, document_ids, num_results)
    res = guidance.Program(
        llm=llm,
        text=LOCATE_DATASETS,
        examples=EXAMPLES,
        json_dumps=json.dumps,
    )(user_prompt=user_prompt)
    return json.loads(res['response'])
