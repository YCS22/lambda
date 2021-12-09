import json, csv, boto3,uuid
from datetime import datetime
import pandas as pd
from boto3.dynamodb.conditions import Attr
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):

    s3= boto3.client("s3")
    random_id=str(uuid.uuid4())+".csv"
    bucket_name="contactcsv" #event.bucketname
    url = f"s3://{bucket_name}/{random_id}"
    id = "export-1" #event.id
    team_id="" #event.team_id
    touch_id="" #event.touch_id
    
    try:
        #get item from dynamodb
        table = dynamodb.Table('Backend-dev')
        response = table.get_item(
                Key={  
                        'id':id,
                    }
        )
    
        properties = response['Item']['properties']
        properties_table = dynamodb.Table(properties)

        response_properties = properties_table.scan(
            FilterExpression=Attr('touch_id').eq(touch_id) & Attr('team_id').eq(team_id)
        )

        # json to csv 
        properties_item = response_properties['Items']
        properties_json=json.dumps(properties_item)
        read_properties = pd.read_json(properties_json)
        csv_properties = read_properties.to_csv(index=False)

        s3.put_object(Body=csv_properties, ContentType='text/csv', Bucket=bucket_name, Key=random_id)

        response = table.update_item(
                Key={        
                    'id':id
                },
                UpdateExpression="set is_status=:s ,csv_url=:c",
                ExpressionAttributeValues={
                    ':s': 'done',
                    ':c': url
                },
                ReturnValues="UPDATED_NEW"
        )
 
    except Exception as error:
       
        table.update_item(
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