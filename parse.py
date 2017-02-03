import json
import yaml
from boto3 import Session

session = Session(profile_name="default")
rekognition = session.client("rekognition")

with open("capture.png", "rb")as imagefile:
    response = rekognition.detect_labels(Image={'Bytes': imagefile.read()}, MaxLabels=10)

quote = "I am "

for label in response["Labels"]:
    c = round(label["Confidence"],2)
    quote+=str(c)
    quote+=str(" percent confident I see a")
    quote+=str(label["Name"])
    quote+=str(" , ")

print quote






#j = "{u'Labels': [{u'Confidence': 99.29132843017578, u'Name': u'Human'},{u'Confidence': 99.29470825195312, u'Name': u'People'},{u'Confidence': 99.29470825195312, u'Name': u'Person'},{u'Confidence': 98.16999053955078, u'Name': u'Arm'},{u'Confidence': 51.457489013671875, u'Name': u'Face'},{u'Confidence': 51.457489013671875, u'Name': u'Selfie'}], 'ResponseMetadata': {'RetryAttempts': 0,'HTTPStatusCode': 200, 'RequestId': '39737a42-e9cf-11e6-b837-ef727c7b4c2e', 'HTTPHeaders': {'date': 'Fri, 03 Feb 2017 05:11:32 GMT','x-amzn-requestid': '39737a42-e9cf-11e6-b837-ef727c7b4c2e','content-length': '302','content-type': 'application/x-amz-json-1.1','connection': 'keep-alive'}}}"

