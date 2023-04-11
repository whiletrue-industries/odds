import os
import openai
import dotenv
import json
import gzip
import pickle
import numpy as np

dotenv.load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')


class Embeddings():

    def __init__(self):
        with gzip.GzipFile('datasets.json.gz', 'r') as zipped:
            self.datasets = json.load(zipped)
        with open('embeddings.pickle.bak', 'rb') as f:
            self.embeddings = pickle.load(f)
        # Create a matrix of all the embeddings
        # vector_len = len(embeddings[list(embeddings.keys())[0]])
        # self.matrix = np.zeros((len(embeddings), vector_len))
        # for i, d in enumerate(self.datasets):
        #     key = f'{d["ckan_instance"]}/{d["name"]}'
        #     if key not in embeddings:
        #         break
        #     vector = embeddings[key]
        #     # vector = vector / np.linalg.norm(vector)
        #     self.matrix[i] = vector

    def process_query(self, query):
        embedding = openai.Embedding.create(input=query, model='text-embedding-ada-002')
        embedding = embedding['data'][0]['embedding']
        embedding = np.array(embedding)
        # embedding = embedding / np.linalg.norm(embedding)
        # Find the closest vector in the matrix using the dot product
        distances = sorted([(k, np.dot(v, embedding)) for k, v in self.embeddings], key=lambda x: x[1], reverse=True)
        # Find the indexes of the closest vectors
        keys = [k for k, v in distances[:10]]
        # Return the top 10 closest vectors
        ret = []
        for k in keys:
            for d in self.datasets:
                if (d['ckan_instance'] + '/' + d['name']) == k:
                    ret.append(d)
                    break
        return ret
        


if __name__=='__main__':
    embeddings = Embeddings()
    # print(embeddings.matrix.shape)
    query = input('Query: ')
    # print(query)
    # query = 'IT contracts from 2016'
    # query = 'Can I have a cigarette at the Nottingham city hall?'
    results = embeddings.process_query(f'Dataset related to {query}')
    print('-------------------')
    for r in results:
        print(f"{r['name']} | {r['title']} | {r.get('notes', '')}"[:180].replace('\n', ' '))