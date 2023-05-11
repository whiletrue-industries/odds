import json

import guidance

from ckangpt import common, config


EXAMPLES = [
    {
        'query': 'Can you find any research on biotoxins in mussels in the United Kingdom?',
        'response': {
            'words': [
                'research', 'biotoxins', 'mussels', 'UK', 'studies', 'articles', 'journals', 'marine', 'monitoring', 'Britain', 'United Kingdom', 'shellfish', 'bivalves', 'mollusks', 'seafood', 'aquaculture', 'farming'
            ],
            'country': 'UK'
        },
        'critic_response': {
            'thoughts': 'The response is good, but it is missing some words',
            'country': 'UK',
            'additional_words': ['ocean', 'sea', 'aquatic', 'toxins', 'toxic', 'poison', 'contamination', 'pollution', 'pollutants', 'chemicals', 'chemical', 'heavy metals', 'heavy metal', 'mercury', 'lead', 'arsenic', 'cadmium', 'copper', 'zinc', 'nickel', 'chromium', 'manganese', 'iron', 'aluminum', 'tin', 'silver', 'gold', 'platinum', 'palladium', 'rhodium', 'iridium', 'ruthenium', 'osmium', 'seawater']
        }
    },
    {
        'query': 'how clean is the tap water in Tel Aviv',
        'response': {
            "words": [
                "tap", "water", "quality", "Israel", "safety", "standards", "purification"
            ]
        },
        'critic_response': {
            'thoughts': 'Some additional words were missing and the country was not specified',
            'country': 'IL',
            'additional_words': ['drinking', 'potable', 'chlorine', 'fluoride', 'bacteria', 'viruses', 'parasites', 'contaminants', 'contamination', 'pollution', 'treatment', 'filtration', 'purification', 'desalination', 'reverse osmosis', 'water softening', 'water hardness', 'water softener']
        }
    },
    {
        'query': 'Where can I find timetable of trains in Moscow?',
        'response': {
            "words": [
                "Moscow", "train", "timetable", "schedule", "Russia"
            ]
        },
        'critic_response': {
            'thoughts': '<YOUR THOUGHTS HERE>',
            'additional_words': ['railway', 'rail', 'station', 'stations', 'railroad', 'railroads', 'railways', 'railway station', 'railway stations', 'railroad station', 'railroad stations', 'railway timetable', 'railway schedule', 'railroad timetable', 'railroad schedule', 'railway map', 'railroad map', 'railway route', 'railroad route', 'railway routes', 'railroad routes', 'railway map', 'railroad map', 'railway route', 'railroad route', 'railway routes', 'railroad routes', 'railway map', 'railroad map', 'railway route', 'railroad route', 'railway routes', 'railroad routes', 'railway map', 'railroad map', 'railway route', 'railroad route', 'railway routes', 'railroad routes', 'railway map', 'railroad map', 'railway route', 'railroad route', 'railway routes', 'railroad routes', 'railway map', 'railroad map', 'railway route', 'railroad route', 'railway routes', 'railroad routes', 'railway map', 'railroad map', 'railway route', 'railroad route', 'railway routes', 'railroad routes']
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

* "thoughts": your thoughts about the previous response
* "country": the 2 letter country code of the country which you think is relevant to the user prompt
* "additional_words": an array of additional words which might also be relevant to the user prompt

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
    guidance.llm = guidance.llms.OpenAI(model_name, chat_mode=True, caching=cache)
    res = guidance.Program(
        GET_VECTOR_DB_QUERY,
        examples=EXAMPLES,
        json_dumps=json.dumps,
        get_critic_example_json=get_critic_example_json,
        get_critic_user_query=get_critic_user_query,
    )(user_prompt=user_prompt)
    vector_db_query_json_uncriticized = json.loads(res['vector_db_query_json_uncriticized'])
    vector_db_query_json_criticized = json.loads(res['vector_db_query_json_criticized'])
    if debug:
        common.print_separator(vector_db_query_json_uncriticized, pprint=True)
        common.print_separator(vector_db_query_json_criticized, pprint=True)
    country = vector_db_query_json_criticized.get('country') or vector_db_query_json_uncriticized.get('country')
    return {
        'words': list(set(vector_db_query_json_uncriticized['words'])),
        **({'additional_words': list(set(vector_db_query_json_criticized['additional_words']))} if vector_db_query_json_criticized.get('additional_words') else {}),
        **({'country': country} if country else {}),
    }
