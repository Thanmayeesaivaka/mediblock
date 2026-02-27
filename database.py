import os
from pymongo import MongoClient

client = MongoClient(os.environ.get("MONGO_URL"))
db = client["mediblock"]

users = db["users"]
blocks = db["blockchain"]

def add_user(user):
    users.insert_one(user)

def find_user(username, password, role):
    return users.find_one({
        "username": username,
        "password": password,
        "role": role
    })

def load_blocks():
    return list(blocks.find({}, {"_id": 0}))

def add_block(block):
    blocks.insert_one(block)