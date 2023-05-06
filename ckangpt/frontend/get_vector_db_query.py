import json

from langchain import LLMChain
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

from ckangpt.common import langchain_llm_callback


SYSTEM_PROMPT_TEMPLATE = SystemMessagePromptTemplate.from_template("""
You are a contextual search query system. You write a query to the database which will return relevant items
based on the user prompt. The user prompt is a sentence describing the user's intent.

The response is a json object with the following fields:
1. "words": an array of words which will retrieve relevant data from the database. Extrapolate to include words which the user did not
write but which you think will also be relevant.
2. "country": optional 2 letter country code of the country relevant to the search, include only if there is a clear indication of the country in the user prompt.
    Available country codes:
      - UK: United Kingdom
      - IL: Israel

Do not include the user prompt in the response. Do not write any explanations in the response. Only respond with the json object.

Example: Can you find any research on biotoxins in mussels in the UK?
{{"words": ["research", "biotoxins", "mussels", "UK", "studies", "articles", "journals", "marine", "monitoring", "Britain", "United Kingdom", "shellfish", "bivalves", "mollusks", "seafood", "aquaculture", "farming"], "country": "UK"}}

Example: how clean is the tap water in Israel
{{"words": ["tap", "water", "quality", "Israel", "safety", "standards", "purification"], "country": "IL"}}

Example: Where can I find timetable of trains in Moscow?
{{"words": ["Moscow", "train", "timetable", "schedule", "Russia"]}}
""")
HUMAN_PROMPT_TEMPLATE = HumanMessagePromptTemplate.from_template("{user_prompt}")
CHAT_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([SYSTEM_PROMPT_TEMPLATE, HUMAN_PROMPT_TEMPLATE])


def main(user_prompt, gpt4=False):
    with langchain_llm_callback(gpt4) as (llm, *_):
        chain = LLMChain(
            llm=llm,
            prompt=CHAT_PROMPT_TEMPLATE,
            verbose=True
        )
        return json.loads(chain.run(user_prompt))
