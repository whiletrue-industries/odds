import os
import json
import hashlib
from kvfile.kvfile_leveldb import KVFileLevelDB as KVFile
from ..config import config, CACHE_DIR

class LLMCache():

    def __init__(self, name) -> None:
        self.log = None
        self.cache = None
        self.logfile = None
        self.cache_name = None
        if config.debug:
            self.role = os.environ.get('ROLE')
            cache_dir = CACHE_DIR
            if self.role is not None:
                cache_dir = cache_dir / self.role
            self.logfile = (cache_dir / f'{name}_llm_runner.log').open('w')
            self.log = {}
            self.cache_name = name

    def ensure_cache(self):
        if self.cache is None and self.cache_name is not None:
            location = CACHE_DIR
            if self.role is not None:
                location = location / self.role
            self.cache = KVFile(location=str(location / f'{self.cache_name}_llm_runner.cache'))
        return self.cache

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
        print('DUMPING LOG', self.logfile, len(self.log))
        if self.logfile:
            for k in self.log.keys():
                self.aux_log_writer(self.log[k])
            self.logfile.close()

    def cache_key(self, request):
        key = json.dumps(request, sort_keys=True)
        key = hashlib.md5(key.encode()).hexdigest()
        return key

    def get_cache(self, request):
        cache = self.ensure_cache()
        if cache is not None:
            key = self.cache_key(request)
            value = cache.get(key, default=None)
            if value is not None:
                return value
        return None

    def set_cache(self, request, content):
        cache = self.ensure_cache()
        if cache is not None:
            key = self.cache_key(request)
            cache.set(key, content)