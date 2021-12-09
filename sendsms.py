import requests
from py3_infobip import (
    SmsClient,
    SmsTextSimpleBody
)
from bottle import template
import json
import boto3
import uuid
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

def lambda_handler(event, context):

    template_id = event["template_id"]
    sender_id = event["sender_id"]
    email_to = event["email_to"]
    email_subject = event["email_subject"]
    touch_id = event["touch_id"]
    team_id = event["team_id"]
    relational_id = event["contact_id"] or event["user_id"]
    outgoing_id = None  # event["outgoing_id"]
    variables = event["body"]

    try:
        if (sender_id and template_id and relational_id and touch_id and team_id) is not None:

            template_table = dynamodb.Table('Backend-dev')

            template_response = template_table.get_item(
                Key={
                    'id': template_id,
                }
            )

            template_content = template_response['Item']['content']
            template_type = template_response['Item']['type']

            is_bool = False
            for i in variables:
                result = str(template_content.find("{"+"{"+i+"}"+"}"))
                if(result != "-1"):
                    is_bool = True
                    break

            if(is_bool):
                update_template_content = template(
                    template_content, **variables)
            else:
                update_template_content = template_content

            sender_table = dynamodb.Table(
                'Sender-4ysbkmgwrzakngngy73f76zzfu-dev')

            sender_response = sender_table.get_item(
                Key={
                    'id': sender_id
                }
            )

            sender = sender_response['Item']['sender']
            sender_name = sender['name']

            sender_provider = sender_response['Item']['sender']['provider']
            provider_name = sender_provider[0]["content"]

            provider_username = sender_provider[1]["content"]
            provider_password = sender_provider[2]["content"]

            if provider_name == "BILPP":
                sns = boto3.client('sns')
                response = sns.publish(
                    PhoneNumber=variables["phone"],
                    Message=update_template_content
                )
                return response

            elif provider_name == "netgsm":
                response = requests.get(
                    '',
                    params={'usercode': provider_username, 'password': provider_password,
                            'gsmno': variables['phone'], 'message': update_template_content, 'msgheader': sender_name},
                )

            elif provider_name == "infobip":

                message = SmsTextSimpleBody()
                message \
                    .set_to([
                        '<phone_number>'
                    ]) \
                    .set_text('some text')

                infobip_client = SmsClient(
                    url='<infobip_url>',
                    api_key='<infobip_apikey>'
                )
                response = infobip_client.send_sms_text_simple(message)
                print(response.json())

            if(response['MessageId'] is not None):
                global message_id
                message_id = response['MessageId']
                variables['is_status'] = "success"

            # outgoing tablosuna yazdırma
            outgoing_table = dynamodb.Table('Backend-dev')  # Outgoing_Table
            if outgoing_id is not None:
                outgoing_table.update_item(
                    Key={
                        'id': outgoing_id,
                    },
                    UpdateExpression="set sender_id=:a , team_id=:b, touch_id =:c,  relational_id =:d, message_id =:e , email_to =:l, email_subject =:m, type_name =:n, is_status =:s, variables=:v, template_id=:t",
                    ExpressionAttributeValues={
                        ':a': sender_id,
                        ':b': team_id,
                        ':c': touch_id,
                        ':d': relational_id,
                        ':e': message_id,
                        ':l': email_to,
                        ':m': email_subject,
                        ':n': template_type,
                        ':s': variables['is_status'],
                        ':v': variables,
                        ':t': template_id
                    },
                    ReturnValues="UPDATED_NEW"
                )
            else:
                outgoing_table.put_item(
                    Item={
                        'id': str(uuid.uuid4()),
                        'sender_id': sender_id,
                        'team_id': team_id,
                        'touch_id': touch_id,
                        'relational_id': relational_id,
                        'message_id': message_id,
                        'email_to': email_to,
                        'email_subject': email_subject,
                        'type_name': template_type,
                        'is_status': variables['is_status'],
                        'variables': variables,
                        'template_id': template_id
                    }
                )

    except Exception as error:
        print("error", error)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "OK",

        }),
    }