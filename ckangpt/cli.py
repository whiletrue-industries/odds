import click
import dotenv
import importlib


dotenv.load_dotenv()


@click.group()
def main():
    pass


for submodule in [
    'frontend',
    'backend',
    'utils',
]:
    main.add_command(getattr(importlib.import_module(f"ckangpt.{submodule}.cli"), submodule))


if __name__ == "__main__":
    main()
