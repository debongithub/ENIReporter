import json
import boto3
from json2html import *

def lambda_handler(event, context):
    
    region = ''
    if(event["queryStringParameters"] is not None and 'region' in event["queryStringParameters"]  and event["queryStringParameters"]["region"] is not None):
        region = event["queryStringParameters"]["region"]
    else:
        region = 'us-east-1'
    
    
    #Client Configs
    lambda_client = boto3.client("lambda",region_name=region)
    ec2_client = boto3.client('ec2',region_name=region)
    vpc_func_details = []
    
    list_func = lambda_client.list_functions(FunctionVersion='ALL')
    eni_share_report = []
    
    #Paginated Query
    while True:
        #For each function in the list fetch all versions and check the VPC + Subnet + SGs combination
        for i in list_func["Functions"]:
            print(list_func)
            func_details = lambda_client.get_function(FunctionName=i["FunctionArn"])["Configuration"]
            func_arn = i["FunctionArn"]
            func_name = i["FunctionName"]
            func_version = i["Version"]
            if func_details.get("VpcConfig") is not None and len(func_details["VpcConfig"]["VpcId"]) != 0:
                eni_filter_node=[{'Name':'group-id', 'Values':[]}, {'Name':'subnet-id', 'Values':[]},{'Name':'vpc-id', 'Values':[]}]
                vpc_id = func_details["VpcConfig"]["VpcId"]
                vpc_config = func_details.get("VpcConfig")
                subnet_level_vpcConfig = {}
                for subnet in vpc_config["SubnetIds"]:
                    print('for each subnet')
                    #Creating my filter for each subnet and I am calling my ENIs based on the filter
                    eni_filter_node[0]['Values'].extend(vpc_config["SecurityGroupIds"])
                    eni_filter_node[1]['Values'].append(subnet)
                    eni_filter_node[2]['Values'].append(vpc_id)
                    enis= ec2_client.describe_network_interfaces(Filters=eni_filter_node)
                    if(enis['NetworkInterfaces'] is not None and len(enis['NetworkInterfaces']) != 0):
                        share_node ={}
                        share_node['Function Name'] = func_name
                        share_node['Version'] = func_version
                        share_node['VPC'] =  vpc_id
                        share_node['Subnet'] = subnet
                        share_node['ENI'] = enis['NetworkInterfaces'][0]['NetworkInterfaceId']
                        share_node['Status'] =  enis['NetworkInterfaces'][0]['Status'] #
                        share_node['Attachment Status'] =  enis['NetworkInterfaces'][0]['Attachment']['Status'] #
                        eni_share_report.append(share_node)
        
        if(list_func.get("NextMarker") is not None):
            list_func = lambda_client.list_functions(FunctionVersion='ALL', Marker = list_func.get("NextMarker"))
        else:
            break
        
    return {"statusCode": 200, "body": give_me_my_html(eni_share_report),"headers": {'Content-Type': 'text/html'}}



def give_me_my_html(eni_share_report_json):
    html_string = ""
    with open('/var/task/report.html', 'r') as file:
        html_string = file.read()
    table_body = json2html.convert(json = eni_share_report_json,table_attributes='id=\"myTable\",class=\"cell-border\"')
    html_string = html_string.replace("MY_TABLE_MARKER",table_body)
    
    return html_string