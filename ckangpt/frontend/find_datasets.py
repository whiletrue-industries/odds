import json

from . import get_answer_from_prompt_context
from ckangpt import config, vectordb


def main(user_prompt, document_ids=None, gpt4=False, num_results=config.DEFAULT_NUM_RESULTS):
    vdb = vectordb.get_vector_db_instance()
    docs = {}
    for doc in get_answer_from_prompt_context.main(user_prompt, document_ids=document_ids, gpt4=gpt4, num_results=num_results):
        if doc.get('error'):
            raise Exception(f'Invalid doc: {doc}')
        docs[doc['id']] = doc
    collection = vdb.get_datasets_collection()
    for id, document in collection.iterate_item_documents(item_ids=list(docs.keys())):
        docs[id]['document'] = json.loads(document)
    return list(sorted(docs.values(), key=lambda d: d['relevancy']))
