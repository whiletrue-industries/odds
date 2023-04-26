import json
from textwrap import dedent

from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.callbacks import get_openai_callback

from ckangpt import chroma


class DataSetsPromptTemplate(PromptTemplate):

    def format(self, **kwargs):
        kwargs = self._merge_partial_and_user_variables(**kwargs)
        dataset = json.loads(kwargs['page_content'])
        res = [l for l in [
            f"Title: {dataset['title'].strip()}",
            f"Notes: {dataset['notes'].strip()}" if dataset.get('notes') else None,
            f"Organization: {dataset['organization']['title'].strip()}" if dataset.get('organization', {}).get('title') else None,
            f"Organization description: {dataset['organization']['description'].strip()}" if dataset.get('organization', {}).get('description') else None,
        ] if l]
        for num, resource in dataset.get('resources', {}).items():
            if resource.get('name'):
                res.append(f"Resource {num}: {resource['name'].strip()}")
        return '\n'.join(res)


def main(query, gpt4=False):
    if gpt4:
        print('WARNING! Using GPT-4 - this will be slow and expensive!')
    retriever = chroma.get_langchain_datasets_db().as_retriever()
    chain = RetrievalQA.from_chain_type(
        ChatOpenAI(model_name='gpt-4' if gpt4 else 'gpt-3.5-turbo', request_timeout=240),
        chain_type='stuff', chain_type_kwargs={
            "prompt": ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(dedent("""
                    Find relevant datasets from the following list to answer the users question.
                    In your reply list the relevant dataset titles, why you think each is relevant and to what degree.
                    If you don't know the answer, just say that you don't know, don't try to make up an answer.
                    ----------------
                    {context}
                """)),
                HumanMessagePromptTemplate.from_template("{question}"),
            ]),
            "document_prompt": DataSetsPromptTemplate(input_variables=["page_content"], template="{page_content}"),
            "verbose": True
        },
        retriever=retriever, return_source_documents=True,
        verbose=True
    )
    with get_openai_callback() as cb:
        res = chain({"query": query})
        print(cb)
    print(f'query: {res["query"]}')
    print(f'result: {res["result"]}')
    print('source documents:')
    for doc in res['source_documents']:
        print(f' - {doc}')
    print(res)
    print('-------')
    print(res['result'])
