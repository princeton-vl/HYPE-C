import argparse
import simpleamt.simpleamt as simpleamt
from pymongo import MongoClient

if __name__ == '__main__':
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    args = parser.parse_args()

    dbc = MongoClient('localhost:27017')

    if args.sandbox:
        db = dbc.gmm_sandbox
    else:
        db = dbc.gmm

    all_evaluations = db.evaluations.find({})

    for evaluation in all_evaluations:
        all_assignments = db.assignments.find(
            {"evaluation_id": evaluation["_id"], "duplicate": False})
        incorrect = 0.0
        total = 0.0
        for assignment in all_assignments:
            total += db.labels.count_documents(
                {"assignment_id": assignment["assignment_id"]})
            incorrect += db.labels.count_documents(
                {"assignment_id": assignment["assignment_id"], "correct": False})

        if total > 0:
            score = incorrect / total
        else:
            score = -1.0

        complete_count = db.assignments.count_documents(
            {"evaluation_id": evaluation["_id"], "duplicate": False, "assignment_status": "Approved"})
        max_assignments = evaluation["evaluation_properties"]["hit_properties"]["MaxAssignments"]
        if complete_count >= max_assignments:
            complete = "Completed"
        else:
            complete = "Incomplete: %d / %d" % (
                complete_count, max_assignments)

        print("%s, %f, %s" % (evaluation["evaluation_name"], score, complete))
