from __future__ import print_function

import json
import boto3
from botocore.vendored import requests

# receive cloudwatch spot interruption events and sent notice to DINGDING
# see cloudwatch event:  EC2 Spot Instance Interruption Warning at: https://docs.amazonaws.cn/AWSEC2/latest/UserGuide/spot-interruptions.html
# How to setup ?  CloudWatch Rules: choose [EC2 Spot Instance Interruption Warning]  -> trigger lambda
region = "cn-north-1"
DING =  "https://oapi.dingtalk.com/robot/send?access_token=xxxx"


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    
    if event['detail-type'] == 'EC2 Spot Instance Interruption Warning':
        print("Received ec2 spot instance interruption message")
        
        instance_id = event['detail']['instance-id']
        ip = ''
        tags = []
        
        #query instance ip for details
        #see: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.describe_instances
        ec2 = boto3.client('ec2', region_name=region)
        response = ec2.describe_instances(InstanceIds=[instance_id])
        for r in response['Reservations']:
           for i in r['Instances']:
               for tag in i['Tags']:
                   tags.append("%s : %s" %(tag['Key'], tag['Value']))
               for netinf in i['NetworkInterfaces']:
                   ip = netinf['PrivateIpAddress']
                   
        data = {
          "msgtype": "markdown",
          "markdown" : {
          "title": "AWS EC2 Spot Interruption Warning",
          "text":  "### AWS EC2 Spot Interruption Warning \n" +
                  " #### Details: \n" + 
                  " > ID: %s \n\n" % instance_id + 
                  " > IP: %s\n\n" % ip + 
                  " > Tags: %s \n\n" % ','.join(tags)
            }
          }
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        send_data = json.dumps(data).encode("utf-8")
        r = requests.post(url = DING, data = send_data, headers=headers) 
        print("Send DingDing message result:%s, request: %s "  %(r, send_data)) 
  
    return "OK" # Echo back the first key value
   
