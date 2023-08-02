import json

import guidance

from ckangpt import common, config


PROMPT = '''
{{#system}}
You are an experienced data analyst.
{{/system}}
{{#user}}
Review the article carefully, identify and extract the 3 most crucial stand alone claims made within the text.
Each claim should be exact, objective and simple to verify for credibility using factual, numeric, data which might be found in an official published dataset.

For each claim, provide its text verbatim, a brief reason explaining why its verifiable by referencing relevant official datasets, and a 2 letter code of the geographic region it refers to, if applicable.
Show results as an array of objects, in a validated json format.

Example response:
[
    {
        "quote": "When the unemployment went low by two percent during the previous quarter",
        "geo": "CA",
        "claim": "The unemployment rate decreased by 2 percent in the last quarter.",
        "sources": "unemployment rates are published periodically by the UK's Department of Labor"
    },
    ...
]

Article Text:
{{article_text}}
{{/user}}
{{#assistant~}}
{{gen 'claims' temperature=0}}
{{~/assistant}}
'''

def main(article_text):
    model_name, cache, debug = config.common()
    llm = guidance.llms.OpenAI(model_name, chat_mode=True, caching=cache)
    res = guidance.Program(
        llm=llm,
        text=PROMPT,
    )(article_text=article_text)
    try:
        claims = json.loads(res['claims'])
    except json.decoder.JSONDecodeError:
        raise Exception(f'Failed to parse json responses:\n{res.get("claims")}')
    if debug:
        common.print_separator(claims, pprint=True)
    return claims
