import json

import click

from ckangpt.common import print_separator, print_usage
from ckangpt.config import DEFAULT_NUM_RESULTS


@click.group()
def frontend():
    pass


@frontend.command()
@click.argument("USER_PROMPT")
def get_vector_db_query(**kwargs):
    from . import get_vector_db_query
    usage, res = get_vector_db_query.main(**kwargs)
    print_separator(json.dumps(res))
    print_usage(usage)


@frontend.command()
@click.argument("QUERY")
@click.option('--from-user-prompt', is_flag=True)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
def get_documents_from_vector_db(query, **kwargs):
    from . import get_documents_from_vector_db
    usage, documents = get_documents_from_vector_db.main(json.loads(query), **kwargs)
    for document in documents:
        print_separator(json.loads(document['document']), pprint=True)
    print_separator(f'Found {len(documents)} documents: {",".join((d["id"] for d in documents))}')
    print_usage(usage)


@frontend.command()
@click.option('--from-db-query', type=str)
@click.option('--from-document-ids', type=str)
@click.option('--from-user-prompt', type=str)
@click.option('--load-from-disk', is_flag=True)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
@click.option('--max-tokens', type=int)
def get_context_from_documents(**kwargs):
    from . import get_context_from_documents
    kwargs['from_document_ids'] = kwargs['from_document_ids'].split(',') if kwargs['from_document_ids'] else None
    usage, context, context_len = get_context_from_documents.main(**kwargs)
    print_separator(context)
    print_separator(f'Context length: {context_len}')
    print_usage(usage)


@frontend.command()
@click.argument("USER_PROMPT")
@click.option('--db-query', type=str)
@click.option('--document-ids', type=str)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
@click.option('--load-from-disk', is_flag=True)
def get_answer_from_prompt_context(**kwargs):
    from . import get_answer_from_prompt_context
    kwargs['document_ids'] = kwargs['document_ids'].split(',') if kwargs['document_ids'] else None
    usage, res = get_answer_from_prompt_context.main(**kwargs)
    print_separator(res, pprint=True)
    print_usage(usage)


@frontend.command()
@click.argument("USER_PROMPT")
@click.option('--document-ids', type=str)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
@click.option('--load-from-disk', is_flag=True)
def find_datasets(**kwargs):
    from . import find_datasets
    usage, answer = find_datasets.main(**kwargs)
    docs = answer.pop('relevant_datasets')
    for doc in docs:
        print_separator(doc, pprint=True)
    print_separator(f'Found {len(docs)} documents, listed above from least to most relevant.')
    print_separator(answer, pprint=True)
    print_usage(usage)
