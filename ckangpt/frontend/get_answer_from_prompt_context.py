import json

import tiktoken
from langchain import LLMChain
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate

from . import get_context_from_documents
from ckangpt.common import langchain_llm_callback
from ckangpt import config


SYSTEM_PROMPT_TEMPLATE = SystemMessagePromptTemplate.from_template("""
You are a dataset retrieval system. You locate datasets which contain relevant data based on the user query.
You will have context containing a list of datasets which might be relevant to the user query. You can use this list
to identify relevant datasets. The user query is a sentence describing the user's intent.

Your response is a list of datasets relevant to the user query, one dataset per line. Each dataset is a json object with the following fields:
1. "id": the dataset ID
2. "relevancy": a number from 1 to 10 indicating how relevant the dataset is to the user query
3. "thoughts": optional thoughts about the dataset and why it might be relevant to the user query

Do not include the user prompt in the response. Do not write any explanations in the response. Do not add any datasets which are not in the context.

Following is an example of context, user query and expected response.

Context:

ID: https://data.gov.uk/waste-and-recycling-customer-satisfaction-cbc
Title: Waste and Recycling Customer Satisfaction
---
ID: https://data.gov.uk/waste-collection-contract-cbc
Title: Waste Collection Contract
---
ID: https://data.gov.uk/budget-2018-19
Title: Budget for 2018/19

Query: Please find details about garbage disposal in the UK
{{"id": "https://data.gov.uk/waste-collection-contract-cbc", "relevancy": 8, "thoughts": "your thoughts about the dataset relevancy to the query"}}
{{"id": "https://data.gov.uk/waste-and-recycling-customer-satisfaction-cbc", "relevancy": 3, "thoughts": "..."}}
""")
HUMAN_PROMPT_TEMPLATE = HumanMessagePromptTemplate.from_template("""
Context:

{context}

Query: {user_prompt}
""")
CHAT_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([SYSTEM_PROMPT_TEMPLATE, HUMAN_PROMPT_TEMPLATE])


def get_context(user_prompt, db_query, document_ids, gpt4, num_results, max_tokens):
    if db_query:
        assert not document_ids
        context, *_ = get_context_from_documents.main(from_db_query=db_query, gpt4=gpt4, num_results=num_results, max_tokens=max_tokens)
    elif document_ids:
        context, *_ = get_context_from_documents.main(from_document_ids=document_ids, gpt4=gpt4, num_results=num_results, max_tokens=max_tokens)
    else:
        context, *_ = get_context_from_documents.main(from_user_prompt=user_prompt, gpt4=gpt4, num_results=num_results, max_tokens=max_tokens)
    return context


def main(user_prompt, db_query=None, document_ids=None, gpt4=False, num_results=config.DEFAULT_NUM_RESULTS):
    max_tokens = 8192 if gpt4 else 4096
    response_tokens = 2048 if gpt4 else 1024
    encoding = tiktoken.encoding_for_model('gpt-4' if gpt4 else 'gpt-3.5-turbo')
    prompt_len = len(encoding.encode(CHAT_PROMPT_TEMPLATE.format_prompt(context="", user_prompt=user_prompt).to_string()))
    context = get_context(user_prompt, db_query, document_ids, gpt4, num_results, max_tokens - response_tokens - prompt_len - 10)
    with langchain_llm_callback(gpt4) as (llm, *_):
        chain = LLMChain(
            llm=llm,
            prompt=CHAT_PROMPT_TEMPLATE,
            verbose=True
        )
        res = chain.run(context=context, user_prompt=user_prompt)
        docs = []
        for line in res.split('{'):
            if line.strip():
                line = '{' + line.strip()
                try:
                    doc = json.loads(line)
                except json.decoder.JSONDecodeError:
                    doc = {"error": "JSONDecodeError", "line": line}
                docs.append(doc)
        return docs
