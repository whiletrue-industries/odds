import click


@click.group()
def utils():
    pass


@utils.command()
@click.option('--limit')
def convert_poc_to_chroma_db(limit):
    from . import convert_poc_to_chroma_db
    convert_poc_to_chroma_db.main(limit)


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