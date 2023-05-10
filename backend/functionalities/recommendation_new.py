from typing import List
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
import numpy as np
import pandas as pd
from pymongo.typings import _DocumentType
from queue import Queue
import sklearn
from .logger import logger
from .database import service_db


services_cursor = service_db["services"].find()
ratings_cursor = service_db["ratings"].find()

services = pd.DataFrame(list(services_cursor))
del services['_id']
ratings = pd.DataFrame((list(ratings_cursor)))
del ratings['_id']


user_freq = ratings[['userId', 'serviceId']].groupby(
    'userId').count().reset_index()
user_freq.columns = ['userId', 'n_ratings']


def create_matrix(df):

    N = len(df['userId'].unique())
    M = len(df['serviceId'].unique())

    # Map Ids to indices
    user_mapper = dict(zip(np.unique(df["userId"]), list(range(N))))
    service_mapper = dict(zip(np.unique(df["serviceId"]), list(range(M))))

    # Map indices to IDs
    user_inv_mapper = dict(zip(list(range(N)), np.unique(df["userId"])))
    service_inv_mapper = dict(zip(list(range(M)), np.unique(df["serviceId"])))

    user_index = [user_mapper[i] for i in df['userId']]
    movie_index = [service_mapper[i] for i in df['serviceId']]

    X = csr_matrix((df["rating"], (movie_index, user_index)), shape=(M, N))

    return X, user_mapper, service_mapper, user_inv_mapper, service_inv_mapper


sprarse_matrix, user_mapper, service_mapper, user_inv_mapper, service_inv_mapper = create_matrix(
    ratings)


def find_similar_services(service_id, X, k, metric='cosine'):

    neighbour_ids = []

    service_ind = service_mapper[service_id]
    service_vec = X[service_ind]
    k += 1
    kNN = NearestNeighbors(n_neighbors=k, algorithm="brute", metric=metric)
    kNN.fit(X)
    service_vec = service_vec.reshape(1, -1)
    neighbour = kNN.kneighbors(service_vec, return_distance=False)
    for i in range(0, k):
        n = neighbour.item(i)
        neighbour_ids.append(service_inv_mapper[n])
    neighbour_ids.pop(0)
    return neighbour_ids


def get_subtypes(item: _DocumentType):
    subtypes = []

    runner_queue = Queue()
    runner_queue.put(item)
    while not runner_queue.empty():
        queue_item = runner_queue.get(False)

        if 'subtypes' in queue_item:
            for temp in queue_item['subtypes']:
                print(temp)
                if isinstance(temp, str):
                    subtypes.append(temp)
                elif ("subtypes" in temp and len(temp['subtypes']) == 0):
                    subtypes.append(temp['name'])
                else:
                    runner_queue.put(temp)
    return subtypes


def recommend_similar(service_type: str, similar_service_count: int = 0):
    cursor = service_db['services'].find_one({'type': service_type})
    if cursor != None:
        id = cursor['serviceId']
        name = cursor['type']
        subtypes: List[str] = get_subtypes(cursor)
        similar_service_ids = find_similar_services(
            id, sprarse_matrix, k=similar_service_count)
        subtype_prefixed = list(
            map(lambda x: name + " / " + x, subtypes))

        for similar_id in similar_service_ids:
            similar_service_cursor = service_db['services'].find_one(
                {"serviceId": int(similar_id)})
            if similar_service_cursor != None:
                similar_subtypes = get_subtypes(similar_service_cursor)
                prefixed_similar_subtypes = list(
                    map(lambda x: similar_service_cursor['type'] + " / " + x, similar_subtypes))
                subtype_prefixed.extend(prefixed_similar_subtypes)

        return {
            "id": id,
            "service": name,
            "recommendations": subtype_prefixed
        }

    return {
        "id": 0,
        "service": service_type,
        "recommendations": []
    }
