import click
from ckangpt import common


@click.group()
def backend():
    pass


@backend.command()
@click.argument("DATASET_DOMAIN")
@click.argument("DATASET_NAME")
@click.option('--load-from-disk', is_flag=True)
@click.option('--save-to-disk', is_flag=True)
@click.option('--save-to-storage', is_flag=True)
@click.option('--glob', is_flag=True, help="DATASET_ arguments will be treated as globs to match over all domains/datasets in storage")
@click.option('--limit', type=int)
def describe_dataset(glob=False, **kwargs):
    from . import describe_dataset
    if glob:
        for desc in describe_dataset.main_glob(**kwargs):
            common.print_separator(desc, pprint=True)
    else:
        common.print_separator(describe_dataset.main(**kwargs), pprint=True)


@backend.command()
@click.argument("DATASET_DOMAIN")
@click.argument("DATASET_NAME")
@click.option('--load-from-disk', is_flag=True)
@click.option('--save-to-disk', is_flag=True)
@click.option('--save-to-storage', is_flag=True)
@click.option('--glob', is_flag=True, help="DATASET_ arguments will be treated as globs to match over all domains/datasets in storage")
@click.option('--limit', type=int)
@click.option('--force-update', is_flag=True)
@click.option('--collection-name', type=str)
def index_dataset(glob=False, **kwargs):
    from . import index_dataset
    if glob:
        for desc in index_dataset.main_glob(**kwargs):
            common.print_separator(desc, pprint=True)
    else:
        common.print_separator(index_dataset.main(**kwargs), pprint=True)


@backend.command()
@click.argument('DOMAIN')
@click.option('--limit', type=int)
@click.option('--save-to-disk', is_flag=True)
@click.option('--save-to-storage', is_flag=True)
@click.option('--glob', is_flag=True, help="DOMAIN argument will be treated as a glob to match over all known domains")
@click.option('--force', is_flag=True, help="To ensure consistent data in storage, save to storage will only work from CI, pass --force to run it anyway")
def scrape_ckan_instance(**kwargs):
    from . import scrape_ckan_instance
    scrape_ckan_instance.main(**kwargs)
