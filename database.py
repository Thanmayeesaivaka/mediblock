from pymongo import MongoClient

# Connect MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["mediblock"]

users_col = db["users"]
blocks_col = db["blockchain"]

# ---------------- USERS ---------------- #

def add_user(user):
    users_col.insert_one(user)

def load_users():
    return list(users_col.find({}, {"_id":0}))

def find_user(username, password, role):
    return users_col.find_one(
        {"username": username, "password": password, "role": role},
        {"_id":0}
    )

# ---------------- BLOCKCHAIN RECORDS ---------------- #

def load_blocks():
    return list(blocks_col.find({}, {"_id":0}))

def save_blocks(blocks):
    blocks_col.delete_many({})
    if blocks:
        blocks_col.insert_many(blocks)

def add_block(block):
    blocks_col.insert_one(block)
