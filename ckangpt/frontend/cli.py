import click


@click.group()
def frontend():
    pass


@frontend.command()
@click.argument("QUERY")
@click.option('--gpt4', is_flag=True)
def find_dataset(query, gpt4):
    from . import find_dataset
    find_dataset.main(query, gpt4)
