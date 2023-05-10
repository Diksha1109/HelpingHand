from pymongo.typings import _DocumentType
from .database import auth_db
from bson import ObjectId


class User:

    def __init__(self, id: str, email: str, username: str, first_name: str, last_name: str, phone: str):
        self.id = id
        self.email = email
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    @staticmethod
    def get_user(user_id):
        user_doc = auth_db["users"].find_one({"_id": ObjectId(user_id)})
        if user_doc == None:
            print("No user found")
            return None
        print(f"Found user:\n{user_doc}")
        return User.doc_to_user(user_doc)

    @staticmethod
    def doc_to_user(user_doc: _DocumentType):
        return User(str(user_doc["_id"]), user_doc["email"], user_doc["username"], user_doc["first_name"], user_doc["last_name"], user_doc["phone"])
