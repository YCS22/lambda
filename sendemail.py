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
    outgoing_id = event["outgoing_id"]
    variables = event["body"]

    try:
        if (sender_id and template_id and relational_id and touch_id and team_id) is not None:

            #
            template_table = dynamodb.Table('Backend-dev')
            template_response = template_table.get_item(
                Key={
                    'id': template_id,
                }
            )

            template_content = template_response['Item']['content']
            template_type = template_response['Item']['type']

            # id ile senderi cekme
            sender_table = dynamodb.Table(
                'Sender-4ysbkmgwrzakngngy73f76zzfu-dev')

            sender_response = sender_table.get_item(
                Key={
                    'id': sender_id
                }
            )

            sender = sender_response['Item']['sender']
            sender_email = sender['email']

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

                response = ses.send_email(
                    Source=sender_email,
                    Destination={
                        'ToAddresses': [
                            email_to
                        ],
                    },
                    Message={
                        'Subject': {
                            'Data': email_subject
                        },
                        'Body': {
                            'Html': {
                                'Data': update_template_content
                            }
                        }
                    },
                    Tags=[
                        {
                            'Name': 'team_id',
                            'Value': team_id,
                        },
                        {
                            'Name': 'touch_id',
                            'Value': touch_id,
                        },
                        {
                            'Name': 'relational_id',
                            'Value': relational_id,
                        },
                    ],
                )

            if(response['MessageId'] is not None):
                global message_id
                message_id = response['MessageId']
                variables['is_status'] = "success"

           #
            outgoing_table = dynamodb.Table('Backend-dev')
            if outgoing_id is not None:
                outgoing_table.update_item(
                    Key={
                        'id': outgoing_id,
                    },
                    UpdateExpression="set sender_id=:a , team_id=:b, touch_id =:c,  contact_id =:d, message_id =:e , email_to =:l, email_subject =:m, type_name =:n, is_status =:s, variables=:v, template_id=:t",
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
                        'contact_id': relational_id,
                        'template_id': template_id,
                        'message_id': message_id,
                        'email_to': email_to,
                        'email_subject': email_subject,
                        'type_name': template_type,
                        'is_status': variables['is_status'],
                        'variables': variables
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