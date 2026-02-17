import os
from pymongo import MongoClient

# Connect Cloud MongoDB
client = MongoClient(os.environ.get("MONGO_URL"))
db = client["mediblock"]

users = db["users"]
blocks = db["blocks"]

# ---------------- USERS ---------------- #

def add_user(user):
    users.insert_one(user)

def find_user(username, password, role):
    return users.find_one({
        "username": username,
        "password": password,
        "role": role
    })

# ---------------- BLOCKCHAIN ---------------- #

def load_blocks():
    return list(blocks.find({}, {"_id": 0}))

def save_block(block):
    blocks.insert_one(block)
