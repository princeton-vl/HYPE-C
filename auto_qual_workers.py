import argparse
import simpleamt.simpleamt as simpleamt
from pymongo import MongoClient
import time
import botocore.exceptions
from datetime import datetime

if __name__ == '__main__':
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    args = parser.parse_args()

    mtc = simpleamt.get_mturk_connection_from_args(args)
    dbc = MongoClient('localhost:27017')
    if args.sandbox:
        db = dbc.gmm_sandbox
    else:
        db = dbc.gmm

    all_hits = {}
    cursor = db.evaluations.find({})
    for document in cursor:
        all_hits[document["hit_id"]
                 ] = document["evaluation_properties"]["hit_properties"]["QualificationId"]

    assignment_ids = []
    delay_mult = 1.0
    while True:
        try:
            for hit_id, qual_id in all_hits.items():
                paginator = mtc.get_paginator('list_assignments_for_hit')
                for a_page in paginator.paginate(HITId=hit_id, AssignmentStatuses=['Submitted'], PaginationConfig={'PageSize': 100}):
                    for a in a_page['Assignments']:
                        if a['AssignmentId'] not in assignment_ids:
                            mtc.associate_qualification_with_worker(QualificationTypeId=qual_id,
                                                                    WorkerId=a['WorkerId'],
                                                                    IntegerValue=1,
                                                                    SendNotification=False)
                            assignment_ids.append(a['AssignmentId'])
                            print("New assignment! Hit ID: %s, Assignment ID: %s" % (
                                hit_id, a['AssignmentId']))
                            print(datetime.now())
                time.sleep(0.5 * delay_mult)
        except botocore.exceptions.ClientError:
            delay_mult = delay_mult * 2.0
            print("Hit rate limit, increasing delay.")
        except Exception as e:
            print(e)

        if delay_mult > 1.0:
            delay_mult = delay_mult * 0.75
        if delay_mult < 1.0:
            delay_mult = 1.0
