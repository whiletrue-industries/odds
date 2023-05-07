import openai

from . import get_vector_db_query
from ckangpt import chroma, config


def main(query, from_user_prompt=False, gpt4=False, num_results=config.DEFAULT_NUM_RESULTS):
    if from_user_prompt:
        query = get_vector_db_query.main(query, gpt4)
    _, collection = chroma.get_datasets_collection()
    words = [w.strip() for w in query['words']]
    ckan_instance = {
        'UK': 'https://data.gov.uk',
        'IL': 'https://data.gov.il',
    }.get(query['country']) if query.get('country') else None
    where = {}
    if ckan_instance:
        where['ckan_instance'] = ckan_instance
    embeddings = [e['embedding'] for e in openai.Embedding.create(input=[', '.join(words)], engine="text-embedding-ada-002")['data']]
    results = collection.query(
        query_embeddings=embeddings,
        n_results=num_results,
        include=["metadatas", "documents"],
        # where causes a crash in Chroma sometimes
        # where=where if where else None,
    )
    all_documents = {}
    for word, ids, documents, metadatas in zip(words, results['ids'], results['documents'], results['metadatas']):
        for id, document, metadata in zip(ids, documents, metadatas):
            if id not in all_documents:
                all_documents[id] = {
                    'id': id,
                    'metadata': metadata,
                    'document': document,
                    'words': set(),
                }
            all_documents[id]['words'].add(word)
    return list(all_documents.values())
