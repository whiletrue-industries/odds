import json

from . import get_answer_from_prompt_context
from ckangpt import config, vectordb


def main(user_prompt, document_ids=None, num_results=config.DEFAULT_NUM_RESULTS):
    vdb = vectordb.get_vector_db_instance()
    usage, answer = get_answer_from_prompt_context.main(user_prompt, document_ids=document_ids, num_results=num_results)
    docs = {}
    for doc in answer['relevant_datasets']:
        docs[doc['id']] = doc
    collection = vdb.get_datasets_collection()
    item_ids = list(docs.keys())
    if len(item_ids) > 0:
        for id, document in collection.iterate_item_documents(item_ids=list(docs.keys())):
            docs[id]['document'] = json.loads(document)
        return usage, {
            **answer,
            'relevant_datasets': list(sorted(docs.values(), key=lambda d: d['relevancy'])),
        }
    else:
        return usage, answer
