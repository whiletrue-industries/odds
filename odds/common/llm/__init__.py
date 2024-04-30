import atexit
from .llm_runner import LLMRunner
from .openai.openai_llm_runner import OpenAILLMRunner
from .mistral.mistral_llm_runner import MistralLLMRunner
from ..select import select

llm_runner: LLMRunner = select('LLMRunner', locals())()

atexit.register(llm_runner.cache.dump_log)
atexit.register(llm_runner.cost_collector.print_total_usage)