"""
This is a replacement for guidance.llms.OpenAI that allows for variable max_tokens.

It runs each time a guidance "gen" block is encountered before the call to openAI API is made.
It counts the number of tokens in the messages and set max_tokens to the available remaining tokens for the API call.

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
import openai
import guidance
import tiktoken


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


class GuidanceOpenAIVariableMaxTokens(guidance.llms.OpenAI):

    def __init__(self, *args, **kwargs):
        self.variable_max_tokens_context = {}
        super().__init__(*args, **kwargs)

    def _preprocess_kwargs(self, chat_completion, **kwargs):
        assert chat_completion
        model = kwargs['model']
        if model == 'gpt-3.5-turbo':
            model_max_tokens = 4096
        elif model == 'gpt-4':
            model = 'gpt-4'
            model_max_tokens = 8192
        else:
            raise Exception(f"Unknown model {model}")
        messages_for_count = []
        got_replacement = False
        for message in kwargs['messages']:
            for k, func in self.variable_max_tokens_context.items():
                if f'__{k}__' in message['content']:
                    assert not got_replacement, 'only one replacement is supported'
                    got_replacement = True
                    message = {
                        **message,
                        'content': message['content'].replace(f'__{k}__', '')
                    }
            messages_for_count.append(message)
        num_tokens = num_tokens_from_messages(messages_for_count, model)
        if got_replacement:
            remaining_tokens = model_max_tokens - kwargs['max_tokens'] - num_tokens - 3
            messages_for_output = []
            for message in kwargs['messages']:
                for k, func in self.variable_max_tokens_context.items():
                    if f'__{k}__' in message['content']:
                        message = {
                            **message,
                            'content': message['content'].replace(f'__{k}__', func(remaining_tokens))
                        }
                messages_for_output.append(message)
            max_tokens = model_max_tokens - num_tokens_from_messages(messages_for_output, model) - 3
        else:
            messages_for_output = messages_for_count
            max_tokens = model_max_tokens - num_tokens - 3
        return {
            **kwargs,
            'messages': messages_for_output,
            'max_tokens': max_tokens,
        }

    def _library_call(self, **kwargs):
        prev_key = openai.api_key
        assert self.token is not None, "You must provide an OpenAI API key to use the OpenAI LLM. Either pass it in the constructor, set the OPENAI_API_KEY environment variable, or create the file ~/.openai_api_key with your key in it."
        openai.api_key = self.token
        if self.chat_mode:
            kwargs['messages'] = guidance.llms._openai.prompt_to_messages(kwargs['prompt'])
            del kwargs['prompt']
            del kwargs['echo']
            del kwargs['logprobs']
            out = openai.ChatCompletion.create(**self._preprocess_kwargs(chat_completion=True, **kwargs))
            out = guidance.llms._openai.add_text_to_chat_mode(out)
        else:
            out = openai.Completion.create(**self._preprocess_kwargs(chat_completion=False, **kwargs))
        openai.api_key = prev_key
        return out
