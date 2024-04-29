import json
import hashlib
from kvfile.kvfile_leveldb import KVFileLevelDB as KVFile
from ..config import config

class LLMCache():

    def __init__(self, name) -> None:
        self.log = None
        self.cache = None
        self.logfile = None
        if config.debug:
            self.logfile = open(f'{name}_llm_runner.log', 'w')
            self.log = {}
            self.cache = KVFile(location=f'{name}_llm_runner.cache')

    def store_log(self, conversation, prompts):
        if self.log is not None:
            o = self.log
            for x in conversation:
                o = o.setdefault(x, {})
            o = o.setdefault('@', [])
            for p in prompts:
                o.append(f'>>> {p[0]}\n{p[1]}')

    def store_error(self, conversation):
        self.store_log(conversation, [('assistant', 'ERROR')])

    def aux_log_writer(self, o, breadcrumbs=''):
        if '@' in o:
            self.logfile.write(f'{breadcrumbs}:\n')
            self.logfile.write('\n'.join(o['@']))
            self.logfile.write('\n')
            for k, v in o.items():
                if k != '@' and isinstance(v, dict):
                    self.aux_log_writer(v, f'{breadcrumbs}.{k}')

    def dump_log(self):
        if self.logfile:
            for k in self.log.keys():
                self.aux_log_writer(self.log[k])
            self.logfile.close()

    def cache_key(self, request):
        key = json.dumps(request, sort_keys=True)
        key = hashlib.md5(key.encode()).hexdigest()
        return key

    def get_cache(self, request):
        if self.cache is not None:
            key = self.cache_key(request)
            value = self.cache.get(key, default=None)
            if value is not None:
                return value
        return None

    def set_cache(self, request, content):
        if self.cache is not None:
            key = self.cache_key(request)
            self.cache.set(key, content)