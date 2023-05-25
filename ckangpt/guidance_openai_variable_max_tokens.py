"""
This is a replacement for guidance.llms.OpenAI that allows for variable max_tokens and some other features.

It runs each time a guidance "gen" block is encountered before the call to openAI API is made.
It counts the number of tokens in the messages and set max_tokens to the available remaining tokens for the API call.
It also adds some usage data and debug details.

An additional feature it provides is to allow running a function to replace a part of the text before the call to openAI API is made.
In the following example, the __TEXT__ string will be replaced by a text with length of the allowed max tokens for the model
minus the number of tokens in the messages minus 200 tokens (the max_tokens in the gen block).

def get_text(max_tokens):
    # assuming each * is 1 token, this will return a string of max_tokens length
    return '*' * max_tokens

llm = GuidanceOpenAIVariableMaxTokens(model_name, chat_mode=True)
llm.variable_max_tokens_context['TEXT'] = get_text
guidance.Program(
    llm=llm,
    text='''
{#user}
What do you think about the following text?

__TEXT__

Write your thougts.
{/user}

{#assistant}
{gen 'response' max_tokens=200}
{/assistant}
'''
    )
"""
from collections import defaultdict

import openai
import guidance
import tiktoken
from langchain.callbacks import openai_info


def num_tokens_from_messages(messages, model):
    encoding = tiktoken.encoding_for_model(model)
    if model == 'gpt-3.5-turbo':
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == 'gpt-4':
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


class GuidanceOpenAIVariableMaxTokensSession(guidance.llms._openai.OpenAISession):

    def _preprocess_call_prompt_to_messages(self, prompt, max_tokens, **kwargs):
        assert self.llm.chat_mode
        if self.llm.model_name == 'gpt-3.5-turbo':
            model_max_tokens = 4096
        elif self.llm.model_name == 'gpt-4':
            model_max_tokens = 8192
        else:
            raise Exception(f"Unsupported model {self.llm.model_name}")
        messages = guidance.llms._openai.prompt_to_messages(prompt)
        messages_for_count = []
        got_replacement = False
        for message in messages:
            for k, func in self.llm.variable_max_tokens_context.items():
                if f'__{k}__' in message['content']:
                    assert not got_replacement, 'only one replacement is supported'
                    got_replacement = True
                    message = {
                        **message,
                        'content': message['content'].replace(f'__{k}__', '')
                    }
            messages_for_count.append(message)
        num_tokens = num_tokens_from_messages(messages_for_count, self.llm.model_name)
        debug_data = {
            'got_replacement': False,
            'num_tokens': num_tokens,
            'model_max_tokens': model_max_tokens,
            'kwargs_max_tokens': max_tokens,
        }
        if got_replacement:
            debug_data['got_replacement'] = True
            debug_data['remaining_tokens'] = remaining_tokens = model_max_tokens - max_tokens - num_tokens - 3
            messages_for_output = []
            for message in messages:
                for k, func in self.llm.variable_max_tokens_context.items():
                    if f'__{k}__' in message['content']:
                        message = {
                            **message,
                            'content': message['content'].replace(f'__{k}__', func(remaining_tokens))
                        }
                messages_for_output.append(message)
            debug_data['num_tokens_after_replace'] = num_tokens_after_replace = num_tokens_from_messages(
                messages_for_output, self.llm.model_name)
            max_tokens = model_max_tokens - num_tokens_after_replace - 3
        else:
            messages_for_output = messages_for_count
            max_tokens = model_max_tokens - num_tokens - 3
        debug_data['max_tokens'] = max_tokens
        assert max_tokens > 1, f"not enough tokens to generate a response\n{debug_data}"
        self.openai_last_call_actual_max_tokens = max_tokens
        return messages_for_output, max_tokens

    async def __call__(self, prompt, **kwargs):
        messages, kwargs['max_tokens'] = self._preprocess_call_prompt_to_messages(prompt, **kwargs)
        self.llm.openai_last_call = (messages, kwargs)
        res = await super().__call__(messages, **kwargs)
        self.llm.openai_usage['num_calls'] += 1
        for k, v in res['usage'].items():
            self.llm.openai_usage[k] += v
        self.llm.openai_last_result = res
        return res


class GuidanceOpenAIVariableMaxTokens(guidance.llms.OpenAI):

    def __init__(self, *args, **kwargs):
        self.variable_max_tokens_context = {}
        self.openai_usage = defaultdict(int)
        self.openai_last_call = None
        self.openai_last_result = None
        self.openai_last_call_actual_max_tokens = None
        super().__init__(*args, **kwargs)

    def session(self, asynchronous=False):
        if asynchronous:
            return GuidanceOpenAIVariableMaxTokensSession(self)
        else:
            return guidance.llms._openai.SyncSession(GuidanceOpenAIVariableMaxTokensSession(self))

    def get_openai_usage(self, add_usage=None):
        usage = {
            **self.openai_usage,
            'cost_usd': (
                openai_info.get_openai_token_cost_for_model(self.model_name, self.openai_usage['completion_tokens'], is_completion=True)
                + openai_info.get_openai_token_cost_for_model(self.model_name, self.openai_usage['prompt_tokens'])
            ),
            'model_name': self.model_name
        }
        if add_usage is None:
            return usage
        else:
            assert usage['model_name'] == add_usage['model_name']
            return {
                **{
                    k: v + add_usage.get(k, 0)
                    for k, v
                    in usage.items()
                    if k != 'model_name'
                },
                'model_name': usage['model_name']
            }


    def _library_call(self, **kwargs):
        self.openai_usage['num_library_calls'] += 1
        prev_key = openai.api_key
        assert self.token is not None, "You must provide an OpenAI API key to use the OpenAI LLM. Either pass it in the constructor, set the OPENAI_API_KEY environment variable, or create the file ~/.openai_api_key with your key in it."
        openai.api_key = self.token
        if self.chat_mode:
            kwargs['messages'] = kwargs['prompt']
            del kwargs['prompt']
            del kwargs['echo']
            del kwargs['logprobs']
            out = openai.ChatCompletion.create(**kwargs)
            out = guidance.llms._openai.add_text_to_chat_mode(out)
        else:
            out = openai.Completion.create(**kwargs)
        openai.api_key = prev_key
        return out

    def _rest_call(self, **kwargs):
        raise NotImplementedError("REST calls are not supported")
