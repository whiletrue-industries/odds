import click


@click.group()
def utils():
    pass


@utils.command()
@click.argument('COLLECTION_NAME')
@click.option('--limit', help='Limit the number of datasets to convert, for testing only.', type=int)
@click.option('--force', is_flag=True, help='Allows to overwrite the default collection. This will cause downtime for anyone currently using the app.')
@click.option('--continue', is_flag=True, help='Continue from the last dataset.')
@click.option('--debug', is_flag=True)
def convert_poc_to_chroma_db(collection_name, **kwargs):
    from . import convert_poc_to_chroma_db
    kwargs['continue_from_last'] = kwargs.pop('continue')
    convert_poc_to_chroma_db.main(collection_name, **kwargs)


@utils.command()
def compress_chroma_db():
    from . import compress_chroma_db
    compress_chroma_db.main()


@utils.command()
def download_chroma_db():
    from . import download_chroma_db
    download_chroma_db.main()


@utils.command()
@click.argument('search', required=False, default=None)
def list_datasets(search):
    from .datasets import list_datasets
    for id in list_datasets():
        if search is None or search in id:
            print(id)


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
