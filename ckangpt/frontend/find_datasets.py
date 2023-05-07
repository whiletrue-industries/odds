import json

from . import get_answer_from_prompt_context
from ckangpt import chroma, config


def main(user_prompt, document_ids=None, gpt4=False, num_results=config.DEFAULT_NUM_RESULTS):
    docs = {}
    for doc in get_answer_from_prompt_context.main(user_prompt, document_ids=document_ids, gpt4=gpt4, num_results=num_results):
        if doc.get('error'):
            raise Exception(f'Invalid doc: {doc}')
        docs[doc['id']] = doc
    _, collection = chroma.get_datasets_collection()
    results = collection.get(ids=list(docs.keys()))
    for id, document in zip(results['ids'], results['documents']):
        docs[id]['document'] = json.loads(document)
    return list(sorted(docs.values(), key=lambda d: d['relevancy']))
