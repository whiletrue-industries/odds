import json

import tiktoken

from . import get_documents_from_vector_db
from ckangpt import vectordb, config


def get_context_str(documents, max_resources=None, with_organization=True, truncate_len=200):
    context = {}
    for id, document in documents.items():
        doc_context = {
            'Title': document.get('title'),
            'Notes': document.get('notes'),
        }
        if with_organization:
            doc_context.update({
                'Organization Title': document.get('organization', {}).get('title'),
                'Organization Description': document.get('organization', {}).get('description'),
            })
        if max_resources != 0:
            for i, resource in enumerate(document.get('resources', {}).values()):
                doc_context[f'Resource {i+1} URL'] = resource.get('url')
                doc_context[f'Resource {i+1} Name'] = resource.get('name')
                if max_resources and i+1 >= max_resources:
                    break
        doc_context_strs = []
        for title, value in doc_context.items():
            if value and value.strip():
                value = value.strip().replace('\n', ' ').replace('\r', ' ').replace('<p>', '').replace('</p>', '')[:truncate_len]
                doc_context_strs.append(f'{title}: {value}')
        if len(doc_context_strs):
            context[id] = '\n'.join(doc_context_strs)
    context_strs = []
    for id, doc_context in context.items():
        context_strs.append(f'ID: {id}\n{doc_context}')
    return '\n---\n'.join(context_strs)


def main(from_db_query=None, from_document_ids=None, from_user_prompt=None, gpt4=False, num_results=config.DEFAULT_NUM_RESULTS, max_tokens=None):
    vdb = vectordb.get_vector_db_instance()
    if not max_tokens:
        max_tokens = 6000 if gpt4 else 2500
    if from_db_query or from_user_prompt:
        assert not from_document_ids
        assert not (from_db_query and from_user_prompt)
        documents = get_documents_from_vector_db.main(
            from_user_prompt if from_user_prompt else from_db_query,
            from_user_prompt=True if from_user_prompt else False,
            gpt4=gpt4, num_results=num_results
        )
        from_document_ids = [d.id for d in documents]
    collection = vdb.get_datasets_collection()
    documents = {
        id: json.loads(document)
        for id, document
        in collection.iterate_item_documents(item_ids=from_document_ids)
    }
    encoding = tiktoken.encoding_for_model('gpt-4' if gpt4 else 'gpt-3.5-turbo')
    context = get_context_str(documents)
    if len(encoding.encode(context)) > max_tokens:
        context = get_context_str(documents, max_resources=3, with_organization=False)
        if len(encoding.encode(context)) > max_tokens:
            context = get_context_str(documents, max_resources=1, with_organization=False, truncate_len=100)
            if len(encoding.encode(context)) > max_tokens:
                context = encoding.decode(encoding.encode(context)[:max_tokens])
    return context, len(encoding.encode(context))
