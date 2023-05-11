import click
import dotenv
import importlib

from . import config


dotenv.load_dotenv()


@click.group()
@click.option('--gpt4', is_flag=True)
@click.option('--no-cache', is_flag=True)
@click.option('--clear-cache', is_flag=True)
@click.option('--debug', is_flag=True)
def main(gpt4, no_cache, clear_cache, debug):
    if clear_cache:
        import shutil, platformdirs
        shutil.rmtree(platformdirs.user_cache_dir("guidance"))
    if gpt4:
        config.USE_GPT4 = True
    if no_cache:
        config.ENABLE_CACHE = False
    if debug:
        config.ENABLE_DEBUG = True


for submodule in [
    'frontend',
    'backend',
    'utils',
]:
    main.add_command(getattr(importlib.import_module(f"ckangpt.{submodule}.cli"), submodule))


if __name__ == "__main__":
    main()
