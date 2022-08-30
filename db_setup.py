import pymongo
from pymongo import MongoClient


if __name__ == '__main__':
    client = MongoClient('localhost:27017')

    db = client.gmm
    evaluations = db.evaluations
    evaluations.create_index("hit_id", unique=True)
    evaluations.create_index("evaluation_name", unique=True)
    evaluations.create_index(
        "evaluation_properties.hit_properties.QualificationId")

    assignments = db.assignments
    assignments.create_index("assignment_id", unique=True)
    assignments.create_index("evaluation_id")
    assignments.create_index("hit_id")
    assignments.create_index("worker_id")

    labels = db.labels
    labels.create_index("evaluation_id")
    labels.create_index("hit_id")
    labels.create_index("worker_id")
    labels.create_index("assignment_id")
    labels.create_index([("hit_id", pymongo.ASCENDING),
                        ("filename", pymongo.ASCENDING)])
    labels.create_index(
        [("evaluation_id", pymongo.ASCENDING), ("filename", pymongo.ASCENDING)])

    db = client.gmm_sandbox
    evaluations = db.evaluations
    evaluations.create_index("hit_id", unique=True)
    evaluations.create_index("evaluation_name", unique=True)
    evaluations.create_index(
        "evaluation_properties.hit_properties.QualificationId")

    assignments = db.assignments
    assignments.create_index("assignment_id", unique=True)
    assignments.create_index("evaluation_id")
    assignments.create_index("hit_id")
    assignments.create_index("worker_id")

    labels = db.labels
    labels.create_index("evaluation_id")
    labels.create_index("hit_id")
    labels.create_index("worker_id")
    labels.create_index("assignment_id")
    labels.create_index([("hit_id", pymongo.ASCENDING),
                        ("filename", pymongo.ASCENDING)])
    labels.create_index(
        [("evaluation_id", pymongo.ASCENDING), ("filename", pymongo.ASCENDING)])

    print("Finished setup.")
