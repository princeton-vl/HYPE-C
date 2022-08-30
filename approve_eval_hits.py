import argparse
import simpleamt.simpleamt as simpleamt
from pymongo import MongoClient
import time

if __name__ == '__main__':
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    parser.add_argument('-f', action='store_true', default=False)
    args = parser.parse_args()

    mtc = simpleamt.get_mturk_connection_from_args(args)
    dbc = MongoClient('localhost:27017')
    if args.sandbox:
        db = dbc.gmm_sandbox
    else:
        db = dbc.gmm

    approve_assignments = []
    reject_assignments = []
    submitted_assignments = db.assignments.find(
        {"assignment_status": "Submitted"})

    total_assignments = 0
    total_bonus = 0.0
    for assignment in submitted_assignments:
        total_assignments += 1
        if assignment["valid_result"] and not assignment["duplicate"]:
            evaluation = db.evaluations.find_one(
                {"_id": assignment["evaluation_id"]})
            correct_count = db.labels.count_documents(
                {"assignment_id": assignment["assignment_id"], "correct": True})
            bonus = correct_count * \
                evaluation["evaluation_properties"]["approval_properties"]["correct_bonus"]
            total_bonus += bonus
            print("Assignment %s correct count: %d, bonus: %f" %
                  (assignment["assignment_id"], correct_count, bonus))

            approve_assignments.append((assignment, bonus))
        else:
            if assignment["duplicate"]:
                print("Duplicate found, rejecting.")
            reject_assignments.append(assignment)

    print("Total assignments: %d" % total_assignments)
    print("This will approve %d assignments, providing bonuses totaling $%f, and reject %d assignments with sandbox %s" % (
        len(approve_assignments), total_bonus, len(reject_assignments), str(args.sandbox)))
    print('Continue?')

    if not args.f:
        s = input('(Y/N): ')
    else:
        s = 'Y'
    if s == 'Y' or s == 'y':
        print('Approving assignments')
        for idx, pair in enumerate(approve_assignments):
            print('Approving assignment %d / %d' %
                  (idx + 1, len(approve_assignments)))
            mtc.approve_assignment(AssignmentId=pair[0]['assignment_id'])
            if pair[1] > 0:
                mtc.send_bonus(WorkerId=pair[0]['worker_id'],
                               BonusAmount="{:.2f}".format(pair[1]),
                               AssignmentId=pair[0]['assignment_id'],
                               Reason='Correct answer bonus.',
                               UniqueRequestToken=(pair[0]['assignment_id'] + pair[0]['worker_id']))

            db.assignments.update_one({'_id': pair[0]['_id']}, {
                                      "$set": {"assignment_status": "Approved"}})
            time.sleep(0.25)

        for idx, assignment in enumerate(reject_assignments):
            print('Rejecting assignment %d / %d' %
                  (idx + 1, len(reject_assignments)))
            if assignment["duplicate"]:
                mtc.reject_assignment(
                    AssignmentId=assignment['assignment_id'], RequesterFeedback='Duplicate assignment.')
            else:
                mtc.reject_assignment(
                    AssignmentId=assignment['assignment_id'], RequesterFeedback='Invalid results.')

            mtc.create_additional_assignments_for_hit(
                HITId=assignment['hit_id'],
                NumberOfAdditionalAssignments=1
            )
            db.assignments.update_one({'_id': assignment["_id"]}, {
                                      "$set": {"assignment_status": "Rejected"}})
            time.sleep(0.25)
    else:
        print('Aborting')
