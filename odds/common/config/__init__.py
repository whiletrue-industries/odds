from pathlib import Path

from .config import Config
from ..select import select

from .yaml_config import YAMLConfig

CACHE_DIR = Path(__file__).parent.parent.parent.parent / '.caches'

config: Config = select('Config', locals())()