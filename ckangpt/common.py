from pprint import pformat
from contextlib import contextmanager

import guidance.llms
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback


@contextmanager
def langchain_llm_callback(gpt4, verbose=True):
    if gpt4:
        if verbose:
            print('WARNING! Using GPT-4 - this will be slow and expensive!')
    llm = ChatOpenAI(model_name='gpt-4' if gpt4 else 'gpt-3.5-turbo', request_timeout=240)
    with get_openai_callback() as cb:
        yield llm, cb
        if verbose:
            print(cb)


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
