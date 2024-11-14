import os
from typing import Coroutine
import httpx

from .config import config, CACHE_DIR
from .datatypes import Resource
from .retry import Retry
from .realtime_status import realtime_status as rts

from io import StringIO
import csv

TEMP_RESOURCE_DIR = CACHE_DIR / 'socrata-resource-temp'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:124.0) Gecko/20100101 Firefox/124.0'
}
ONGOING_SUFFIX = '.ongoing'


class WebsiteResource(Resource):

    def __init__(self, *args, **kwargs) -> None:
        kwargs['kind'] = 'website'
        super().__init__(*args, **kwargs)

