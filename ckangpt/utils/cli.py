import json

import click

from ckangpt import storage


@click.group()
def utils():
    pass


@utils.command()
@click.argument('COLLECTION_NAME')
@click.option('--limit', help='Limit the number of datasets to convert, for testing only.', type=int)
@click.option('--force', is_flag=True, help='Allows to overwrite the default collection. This will cause downtime for anyone currently using the app.')
@click.option('--continue', is_flag=True, help='Continue from the last dataset.')
@click.option('--debug', is_flag=True)
def convert_poc_to_vector_db(collection_name, **kwargs):
    from . import convert_poc_to_vector_db
    kwargs['continue_from_last'] = kwargs.pop('continue')
    convert_poc_to_vector_db.main(collection_name, **kwargs)


@utils.command()
def compress_chroma_db():
    from . import compress_chroma_db
    compress_chroma_db.main()


@utils.command()
def download_chroma_db():
    from . import download_chroma_db
    download_chroma_db.main()


@utils.command()
@click.argument("DATASET_DOMAIN")
@click.argument("DATASET_NAME")
@click.option('--load-from-disk', is_flag=True)
@click.option('--limit', type=int)
def list_datasets(**kwargs):
    from .datasets import list_datasets
    for domain, name, item in list_datasets(**kwargs):
        print(f"{domain}/{name}: {item['summary']} - \n\t\t{item['description'][:80]}...")


@utils.command()
@click.argument('dataset_id', required=True)
def get_datasets(dataset_id):
    from .datasets import get_dataset
    print(get_dataset(dataset_id))


@utils.command()
@click.argument('COLLECTION_NAME')
@click.option('--force', is_flag=True, help='Allows to reindex the default collection. This will cause downtime for anyone currently using the app.')
def reindex_collection(collection_name, force):
    from . import reindex_collection
    reindex_collection.main(collection_name, force)


@utils.command()
def list_collections():
    from ckangpt import vectordb
    for collection in vectordb.get_vector_db_instance().list_collections():
        print(collection.name)


@utils.command()
@click.argument("NAME")
def delete_collection(name):
    from ckangpt import vectordb
    vectordb.get_vector_db_instance().delete_collection(name)
    print('OK')


@utils.command()
@click.option('--prefix')
@click.option('--recursive', is_flag=True)
def storage_list(**kwargs):
    for item in storage.list_(**kwargs):
        print(f'- {item}')
