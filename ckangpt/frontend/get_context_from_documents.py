import json

import tiktoken

from . import get_documents_from_vector_db
from ckangpt import vectordb, config, storage


def get_context_str(documents):
    context = {}
    for id, document in documents.items():
        doc_context_strs = [
            f'Summary: {document["summary"]}',
            f'Description: {document["description"]}',
        ]
        context[id] = '\n'.join(doc_context_strs)
    context_strs = []
    for id, doc_context in context.items():
        context_strs.append(f'ID: {id}\n{doc_context}')
    return '\n---\n'.join(context_strs)


def main(from_db_query=None, from_document_ids=None, from_user_prompt=None, num_results=config.DEFAULT_NUM_RESULTS, max_tokens=None, load_from_disk=False):
    vdb = vectordb.get_vector_db_instance()
    if not max_tokens:
        max_tokens = 6000 if config.USE_GPT4 else 2500
    usage = None
    if from_db_query or from_user_prompt:
        assert not from_document_ids
        assert not (from_db_query and from_user_prompt)
        usage, documents = get_documents_from_vector_db.main(
            from_user_prompt if from_user_prompt else from_db_query,
            from_user_prompt=True if from_user_prompt else False,
            num_results=num_results
        )
        from_document_ids = [d.id for d in documents]
    collection = vdb.get_datasets_collection()
    documents = {
        id: storage.load(*document, load_from_disk=load_from_disk, with_metadata=False)
        for id, document
        in collection.iterate_item_documents(item_ids=from_document_ids)
    }
    encoding = tiktoken.encoding_for_model(config.model_name())
    context = get_context_str(documents)
    if len(encoding.encode(context)) > max_tokens:
        context = encoding.decode(encoding.encode(context)[:max_tokens])
    return usage, context, len(encoding.encode(context))
