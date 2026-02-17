import hashlib
import json
from datetime import datetime
from database import load_blocks, add_block

# Create hash for a block
def calculate_hash(index, patient, doctor, diagnosis, prescription, timestamp, previous_hash):
    block_string = f"{index}{patient}{doctor}{diagnosis}{prescription}{timestamp}{previous_hash}"
    return hashlib.sha256(block_string.encode()).hexdigest()


# Create new medical record block
def create_block(patient, doctor, diagnosis, prescription):

    blocks = load_blocks()
    index = len(blocks) + 1
    timestamp = str(datetime.now())

    if len(blocks) == 0:
        previous_hash = "0"   # Genesis block
    else:
        previous_hash = blocks[-1]["hash"]

    block_hash = calculate_hash(index, patient, doctor, diagnosis, prescription, timestamp, previous_hash)

    block = {
        "index": index,
        "patient": patient,
        "doctor": doctor,
        "diagnosis": diagnosis,
        "prescription": prescription,
        "timestamp": timestamp,
        "previous_hash": previous_hash,
        "hash": block_hash
    }

    add_block(block)
    return block


# Verify blockchain integrity
def verify_chain():
    blocks = load_blocks()

    for i in range(1, len(blocks)):
        current = blocks[i]
        previous = blocks[i - 1]

        recalculated_hash = calculate_hash(
            current["index"],
            current["patient"],
            current["doctor"],
            current["diagnosis"],
            current["prescription"],
            current["timestamp"],
            current["previous_hash"]
        )

        if current["hash"] != recalculated_hash:
            return False

        if current["previous_hash"] != previous["hash"]:
            return False

    return True
