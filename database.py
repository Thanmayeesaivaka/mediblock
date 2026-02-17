import os
from pymongo import MongoClient

client = MongoClient(os.environ.get("MONGO_URL"))
db = client["mediblock"]
