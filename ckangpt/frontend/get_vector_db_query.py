import json

import guidance

from ckangpt import common, config


EXAMPLES = [
    {
        'query': 'Can you find any research on biotoxins in mussels in the United Kingdom?',
        'response': {
            'words': [
                'research', 'biotoxins', 'mussels', 'UK', 'studies', 'articles', 'journals', 'marine', 'monitoring', 'Britain', 'United Kingdom', 'shellfish', 'bivalves',
            ],
            'country': 'UK'
        },
        'critic_response': {
            'country': 'UK',
            'additional_words': ['mollusks', 'seafood', 'aquaculture', 'farming']
        }
    },
    {
        'query': 'how clean is the tap water in Tel Aviv',
        'response': {
            "words": [
                "tap", "water", "quality", "Israel",
            ]
        },
        'critic_response': {
            'country': 'IL',
            'additional_words': ["safety", "standards", "purification"]
        }
    },
    {
        'query': 'Where can I find timetable of trains in Moscow?',
        'response': {
            "words": [
                "Moscow", "train", "timetable",
            ]
        },
        'critic_response': {
            'additional_words': ["schedule", "Russia"]
        }
    }
]


GET_VECTOR_DB_QUERY_UNCRITICIZED = '''
{{#system}}
You are a contextual search query system.
{{/system}}
{{#user}}
You write a query to the database which will return relevant items based on the user prompt. The user prompt is a sentence describing the user's intent.

The response is a json object with the following fields:
* "words": an array of words which will retrieve relevant data from the database. Extrapolate to include words which the user did not
write but which you think will also be relevant.
* "country": optional 2 letter country code, must be included if the user prompt specified a country.
    Available country codes:
      - UK: United Kingdom
      - IL: Israel

Do not include the user prompt in the response. Do not write any explanations in the response. Only respond with the json object.
{{/user}}

{{#each examples}}
{{#user}}
{{this.query}}
{{/user}}
{{#assistant}}
{{json_dumps this.response}}
{{/assistant}}
{{/each}}

{{#user}}
{{user_prompt}}
{{/user}}

{{#assistant~}}
{{gen 'vector_db_query_json_uncriticized'}}
{{~/assistant}}
'''


GET_VECTOR_DB_QUERY_CRITIC = '''
{{#system}}
You are a contextual search query system critic.
{{/system}}
{{#user}}
You analyze the response of a contextual search query system and provide feedback on how to improve it.
The user prompt is a json object with the following fields:

* "query": a sentence describing the user's intent which was used to get the response you are now criticizing.
* "words": an array of words which will retrieve relevant data from the database, extrapolated to include words which the user did not
write but which might also be relevant.
* "country": optional 2 letter country code, must be included if the user prompt specified a country.
    Available country codes:
      - UK: United Kingdom
      - IL: Israel

Your response must be a json object with the following fields:

* "country": the 2 letter country code of the country which you think is relevant to the user prompt
* "additional_words": an array of additional words which might also be relevant to the user prompt, 
only include words which are not already in the "words" field of the previous response. Don't include lexical variants of words already in the "words" field.

Do not write any explanations in the response. Only respond with the json object.
{{/user}}

{{#each examples}}
{{#user}}
{{get_critic_example_json this}}
{{/user}}
{{#assistant}}
{{json_dumps this.critic_response}}
{{/assistant}}
{{/each}}

{{#user}}
{{get_critic_user_query user_prompt vector_db_query_json_uncriticized}}
{{/user}}

{{#assistant~}}
{{gen 'vector_db_query_json_criticized'}}
{{~/assistant}}
'''


GET_VECTOR_DB_QUERY = f'''
{{#block hidden=True}}
{GET_VECTOR_DB_QUERY_UNCRITICIZED}
{{/block}}

{GET_VECTOR_DB_QUERY_CRITIC}
'''


def get_critic_example_json(example):
    return json.dumps({
        'query': example['query'],
        **example['response'],
    })


def get_critic_user_query(user_prompt, vector_db_query_json_uncriticized):
    return json.dumps({
        'query': user_prompt,
        **json.loads(vector_db_query_json_uncriticized),
    })


def main(user_prompt):
    model_name, cache, debug = config.common()
    llm = guidance.llms.OpenAI(model_name, chat_mode=True, caching=cache)
    res = guidance.Program(
        llm=llm,
        text=GET_VECTOR_DB_QUERY,
        examples=EXAMPLES,
        json_dumps=json.dumps,
        get_critic_example_json=get_critic_example_json,
        get_critic_user_query=get_critic_user_query,
    )(user_prompt=user_prompt)
    try:
        vector_db_query_json_uncriticized = json.loads(res['vector_db_query_json_uncriticized'])
        vector_db_query_json_criticized = json.loads(res['vector_db_query_json_criticized'])
    except json.decoder.JSONDecodeError:
        raise Exception(f'Failed to parse json responses: {res}')
    if debug:
        common.print_separator(vector_db_query_json_uncriticized, pprint=True)
        common.print_separator(vector_db_query_json_criticized, pprint=True)
    country = vector_db_query_json_criticized.get('country') or vector_db_query_json_uncriticized.get('country')
    return (
        {k: llm.usage.get(k, 0) + llm.usage.get(k, 0) for k in {*llm.usage.keys(), *llm.usage_cached.keys()}},
        {
            'words': list(set(vector_db_query_json_uncriticized['words'])),
            **({'additional_words': list(set(vector_db_query_json_criticized['additional_words']))} if vector_db_query_json_criticized.get('additional_words') else {}),
            **({'country': country} if country else {}),
        }
    )
