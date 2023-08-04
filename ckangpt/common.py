from pprint import pformat

import guidance.llms


def print_separator(msg=None, pprint=False):
    txt = "-" * 10
    if msg:
        txt += '\n'
        txt += pformat(msg, width=200) if pprint else msg
    print(txt)


def print_usage(usage):
    from .config import model_name
    print_separator({
        'model_name': model_name(),
        'total_tokens': usage.get('total_tokens', 0),
        'cost_usd': guidance.llms.OpenAI(model_name(), chat_mode=True).get_usage_cost_usd(usage),
    }, pprint=True)
