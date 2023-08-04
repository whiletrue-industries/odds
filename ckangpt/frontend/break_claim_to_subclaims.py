import json

import guidance

from ckangpt import common, config


PROMPT = '''
{{#system}}
You are an experienced data analyst and logician.
{{/system}}
{{#user}}
Generate a list of individual, separately verifiable claims, which combined are equivalent to the following compound claim: "{{claim}}".
If the claim is already an individual claim, return it as the only element in the list.
Return the list as an array of strings, in a validated json format.
{{/user}}
{{#assistant~}}
{{gen 'claims' temperature=0}}
{{~/assistant}}
'''

def main(claim):
    model_name, cache, debug = config.common()
    llm = guidance.llms.OpenAI(model_name, chat_mode=True, caching=cache)
    res = guidance.Program(
        llm=llm,
        text=PROMPT,
    )(claim=claim)
    try:
        claims = json.loads(res['claims'])
    except json.decoder.JSONDecodeError:
        raise Exception(f'Failed to parse json responses:\n{res.get("claims")}')
    if debug:
        common.print_separator(claims, pprint=True)
    return claims


if __name__ == '__main__':
    import pprint
    pprint.pprint(main("Ontario's corn and soybean yields in 2022 were healthy but lower than the record yields achieved in 2021"))