import json

import guidance

from ckangpt import common, config


PROMPT = '''
{{#system}}
You are an experienced data analyst.
{{/system}}
{{#user}}
Generate a list of likely relevant official dataset titles which would contain data that could be used to verify the following claims.
Return the list as an array of strings, in a validated json format.

Claims:
{{#each claims}}
- {{this}}
{{/each}}


{{/user}}
{{#assistant~}}
{{gen 'dataset_titles' temperature=0}}
{{~/assistant}}
'''

def main(claims):
    model_name, cache, debug = config.common()
    llm = guidance.llms.OpenAI(model_name, chat_mode=True, caching=cache)
    res = guidance.Program(
        llm=llm,
        text=PROMPT,
    )(claims=claims)
    try:
        dataset_titles = json.loads(res['dataset_titles'])
    except json.decoder.JSONDecodeError:
        raise Exception(f'Failed to parse json responses:\n{res.get("dataset_titles")}')
    if debug:
        common.print_separator(dataset_titles, pprint=True)
    return dataset_titles


if __name__ == '__main__':
    claims = [
        "Ontario's corn yields in 2022 were healthy",
        "Ontario's corn yields in 2022 were lower than the record yields achieved in 2021",
        "Ontario's soybean yields in 2022 were healthy",
        "Ontario's soybean yields in 2022 were lower than the record yields achieved in 2021"
    ]
    import pprint
    pprint.pprint(main(claims))