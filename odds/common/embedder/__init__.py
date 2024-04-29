import atexit

from .embedder import Embedder
from .openai.openai_embedder import OpenAIEmbedder
from ..select import select

embedder: Embedder = select('Embedder', locals())()

atexit.register(embedder.print_total_usage)