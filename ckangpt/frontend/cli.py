import json

import click

from ckangpt.common import print_separator
from ckangpt.config import DEFAULT_NUM_RESULTS


@click.group()
def frontend():
    pass


@frontend.command()
@click.argument("USER_PROMPT")
@click.option('--gpt4', is_flag=True)
def get_vector_db_query(user_prompt, gpt4):
    from . import get_vector_db_query
    print_separator(json.dumps(get_vector_db_query.main(user_prompt, gpt4)))


@frontend.command()
@click.argument("QUERY")
@click.option('--from-user-prompt', is_flag=True)
@click.option('--gpt4', is_flag=True)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
def get_documents_from_vector_db(query, **kwargs):
    from . import get_documents_from_vector_db
    query = '{"words":["garbage","disposal","collection","times","Rehovot","Israel","waste","trash","pickup","schedule"],"country":"IL"}'
    documents = get_documents_from_vector_db.main(json.loads(query), **kwargs)
    for document in documents:
        print_separator(json.loads(document['document']), pprint=True)
    print_separator(f'Found {len(documents)} documents: {",".join((d["id"] for d in documents))}')


@frontend.command()
@click.option('--from-db-query', type=str)
@click.option('--from-document-ids', type=str)
@click.option('--from-user-prompt', type=str)
@click.option('--gpt4', is_flag=True)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
@click.option('--max-tokens', type=int)
def get_context_from_documents(**kwargs):
    from . import get_context_from_documents
    kwargs['from_document_ids'] = kwargs['from_document_ids'].split(',') if kwargs['from_document_ids'] else None
    context, context_len = get_context_from_documents.main(**kwargs)
    print_separator(context)
    print_separator(f'Context length: {context_len}')


@frontend.command()
@click.argument("USER_PROMPT")
@click.option('--db-query', type=str)
@click.option('--document-ids', type=str)
@click.option('--gpt4', is_flag=True)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
def get_answer_from_prompt_context(**kwargs):
    from . import get_answer_from_prompt_context
    kwargs['document_ids'] = kwargs['document_ids'].split(',') if kwargs['document_ids'] else None
    print_separator(get_answer_from_prompt_context.main(**kwargs), pprint=True)


@frontend.command()
@click.argument("USER_PROMPT")
@click.option('--document-ids', type=str)
@click.option('--gpt4', is_flag=True)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
def find_datasets(**kwargs):
    from . import find_datasets
    docs = find_datasets.main(**kwargs)
    for doc in docs:
        print_separator(doc, pprint=True)
    print_separator(f'Found {len(docs)} documents, listed above from least to most relevant.')
