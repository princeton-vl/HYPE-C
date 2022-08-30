import argparse
import json

import os
import random
import simpleamt.simpleamt as simpleamt
import benchmark_utils
import copy

from pymongo import MongoClient

from datetime import datetime

if __name__ == '__main__':
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    parser.add_argument('--eval_properties',
                        type=argparse.FileType('r'), required=True)
    parser.add_argument('--eval_name', type=str, required=True)
    parser.add_argument('--html_template', required=True)
    args = parser.parse_args()

    mtc = simpleamt.get_mturk_connection_from_args(args)
    dbc = MongoClient('localhost:27017')

    if args.sandbox:
        db = dbc.gmm_sandbox
    else:
        db = dbc.gmm

    assert(db.evaluations.count_documents(
        {"evaluation_name": args.eval_name}, limit=1) == 0)

    eval_properties = json.load(args.eval_properties)

    eval_properties["dataset_properties"]["real_dir"] = os.path.abspath(
        eval_properties["dataset_properties"]["real_dir"])
    eval_properties["dataset_properties"]["fake_dir"] = os.path.abspath(
        eval_properties["dataset_properties"]["fake_dir"])

    dataset_properties = eval_properties["dataset_properties"]
    hit_properties = copy.deepcopy(eval_properties["hit_properties"])

    hit_properties['Reward'] = str(hit_properties['Reward'])
    simpleamt.setup_qualifications(hit_properties, mtc)

    frame_height = hit_properties.pop('FrameHeight')
    env = simpleamt.get_jinja_env(args.config)
    template = env.get_template(args.html_template)

    anon_links = benchmark_utils.upload_anon_images(dataset_properties["real_dir"],
                                                    dataset_properties["fake_dir"],
                                                    dataset_properties["bucket_name"],
                                                    dataset_properties["bucket_region"],
                                                    args.config.get(
                                                        'aws_access_key'),
                                                    args.config.get('aws_secret_key'))

    answer_key = []
    answer_key += [(val[0], val[1], "real") for val in anon_links["real"]]
    answer_key += [(val[0], val[1], "fake") for val in anon_links["fake"]]

    all_links = [val[1] for val in anon_links["real"]] + [val[1]
                                                          for val in anon_links["fake"]]
    random.shuffle(all_links)

    template_params = {
        'description': hit_properties['Description'], 'input': json.dumps(all_links)}
    html_doc = template.render(template_params)
    html_question = '''
    <HTMLQuestion xmlns="http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2011-11-11/HTMLQuestion.xsd">
      <HTMLContent>
        <![CDATA[
          <!DOCTYPE html>
          %s
        ]]>
      </HTMLContent>
      <FrameHeight>%d</FrameHeight>
    </HTMLQuestion>
  ''' % (html_doc, frame_height)
    hit_properties['Question'] = html_question
    hit_properties['UniqueRequestToken'] = str(datetime.now())

    launched = False
    while not launched:
        try:
            boto_hit = mtc.create_hit(**hit_properties)
            launched = True
        except Exception as e:
            print(e)
    hit_id = boto_hit['HIT']['HITId']

    output = {"evaluation_properties": eval_properties, "hit_id": hit_id,
              "evaluation_name": args.eval_name, "answer_key": answer_key}

    db.evaluations.insert_one(output)

    print('Launched HIT ID: %s' % hit_id)
