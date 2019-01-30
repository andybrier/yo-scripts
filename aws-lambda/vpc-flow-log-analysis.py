import json
import base64
import gzip
from botocore.vendored import requests

from StringIO import StringIO

# analysis aws vpc flow log.  put the info into influxdb 

# how to setup?   VPC Flow Log -> cloudwatch logs --> lambda

def lambda_handler(event, context):
    #capture the CloudWatch log data
    outEvent = str(event['awslogs']['data'])
    
    #decode and unzip the log data
    outEvent = gzip.GzipFile(fileobj=StringIO(outEvent.decode('base64','strict'))).read()
    
    #convert the log data from JSON into a dictionary
    cleanEvent = json.loads(outEvent)
    
    ip = ""
    out_stat = {}
    in_stat = {}

    for t in cleanEvent['logEvents']:
        message = t['message'].split(' ')
        #<version> <account-id> <interface-id> <srcaddr> <dstaddr> <srcport> <dstport> <protocol> <packets> <bytes> <start> <end> <action> <log-status>
        # '2 860721417875 eni-068a3526ca86629fc 172.31.70.104 172.31.9.217 53100 53 17 1 64 1548232966 1548233026 ACCEPT OK', u'id': u'34526748882731325510119781932930655780063475715249277575'
        src = message[3]
        dst = message[4]
        if message[9] == '-':
            continue
        size = int(message[9])
       
        # aws  to qcloud flow 
        if "10.66" in dst or "10.67" in dst:
            ip = src
            if not dst in out_stat:
                out_stat[dst] = size
            else:
                out_stat[dst] += size
         # qcloud to aws flow 
        if "10.66" in src or "10.67" in src:
            ip = dst
            if  not src in in_stat:
                in_stat[src] = size
            else:
                in_stat[src] += size
    
    # write to influxdb
    influxdb =  'http://172.31.70.9:8086/write?db=yoho_event'
    
    if out_stat:  
        for key in out_stat:
            data="aws_to_qcloud,host=%s,dst=%s bytes=%d" %(ip, key, out_stat[key])
            requests.post(influxdb, data=data)
             
    if in_stat:  
        for key in in_stat:
            data="qcloud_to_aws,host=%s,src=%s bytes=%d" %(ip, key, in_stat[key])
            requests.post(influxdb, data=data)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

