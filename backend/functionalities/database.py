import pymongo


mongo = pymongo.MongoClient(
    "mongodb+srv://service-account:qRVTdh9S9ePGMggA@suggesta-service.smd4qyy.mongodb.net/?retryWrites=true&w=majority")
service_db = mongo['suggesta_service']
auth_db = mongo['auth']
