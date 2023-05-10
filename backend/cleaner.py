from typing import List, TypedDict
from bson.objectid import ObjectId
import pandas as pn
from functionalities import service_db


""" First Step """
def create_subtype(name: str, subtypes: List[str] = []):
    return {
        "name": name,
        "subtypes": subtypes
    }


services = [
    {
        "serviceId": 1,
        "title": "cook",
        "type": "cooking",
        "subtypes": [
            create_subtype("indian", ["south indian", "north indian"]), create_subtype(
                "chinese"), create_subtype("italian"), create_subtype("french")
        ]
    },
    {
        "serviceId": 3,
        "title": "driver",
        "type": "driving",
        "subtypes": [create_subtype("short route driving"), create_subtype("long route driving")]
    },
    {
        "serviceId": 2,
        "title": "guard",
        "type": "guarding",
        "subtypes": [create_subtype("morning time guard"), create_subtype("day time guard"), create_subtype("night time guard"), create_subtype("lift guard")]
    },
    {
        "serviceId": 4,
        "title": "maid",
        "type": "maid",
        "subtypes": [create_subtype("cleaning maid"), create_subtype("sweeper"), create_subtype("cooking maid")]
    },
    {
        "serviceId": 5,
        "title": "repair",
        "type": "repair",
        "subtypes": [create_subtype("electrician"), create_subtype("plumber")]
    },
]


service_db['services'].drop()

service_db['services'].insert_many(services)


""" Second Step """

ratings: pn.DataFrame = pn.read_csv("info/rating.csv")
ratings = ratings.loc[:, ['userId', 'serviceId', 'rating']]

ratings['serviceId'] = (ratings['serviceId'] % 5) + 1
ratings["userId"] = ratings['userId'].apply(str)


service_db['ratings'].drop()
service_db['ratings'].insert_many(ratings.to_dict('records'))
