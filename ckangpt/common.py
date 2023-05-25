from pprint import pformat
from contextlib import contextmanager

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
    usage['num_cached_calls'] = usage.get('num_calls', 0) - usage.get('num_library_calls', 0)
    print_separator({
        {
            'cost_usd': 'Cost (USD) if all calls were non-cached',
            'num_library_calls': 'Number of non-cached calls',
            'num_cached_calls': 'Number of cached calls',
            'model_name': 'Model name',
            'total_tokens': 'Total tokens',
        }.get(k, k): round(v, 5) if k == 'cost_usd' else v
        for k, v
        in {'num_library_calls': 0, **usage}.items()
        if k in ['cost_usd', 'num_library_calls', 'model_name', 'total_tokens', 'num_cached_calls']
    }, pprint=True)
