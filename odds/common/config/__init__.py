from .config import Config
from ..select import select

from .yaml_config import YAMLConfig

config: Config = select('Config', locals())()