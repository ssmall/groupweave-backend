"""
Submodule for interacting with DynamoDB
"""
import pickle
import random
import string

import boto3

dynamodb = boto3.resource('dynamodb')

_GAME_STATE_TABLE = dynamodb.Table('groupweave_game_state')
GAME_ID_LENGTH = 4

class GameIdGenerator(object):
    """
    Generates a new game ID based on the existing
    IDs in Dynamo, to avoid collisions
    """

    def new_id(self):
        response = _GAME_STATE_TABLE.scan(
            ProjectionExpression="game_id"
        )
        existing_ids = set([item["game_id"] for item in response['Items']])
        game_id = self.random_word(GAME_ID_LENGTH)
        while game_id in existing_ids:
            game_id = self.random_word(GAME_ID_LENGTH)
        return game_id

    def random_word(self, length):
        return ''.join(random.choice(string.uppercase) for i in range(length))

def create_game(game):
    _GAME_STATE_TABLE.put_item(
        Item={
            'game_id': game.id,
            'game_state': pickle.dumps(game)
        }
    )


def load_game(game_id):
    response = _GAME_STATE_TABLE.get_item(
        Key={
            'game_id': game_id
        }
    )
    return pickle.loads(response['Item']['game_state'])


def save_game(game):
    _GAME_STATE_TABLE.update_item(
        Key={
            'game_id': game.id
        },
        UpdateExpression="SET game_state = :game_state",
        ExpressionAttributeValues={
            ':game_state': pickle.dumps(game)
        }
    )
