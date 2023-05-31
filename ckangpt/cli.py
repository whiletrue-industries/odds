import click
import dotenv
import importlib

import guidance.llms


dotenv.load_dotenv()


from . import config


@click.group()
@click.option('--gpt4', is_flag=True)
@click.option('--no-cache', is_flag=True)
@click.option('--clear-cache', is_flag=True)
@click.option('--debug', is_flag=True)
def main(gpt4, no_cache, clear_cache, debug):
    if clear_cache:
        guidance.llms.OpenAI.cache.clear()
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
