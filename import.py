import json, csv, boto3,uuid
from pprint import pprint
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import urlopen

dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

def lambda_handler(event, context):

    id = "import-1" #event.id
    queue_url='https://sqs.us-east-1.amazonaws.com/452953247977/ContactHub.fifo' #event.url
    
    try:
        # get file_url from dynamodb 
        table_datasync = dynamodb.Table('Backend-dev') # event.table
        table_response = table_datasync.get_item(
                    Key={  
                            'id':id,
                        }
                    )
        file_URL =table_response['Item']['file']

        #CSV to Json parser
        my_file = urlopen(file_URL).read().decode('utf-8').split('\n')
        csv_file = csv.DictReader(my_file)
        get_Data = list(csv_file)
        
     
        for x in get_Data:
            random_id=uuid.uuid4()
            #send message to sqs 
            sqs_response= sqs.send_message(
                MessageDeduplicationId=str(random_id),
                MessageGroupId=str(random_id),   
                QueueUrl=queue_url,
                MessageBody= (
                       json.dumps(x)
                ),

            )   
            

        #After sqs operation, update status and url in database
        table_datasync.update_item(
            Key={
                'id':id,
            },
            UpdateExpression="set is_status=:c,sqsUrl=:s",
            ExpressionAttributeValues={
                 ':c': 'done',
                 ':s': queue_url

            },
            ReturnValues="UPDATED_NEW"
        )
      
    except Exception as error:
        table_datasync.update_item(
            Key={
                'id':id,
            },
            UpdateExpression="set description=:c",
            ExpressionAttributeValues={
                 ':c':str(error),
            },
            ReturnValues="UPDATED_NEW"
        )
        raise
        
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "OK",
        }),
    }