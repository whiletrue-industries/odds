import click


@click.group()
def backend():
    pass


@backend.command()
@click.argument("QUERY")
@click.option('--gpt4', is_flag=True)
def describe_dataset(query, gpt4):
    from . import describe_dataset
    description = describe_dataset.main(query, gpt4)
    print('Description:\n', description)
