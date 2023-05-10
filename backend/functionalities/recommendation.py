import datetime
from typing import Dict
from fuzzywuzzy import fuzz
from sklearn.neighbors import NearestNeighbors
from scipy.sparse import csr_matrix
import pandas as pd
from .logger import logger
from .database import service_db

# Load the data

services_cursor = service_db["services"].find()
ratings_cursor = service_db["ratings"].find()


services = pd.DataFrame(list(services_cursor))
del services['_id']
ratings = pd.DataFrame((list(ratings_cursor)))
del ratings['_id']


# Filter the services to only include the most popular services
service_count = ratings.groupby(
    'serviceId').size().sort_values(ascending=False)
popular_services = list(service_count[service_count >= 10].index)
ratings = ratings[ratings['serviceId'].isin(popular_services)]


# Create a pivot table of user ratings for each service
item_user_mat: pd.DataFrame = ratings.pivot_table(
    index='serviceId', columns='userId', values='rating').fillna(0)

# Create a sparse matrix for more efficient calculations
item_user_mat_sparse = csr_matrix(item_user_mat.values)

# Create a mapper which maps service index and its title
service_to_index = {
    serviceName: i for i, serviceName in enumerate(list(services.set_index('serviceId').loc[item_user_mat.index]['type']))
}


# Define the recommendation model
recommendation_model = NearestNeighbors(
    metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)
recommendation_model.fit(item_user_mat_sparse)

# Define a function to perform fuzzy service name matching


def fuzzy_service_name_matching(input_str, mapper, print_matches):
    # match_service is list of tuple of 3 values(service_name,index,fuzz_ratio)
    match_service = []
    for service, ind in mapper.items():
        current_ratio = fuzz.ratio(service.lower(), input_str.lower())
        if (current_ratio >= 15):
            match_service.append((service, ind, current_ratio))

    # sort the match_service with respect to ratio
    match_ = sorted(match_service, key=lambda x: x[2])[::-1]

    if print_matches:
        logger.debug('Top matches for %s: %s',
                     input_str, [x[0] for x in match_])

    return match_


def recommend(service: str) -> Dict:
    try:
        logger.debug(f"services:\n{services}")
        logger.debug(f"ratings:\n{ratings}")

        keyword = service.lower()
        # Create a mapping of keywords to service types
        keyword_mapping = {
            'cooking': ['Indian', 'Chinese', 'Italian'],
            'cleaning': ['House Cleaning', 'Office Cleaning', 'Carpet Cleaning']
            # Add more keywords and service types as needed
        }

        # Check if any of the keywords match the mapped service types
        service_types = []
        if keyword in keyword_mapping:
            service_types.extend(keyword_mapping[keyword])

        if len(service_types) == 0:
            print("no available service types")
            return {
                "service": service,
                "recommendations": []
            }
        else:
            # Get the indices of the services that match the selected service types
            indices = []
            for service_type in service_types:
                logger.debug(f"before extending indices\n{indices}")
                indices.extend(
                    item_user_mat.index[item_user_mat['subtype'] == service_type].tolist())
                logger.debug(f"after extending indices\n{indices}")

            # Remove duplicates and find the nearest neighbors
            indices = list(set(indices))
            distances, indices = recommendation_model.kneighbors(
                item_user_mat_sparse[indices], n_neighbors=3)
            recommended_services = []
            for i in indices[0]:
                service_id = item_user_mat.index[i]
                recommended_services.append(
                    services[services['serviceId'] == service_id]['subtype'].values[0])
            logger.debug('Recommended services for %s: %s',
                         service, recommended_services)
            return {'service': service, 'recommendations': recommended_services}
    except Exception as e:
        logger.error(e)
        return {'service': service, 'recommendations': []}


# run this to transfer csv data to mongodb
if __name__ == '__main__':
    services_dict = services.to_dict("records")
    ratings_dict = ratings.fillna("").to_dict("records")

    # with open('format.json', "w+") as f:
    #     f.write(json.dumps({
    #         'ratings': ratings_dict,
    #         'services': services_dict
    #     }))

    service_db['ratings'].insert_many(ratings_dict)
    service_db['services'].insert_many(services_dict)
