"""
Submodule for interacting with SQS
"""
import boto3

sqs = boto3.client('sqs')


def create_queue(game_id, token):
    """
    Create an SQS queue for the given game id and token
    :return: the URL for the new queue
    """
    queue_name = "groupweave-{}-{}".format(game_id, token)
    response = sqs.create_queue(
        QueueName=queue_name
    )
    return response["QueueUrl"]


def send_message(queue_url, event):
    """
    Send an event as a message to an SQS queue
    """
    eventJson = event.toJson()
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=eventJson
    )
