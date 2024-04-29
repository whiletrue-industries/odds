import yaml
from pathlib import Path

from .config import Config


FILE_PATH = Path(__file__).parent.parent.parent.parent / 'odds.config.yaml'


class YAMLConfig(Config):

    def __init__(self, file_path=FILE_PATH):
        self.file_path = file_path
        self.config = self.load_config()

    def load_config(self):
        with open(self.file_path, 'r') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    def get(self, key):
        return self.config.get(key, None)

