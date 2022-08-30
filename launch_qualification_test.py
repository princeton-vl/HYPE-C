import argparse
import json
import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import Element, SubElement

import random

import simpleamt.simpleamt as simpleamt
import benchmark_utils

if __name__ == '__main__':
    parser = argparse.ArgumentParser(parents=[simpleamt.get_parent_parser()])
    parser.add_argument('--qual_properties',
                        type=argparse.FileType('r'))
    args = parser.parse_args()

    mtc = simpleamt.get_mturk_connection_from_args(args)

    qualification_properties = json.load(args.qual_properties)
    dataset_properties = qualification_properties["dataset_properties"]
    test_properties = qualification_properties["test_properties"]

    anon_links = benchmark_utils.upload_anon_images(dataset_properties["real_dir"],
                                                    dataset_properties["fake_dir"],
                                                    dataset_properties["bucket_name"],
                                                    dataset_properties["bucket_region"],
                                                    args.config.get(
                                                        'aws_access_key'),
                                                    args.config.get('aws_secret_key'))

    all_images = [(val[1], True) for val in anon_links["real"]]
    all_images += [(val[1], False) for val in anon_links["fake"]]
    random.shuffle(all_images)

    question_root = Element("QuestionForm")
    question_root.set(
        "xmlns", "http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/QuestionForm.xsd")
    for i in range(len(all_images)):
        question = SubElement(question_root, "Question")
        SubElement(question, "QuestionIdentifier").text = "q%d" % i
        SubElement(question, "IsRequired").text = "true"

        content = SubElement(question, "QuestionContent")
        SubElement(content, "Text").text = "Is the photo real?"
        binary = SubElement(content, "Binary")
        mime = SubElement(binary, "MimeType")
        SubElement(mime, "Type").text = "image"
        SubElement(mime, "SubType").text = "png"
        SubElement(binary, "DataURL").text = all_images[i][0]
        SubElement(binary, "AltText").text = ""

        answerspec = SubElement(question, "AnswerSpecification")
        selanswer = SubElement(answerspec, "SelectionAnswer")
        SubElement(selanswer, "StyleSuggestion").text = "radiobutton"
        selections = SubElement(selanswer, "Selections")
        selreal = SubElement(selections, "Selection")
        SubElement(selreal, "SelectionIdentifier").text = "q%dr" % i
        SubElement(selreal, "Text").text = "Yes"
        selfake = SubElement(selections, "Selection")
        SubElement(selfake, "SelectionIdentifier").text = "q%df" % i
        SubElement(selfake, "Text").text = "No"

    answerkey_root = Element("AnswerKey")
    answerkey_root.set(
        "xmlns", "http://mechanicalturk.amazonaws.com/AWSMechanicalTurkDataSchemas/2005-10-01/AnswerKey.xsd")
    for i in range(len(all_images)):
        question = SubElement(answerkey_root, "Question")
        SubElement(question, "QuestionIdentifier").text = "q%d" % i

        optionreal = SubElement(question, "AnswerOption")
        SubElement(optionreal, "SelectionIdentifier").text = "q%dr" % i
        SubElement(
            optionreal, "AnswerScore").text = "1" if all_images[i][1] else "0"

        optionfake = SubElement(question, "AnswerOption")
        SubElement(optionfake, "SelectionIdentifier").text = "q%df" % i
        SubElement(
            optionfake, "AnswerScore").text = "0" if all_images[i][1] else "1"

    qualvalue = SubElement(answerkey_root, "QualificationValueMapping")
    percentmap = SubElement(qualvalue, "PercentageMapping")
    SubElement(percentmap, "MaximumSummedScore").text = str(len(all_images))

    test_properties["Test"] = ElementTree.tostring(
        question_root, encoding="unicode")
    test_properties["AnswerKey"] = ElementTree.tostring(
        answerkey_root, encoding="unicode")

    launched = False
    while not launched:
        try:
            qual_response = mtc.create_qualification_type(**test_properties)
            launched = True
        except Exception as e:
            print(e)
    qual_id = qual_response['QualificationType']['QualificationTypeId']
    print('Launched Qualfication ID: %s' % qual_id)
