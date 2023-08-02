import json

import click

from ckangpt.common import print_separator, print_usage
from ckangpt.config import DEFAULT_NUM_RESULTS


@click.group()
def frontend():
    pass


@frontend.command()
@click.option('--port', default=8000, help='Port to bind to.')
@click.option('--host', default='0.0.0.0', help='Host to bind to.')
@click.option('--debug', is_flag=True)
def start_dev_server(port, host, debug):
    import uvicorn
    uvicorn.run(
        "ckangpt.frontend.api.main:app",
        host=host,
        port=port,
        log_level="info" if not debug else "debug",
        reload=True,
        loop='asyncio',
    )

@frontend.command()
@click.argument("TEXT")
def extract_claims_from_text(text, **kwargs):
    from . import extract_claims_from_text
    if text == '-':
        text = click.get_text_stream('stdin').read()
    claims = extract_claims_from_text.main(text, **kwargs)
    for claim in claims:
        print_separator(claim, pprint=True)
    print_separator(f'Found {len(claims)} claims')


@frontend.command()
@click.argument("CLAIM")
def break_claim_to_subclaims(claim, **kwargs):
    from . import break_claim_to_subclaims
    claims = break_claim_to_subclaims.main(claim, **kwargs)
    for claim in claims:
        print_separator(claim, pprint=True)
    print_separator(f'Found {len(claims)} sub-claims')



@frontend.command()
@click.argument("CLAIMS")
def get_potential_dataset_names(claims, **kwargs):
    from . import get_potential_dataset_names
    claims = claims.split(',')
    datasets = get_potential_dataset_names.main(claims, **kwargs)
    for dataset in datasets:
        print('-', dataset)
    print_separator(f'Found {len(datasets)} dataset names')


@frontend.command()
@click.argument("USER_PROMPT")
def get_vector_db_query(**kwargs):
    from . import get_vector_db_query
    usage, res = get_vector_db_query.main(**kwargs)
    print_separator(json.dumps(res))
    print_usage(usage)


@frontend.command()
@click.argument("QUERY")
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
def get_documents_from_vector_db(query, **kwargs):
    from . import get_documents_from_vector_db
    documents = get_documents_from_vector_db.main(json.loads(query), **kwargs)
    for document in documents:
        print_separator(json.loads(document['document']), pprint=True)
    print_separator(f'Found {len(documents)} documents: {",".join((d["id"] for d in documents))}')


@frontend.command()
@click.option('--db-queries', type=str)
@click.option('--from-document-ids', type=str)
@click.option('--load-from-disk', is_flag=True)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
@click.option('--max-tokens', type=int)
def get_context_from_documents(**kwargs):
    from . import get_context_from_documents
    kwargs['from_document_ids'] = kwargs['from_document_ids'].split(',') if kwargs['from_document_ids'] else None
    kwargs['db_queries'] = kwargs['db_queries'].split(',') if kwargs['db_queries'] else None
    context, context_len = get_context_from_documents.main(**kwargs)
    print_separator(context)
    print_separator(f'Context length: {context_len}')


@frontend.command()
@click.argument("USER_PROMPT")
@click.option('--db-queries', type=str)
@click.option('--document-ids', type=str)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
@click.option('--load-from-disk', is_flag=True)
def get_answer_from_prompt_context(**kwargs):
    from . import get_answer_from_prompt_context
    kwargs['document_ids'] = kwargs['document_ids'].split(',') if kwargs['document_ids'] else None
    kwargs['db_queries'] = kwargs['db_queries'].split(',') if kwargs['db_queries'] else None
    usage, res = get_answer_from_prompt_context.main(**kwargs)
    print_separator(res, pprint=True)
    print_usage(usage)


@frontend.command()
@click.argument("USER_PROMPT")
@click.argument("DB_QUERIES")
@click.option('--document-ids', type=str)
@click.option('--num-results', type=int, default=DEFAULT_NUM_RESULTS)
@click.option('--load-from-disk', is_flag=True)
def find_datasets(**kwargs):
    from . import find_datasets
    kwargs['document_ids'] = kwargs['document_ids'].split(',') if kwargs['document_ids'] else None
    kwargs['db_queries'] = kwargs['db_queries'].split(',') if kwargs['db_queries'] else None
    usage, answer = find_datasets.main(**kwargs)
    docs = answer.pop('relevant_datasets')
    for doc in docs:
        print_separator(doc, pprint=True)
    print_separator(f'Found {len(docs)} documents, listed above from least to most relevant.')
    print_separator(answer, pprint=True)
    print_usage(usage)


@frontend.command()
@click.argument("DATASET_DOMAIN")
@click.argument("DATASET_ID")
@click.option('--target-path')
@click.option('--print-dataset', is_flag=True)
def get_dataset_dbs(print_dataset=False, **kwargs):
    from . import get_dataset_dbs
    dataset = get_dataset_dbs.main(**kwargs)
    if print_dataset:
        print_separator(dataset, pprint=True)
    for i, resource in enumerate(dataset.get('resources', [])):
        if resource.get('__db_metadata'):
            print_separator(f'Resource {i}: {resource["name"]}')
            print_separator(resource['__db_metadata'], pprint=True)
