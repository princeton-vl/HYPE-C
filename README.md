
# HYPE-C: Evaluating Image Completion Models Through Standardized Crowdsourcing

This repository is the official implementation of HYPE-C: Evaluating Image Completion Models Through Standardized Crowdsourcing.

## Requirements

Management and collection of HYPE-C evaluations requires a working local MongoDB installation. Installation instructions for MongoDB can be found [here.](https://www.mongodb.com/docs/manual/installation/)

A HYPE-C Conda environment can be created via:

```setup
conda env create -f requirements.yaml
```

Finally, HYPE-C requires a [Mechanical Turk requester account](https://requester.mturk.com/) and uses [Amazon S3](https://aws.amazon.com/s3/) for data storage.

## Configuration

### Amazon

An Amazon AWS access key and secret key is required to manage HITs. New access keys can be created through the 
[AWS console](https://console.aws.amazon.com/iam/home?#security_credential). If using an IAM user with limited permissions, the user must have access to both Amazon Mechanical Turk as well as Amazon S3.

Place both the access and secret keys in a file named config.json, written as:

```
{
  "aws_access_key": "XXXXXXXXX",
  "aws_secret_key": "XXXXXXXXX"
}
```

### Qualification and HIT Properties

Qualification tests are configured using a .json file with the template:

```
{
  "dataset_properties": {
    "real_dir": "../datasets/qualification_sets/real",
    "fake_dir": "../datasets/qualification_sets/fake",
    "bucket_name": "mybucket",
    "bucket_region": "us-east-1"
  },
  "test_properties": {
    "Name": "Image Label Qualification Test",
    "Description": "Decide whether each image is a real photograph or a computer generated fake.",
    "Keywords": "image,images,label,labeling,classify,classification,test,qualification",
    "QualificationTypeStatus": "Active",
    "TestDurationInSeconds": 1200
  }
}
```

Similarly, evaluations are configured using the template:

```
{
  "dataset_properties": {
    "real_dir": "../datasets/eval/real",
    "fake_dir": "../datasets/eval/fake",
    "bucket_name": "mybucket",
    "bucket_region": "us-east-1"
  },
  "hit_properties": {
    "Title": "Determine whether the images are real or fake",
    "Description": "Decide whether each image is real or a computer generated fake.",
    "Keywords": "image,images,label,labeling,classify,classification",
    "Reward": 0.05,
    "LifetimeInSeconds": 604800,
    "AssignmentDurationInSeconds": 900,
    "FrameHeight": 20000,
    "MaxAssignments": 1,
    "QualificationId": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "QualificationComparator": ">",
    "QualificationInteger": 64
  },
  "approval_properties": {
    "correct_bonus": 0.02
  }
}
```

| Property  | Description |
| ------------- | ------------- |
| `real_dir`  | Directory containing real, unmodified images for use in a qualification test or evaluation.  |
| `fake_dir`  | Directory containing partially synthetic images for use in a qualification test or evaluation.  |
| `bucket_name`  | Name of the S3 bucket to store anonymized images.  |
| `bucket_region`  | The region of the S3 bucket.  |
| `correct_bonus`  | The bonus given to evaluators for each correct answer.  |
| `QualificationId` | Must be set to the ID of a qualification launched using `launch_qualification_test.py`. |

A description of all other properties can be found [here](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mturk.html#MTurk.Client.create_qualification_type) and [here](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mturk.html#MTurk.Client.create_hit).


### Hit UI Templates

Hit UI templates define the UI of the AMT HIT. The basic UI used for the HYPE-C baseline evaluations is included the `hit_templates` directory. Information on modifying the template can be found [here](https://github.com/jcjohnson/simple-amt) and [here](https://jinja.palletsprojects.com/en/3.1.x/).

## Using HYPE-C

| Script | Example | Description |
| ------------- | ------------- | ------------- |
| `launch_qualification_test.py` | `python launch_qualification_test.py --config=config.json --qual_properties=qual_properties/my_test.json` | Launches a new qualification test and returns the qualification ID. Launches to the sandbox by default; use the `--prod` flag to launch to production. |
| `launch_evaluation.py` | `python launch_evaluation.py --config=config.json --eval_properties=eval_properties/my_eval.json --eval_name="My Evaluation" --html_template=hit_templates/hypec_label.html` | Launches a new evaluation. Launches to the sandbox by default; use the `--prod` flag to launch to production. |
| `get_eval_results.py` | `python get_eval_results.py --config=config.json` | Gets evaluation results and updates local database. Should be run before using `approve_eval_hits.py`. Collects results from the sandbox by default; use the `--prod` flag to collect production results. |
| `approve_eval_hits.py` | `python approve_eval_hits.py --config=config.json` | Approves all valid evaluations and disburses bonuses to workers who submitted correct answers. Invalid or duplicate evaluations are rejected. Approves results from the sandbox by default; use the `--prod` flag to approve production results. |
| `auto_qual_workers.py` | `python auto_qual_workers.py --config=config.json` | Automatically disqualifies workers who have submitted an evaluation for a specific dataset from performing another evaluation using the same dataset. Prevents duplicate evaluations. Only works with workers from the sandbox by default; use the `--prod` flag to monitor production workers. |
| `compute_scores.py` | `python compute_scores.py` | Reports HYPE-C scores for all evaluations. Reports only results from the sandbox by default; use the `--prod` flag to report production results.|
| `db_setup.py` | `python db_setup.py` | Creates indices for the HYPE-C MongoDB database. |
