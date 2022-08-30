import argparse
import json

import simpleamt.simpleamt as simpleamt
from pymongo import MongoClient

import sys
import os
import re


def process_assignments(mtc, hit_id, status):
    results = []
    paginator = mtc.get_paginator('list_assignments_for_hit')
    try:
        for a_page in paginator.paginate(HITId=hit_id, PaginationConfig={'PageSize': 100}):
            for a in a_page['Assignments']:
                if a['AssignmentStatus'] not in status:
                    continue
                valid_result = True
                try:
                    answer = json.loads(
                        re.search(r'<FreeText>(?P<answer>.*?)</FreeText>', a['Answer'])['answer'])
                except ValueError as e:
                    answer = []
                    valid_result = False
                results.append({
                    'assignment_id': a['AssignmentId'],
                    'hit_id': hit_id,
                    'worker_id': a['WorkerId'],
                    'assignment_status': a['AssignmentStatus'],
                    'answers': answer,
                    'valid_result': valid_result,
                    'submit_time': a['SubmitTime'],
                })
    except mtc.exceptions.RequestError:
        print('Bad hit_id %s' % str(hit_id), file=sys.stderr)
        return results

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    args = parser.parse_args()

    mtc = simpleamt.get_mturk_connection_from_args(args)
    dbc = MongoClient('localhost:27017')

    if args.sandbox:
        db = dbc.gmm_sandbox
    else:
        db = dbc.gmm

    status = ['Approved', 'Submitted', 'Rejected']

    all_evaluations = db.evaluations.find({})
    for evaluation in all_evaluations:
        results = process_assignments(mtc, evaluation["hit_id"], status)
        for result in results:
            if db.assignments.count_documents({"assignment_id": result["assignment_id"]}, limit=1) == 0:

                mtc.associate_qualification_with_worker(QualificationTypeId=evaluation["evaluation_properties"]["hit_properties"]["QualificationId"],
                                                        WorkerId=result['worker_id'],
                                                        IntegerValue=1,
                                                        SendNotification=False)

                result["duplicate"] = False
                for sibling_evaluation in db.evaluations.find({"evaluation_properties.hit_properties.QualificationId": evaluation["evaluation_properties"]["hit_properties"]["QualificationId"]}):

                    if db.assignments.count_documents({"hit_id": sibling_evaluation["hit_id"], "worker_id": result["worker_id"]}, limit=1) != 0:
                        result["duplicate"] = True
                        break

                result["evaluation_id"] = evaluation["_id"]
                db.assignments.insert_one(result)
                if result["valid_result"]:
                    answer_key = {val[1]: (val[2], val[0])
                                  for val in evaluation['answer_key']}
                    for answer in result['answers']:
                        label = {"evaluation_id": evaluation["_id"],
                                 "hit_id": evaluation["hit_id"],
                                 "assignment_id": result["assignment_id"],
                                 "worker_id": result["worker_id"],
                                 "image_url": answer["image_url"],
                                 "abs_path": os.path.abspath(answer_key[answer["image_url"]][1]),
                                 "filename": os.path.basename(answer_key[answer["image_url"]][1]),
                                 "human_label": answer["label"],
                                 "true_label": answer_key[answer["image_url"]][0],
                                 "correct": (answer["label"] == answer_key[answer["image_url"]][0])
                                 }
                        db.labels.insert_one(label)
            else:
                db.assignments.update_one({'assignment_id': result['assignment_id']}, {
                                          "$set": {"assignment_status": result["assignment_status"]}})

    # Check which evaluations are complete
    all_evaluations = db.evaluations.find({})
    for evaluation in all_evaluations:
        complete_count = db.assignments.count_documents(
            {"evaluation_id": evaluation["_id"], "duplicate": False, "assignment_status": "Approved"})
        max_assignments = evaluation["evaluation_properties"]["hit_properties"]["MaxAssignments"]
        if complete_count >= max_assignments:
            complete = True
        else:
            complete = False

        db.evaluations.update_one({'_id': evaluation["_id"]}, {
                                  "$set": {"complete": complete}})

    print("Done.")
